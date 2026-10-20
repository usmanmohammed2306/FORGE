"""Execute a real CPU data-layout analysis and emit its evidence chain."""

import json
import platform
import subprocess
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4

from forge.artifacts import ArtifactStore
from forge.canonical import canonical_bytes, digest
from forge.contracts import Experiment
from forge.l0 import train_tiny_transformer
from forge.packing import compare_layouts
from forge.registry import RunRegistry

CPU_LAYOUT_CLAIM_LIMIT = (
    "Token-count utilization only. No accelerator throughput, model quality, "
    "or memory improvement has been measured."
)
CPU_TRAIN_CLAIM_LIMIT = (
    "Tiny CPU optimization smoke only. The fixture is not a useful language model "
    "and makes no A100, Gaudi, or held-out quality claim."
)


def _git_revision(workspace: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def source_digest() -> str:
    """Hash local source and CPU locks even before a first Git commit exists."""
    package = Path(__file__).resolve().parent
    project = package.parent
    files = list(package.glob("*.py"))
    for relative in ("pyproject.toml", "constraints/dev.txt", "constraints/l0-macos-arm64.txt"):
        candidate = project / relative
        if candidate.exists():
            files.append(candidate)
    import hashlib

    members = {
        str(path.relative_to(project)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(files)
    }
    return digest(members, domain="forge.source.v1")


def environment_versions(workload_kind: str) -> dict[str, str]:
    """Capture installed libraries that can change the execution semantics."""
    packages = ["pydantic", "typer"]
    if workload_kind == "tiny_lm":
        packages.extend(["torch", "numpy"])
    return {package: version(package) for package in packages}


def run_experiment(experiment: Experiment, workspace: Path) -> dict:
    if experiment.hardware.backend != "cpu":
        raise ValueError(
            "this runner currently supports CPU data analysis only; CUDA and HPU jobs must "
            "not be represented by CPU evidence"
        )
    root = workspace / ".forge"
    artifacts = ArtifactStore(root / "artifacts")
    registry = RunRegistry(root / "registry.sqlite3")
    run_id = "RUN-" + uuid4().hex[:12]
    created_at = datetime.now(timezone.utc).isoformat()
    config_ref = artifacts.put(canonical_bytes(experiment.model_dump(mode="json")))
    registry.start(run_id, created_at, experiment.config_digest, config_ref)
    try:
        if experiment.workload.kind == "packing":
            layouts = compare_layouts(
                experiment.workload.sequence_lengths,
                experiment.workload.batch_size,
                experiment.workload.max_sequence_length,
            )
            report = {
                "schema_version": 1,
                "kind": "analytical_cpu_data_layout",
                "workload": "packing",
                "config_digest": experiment.config_digest,
                "logical_examples": len(experiment.workload.sequence_lengths),
                "layouts": layouts,
                "claim_limit": CPU_LAYOUT_CLAIM_LIMIT,
            }
        else:
            training = train_tiny_transformer(experiment.workload, seed=experiment.seed)
            checkpoint_ref = artifacts.put(training.checkpoint_bytes)
            report = {
                "schema_version": 1,
                "kind": "real_cpu_l0_training",
                "workload": "tiny_lm",
                "config_digest": experiment.config_digest,
                "training": training.report_fields(),
                "torch_version": version("torch"),
                "checkpoint_ref": checkpoint_ref,
                "claim_limit": CPU_TRAIN_CLAIM_LIMIT,
            }
        report_ref = artifacts.put(canonical_bytes(report))
        passport = {
            "schema_version": 1,
            "run_id": run_id,
            "created_at": created_at,
            "status": "complete",
            "config_digest": experiment.config_digest,
            "config_ref": config_ref,
            "report_ref": report_ref,
            "checkpoint_ref": report.get("checkpoint_ref"),
            "git_revision": _git_revision(workspace),
            "source_digest": source_digest(),
            "environment_versions": environment_versions(experiment.workload.kind),
            "model": experiment.model.model_dump(mode="json"),
            "dataset": experiment.dataset.model_dump(mode="json"),
            "hardware": {
                "backend": "cpu",
                "world_size": 1,
                "system": platform.system(),
                "machine": platform.machine(),
                "python": platform.python_version(),
            },
            "reproduction": f"forge reproduce {run_id}",
            "claim_limit": report["claim_limit"],
        }
        passport_ref = artifacts.put(canonical_bytes(passport))
        registry.complete(run_id, report_ref, passport_ref)
        return {"passport": passport, "passport_ref": passport_ref, "report": report}
    except Exception as error:
        registry.fail(run_id, f"{type(error).__name__}: {error}")
        raise


def load_report(run_id: str, workspace: Path) -> dict:
    root = workspace / ".forge"
    row = RunRegistry(root / "registry.sqlite3").get(run_id)
    if row["status"] != "complete" or not row["report_ref"]:
        raise ValueError(f"run {run_id} has no complete report")
    payload = ArtifactStore(root / "artifacts").get(row["report_ref"])
    return json.loads(payload)


def load_experiment(run_id: str, workspace: Path) -> Experiment:
    root = workspace / ".forge"
    row = RunRegistry(root / "registry.sqlite3").get(run_id)
    payload = ArtifactStore(root / "artifacts").get(row["config_ref"])
    experiment = Experiment.model_validate_json(payload)
    if experiment.config_digest != row["config_digest"]:
        raise ValueError("stored configuration digest does not match the registry")
    return experiment


def verify_reproduction_source(run_id: str, workspace: Path) -> None:
    root = workspace / ".forge"
    row = RunRegistry(root / "registry.sqlite3").get(run_id)
    if not row["passport_ref"]:
        raise ValueError("source run has no passport")
    passport = json.loads(ArtifactStore(root / "artifacts").get(row["passport_ref"]))
    if passport.get("source_digest") != source_digest():
        raise ValueError("source code or CPU lock changed; this would not be an exact reproduction")
    experiment = load_experiment(run_id, workspace)
    if passport.get("environment_versions") != environment_versions(experiment.workload.kind):
        raise ValueError(
            "installed package versions changed; this would not be an exact reproduction"
        )
    hardware = passport.get("hardware", {})
    if (hardware.get("system"), hardware.get("machine"), hardware.get("python")) != (
        platform.system(),
        platform.machine(),
        platform.python_version(),
    ):
        raise ValueError("host or Python version changed; this would not be an exact reproduction")
