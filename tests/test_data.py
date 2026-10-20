import json
import random
from pathlib import Path

import pytest

from forge.artifacts import ArtifactStore
from forge.data import build_dataset, jaccard, normalized_text, read_jsonl, shingles


def test_data_builder_removes_duplicate_and_evaluation_leak(tmp_path: Path):
    train = Path("configs/l0_train_rows.jsonl")
    evaluation = Path("configs/l0_eval_rows.jsonl")
    first = build_dataset(train, evaluation, tmp_path)
    second = build_dataset(train, evaluation, tmp_path)
    assert first["manifest_ref"] == second["manifest_ref"]
    manifest = first["manifest"]
    assert manifest["raw_rows"] == 4
    assert manifest["kept_rows"] == 2
    assert {row["reason"] for row in manifest["removals"]} == {
        "exact_duplicate",
        "eval_contamination",
    }
    clean = ArtifactStore(tmp_path / ".forge" / "artifacts").get(manifest["clean_data_ref"])
    assert b'"id":"t1"' in clean
    assert b'"id":"t4"' not in clean


def test_duplicate_row_ids_fail_before_publication(tmp_path: Path):
    path = tmp_path / "duplicate.jsonl"
    original = Path("configs/l0_train_rows.jsonl").read_text(encoding="utf-8").splitlines()[0]
    path.write_text(original + "\n" + original + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate row id"):
        read_jsonl(path)


@pytest.mark.parametrize("threshold", [0.1, 0.8, 1.0])
def test_indexed_dedup_matches_pairwise_reference_on_edge_cases(tmp_path: Path, threshold: float):
    rng = random.Random(19)
    vocab = ["alpha", "beta", "gamma", "delta", "epsilon"]
    prompts = ["!!!", "???", "alpha beta gamma", "alpha beta gamma", "heldout special"]
    prompts.extend(" ".join(rng.choices(vocab, k=rng.randrange(1, 7))) for _ in range(75))
    rows = [
        {
            "id": f"row_{index:03d}",
            "prompt": prompt,
            "completion": "same" if index % 3 else "different",
            "source": "synthetic_test",
            "revision": "v1",
            "source_group": "eval" if index == 10 else "train",
        }
        for index, prompt in enumerate(prompts)
    ]
    training = tmp_path / "train.jsonl"
    evaluation = tmp_path / "eval.jsonl"
    training.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    evaluation.write_text(
        json.dumps(
            {
                "id": "heldout",
                "prompt": "heldout special",
                "completion": "answer",
                "source": "synthetic_test",
                "revision": "v1",
                "source_group": "eval",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    kept = []
    reasons = []
    for row in rows:
        if row["source_group"] == "eval" or normalized_text(row["prompt"]) == "heldout special":
            reason = "eval_contamination"
        elif any(
            row["prompt"] == other["prompt"] and row["completion"] == other["completion"]
            for other in kept
        ):
            reason = "exact_duplicate"
        elif any(
            jaccard(shingles(row["prompt"]), shingles(other["prompt"])) >= threshold
            for other in kept
        ):
            reason = "near_duplicate"
        else:
            reason = None
        if reason:
            reasons.append((row["id"], reason))
        else:
            kept.append(row)
    result = build_dataset(training, evaluation, tmp_path, near_duplicate_threshold=threshold)
    manifest = result["manifest"]
    assert manifest["kept_rows"] == len(kept)
    assert [(item["id"], item["reason"]) for item in manifest["removals"]] == reasons
    clean = ArtifactStore(tmp_path / ".forge" / "artifacts").get(manifest["clean_data_ref"])
    assert [json.loads(line)["id"] for line in clean.splitlines()] == sorted(
        row["id"] for row in kept
    )
