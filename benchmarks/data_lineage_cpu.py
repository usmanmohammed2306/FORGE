"""Reproducible local CPU microbenchmark; synthetic input, not an SFT result."""

import argparse
import hashlib
import json
import platform
import statistics
import tempfile
import time
from pathlib import Path

from data_lineage_reference import build_dataset_pairwise

from forge.data import build_dataset


def _write_fixture(root: Path, rows: int, distribution: str) -> tuple[Path, Path]:
    training = root / "training.jsonl"
    evaluation = root / "evaluation.jsonl"
    with training.open("w", encoding="utf-8") as stream:
        for index in range(rows):
            source = (
                index // 10
                if distribution == "duplicate_heavy"
                else (index - 1 if index % 10 == 0 and index > 0 else index)
            )
            prompt = (
                f"common alpha beta c{source} d{source} e{source}"
                if distribution == "shared_shingle"
                else f"a{source} b{source} c{source} d{source}"
            )
            row = {
                "id": f"row_{index}",
                "prompt": prompt,
                "completion": f"answer_{source}",
                "source": "synthetic_benchmark",
                "revision": "v1",
                "source_group": "train",
            }
            stream.write(json.dumps(row, sort_keys=True) + "\n")
    evaluation.write_text(
        json.dumps(
            {
                "id": "heldout",
                "prompt": "heldout example only",
                "completion": "heldout answer",
                "source": "synthetic_benchmark",
                "revision": "v1",
                "source_group": "eval",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return training, evaluation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=1200)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument(
        "--distribution",
        choices=("disjoint", "shared_shingle", "duplicate_heavy"),
        default="disjoint",
    )
    args = parser.parse_args()
    if args.rows < 20 or args.repeats < 3:
        parser.error("rows must be >=20 and repeats >=3")
    source_path = Path(__file__).resolve().parents[1] / "forge" / "data.py"
    source_ref = "sha256:" + hashlib.sha256(source_path.read_bytes()).hexdigest()
    reference_path = Path(__file__).resolve().parent / "data_lineage_reference.py"
    reference_ref = "sha256:" + hashlib.sha256(reference_path.read_bytes()).hexdigest()
    elapsed_ms = {"pairwise": [], "indexed": []}
    output_refs = set()
    with tempfile.TemporaryDirectory(prefix="forge-data-bench-") as temporary:
        root = Path(temporary)
        training, evaluation = _write_fixture(root, args.rows, args.distribution)
        for repeat in range(args.repeats + 1):
            order = ("pairwise", "indexed") if repeat % 2 else ("indexed", "pairwise")
            results = {}
            for method in order:
                builder = build_dataset_pairwise if method == "pairwise" else build_dataset
                started = time.perf_counter_ns()
                result = builder(training, evaluation, root / f"run_{repeat}_{method}")
                duration_ms = (time.perf_counter_ns() - started) / 1_000_000
                if repeat:
                    elapsed_ms[method].append(duration_ms)
                results[method] = result["manifest"]
                output_refs.add(result["manifest"]["clean_data_ref"])
            for field in ("raw_rows", "kept_rows", "removed_rows", "removals", "clean_data_ref"):
                if results["pairwise"][field] != results["indexed"][field]:
                    raise RuntimeError(f"benchmark methods disagree on {field}")
        if len(output_refs) != 1:
            raise RuntimeError("benchmark runs produced different clean datasets")
        paired_speedups = [
            pairwise / indexed
            for pairwise, indexed in zip(elapsed_ms["pairwise"], elapsed_ms["indexed"])
        ]
        print(
            json.dumps(
                {
                    "status": "LOCAL_SYNTHETIC_CPU_ONLY",
                    "source_refs": {"pairwise": reference_ref, "indexed": source_ref},
                    "python": platform.python_version(),
                    "system": platform.system(),
                    "machine": platform.machine(),
                    "raw_rows": args.rows,
                    "distribution": args.distribution,
                    "kept_rows": result["manifest"]["kept_rows"],
                    "removed_rows": result["manifest"]["removed_rows"],
                    "warmup_runs": 1,
                    "measured_repeats": args.repeats,
                    "elapsed_ms": elapsed_ms,
                    "median_ms": {
                        method: statistics.median(values) for method, values in elapsed_ms.items()
                    },
                    "paired_speedups": paired_speedups,
                    "median_paired_speedup": statistics.median(paired_speedups),
                    "clean_data_ref": results["indexed"]["clean_data_ref"],
                    "claim_limit": (
                        "Synthetic CPU data-lineage fixture with named distribution only; "
                        "not accelerator training or representative corpus throughput."
                    ),
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
