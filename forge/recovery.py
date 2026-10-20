"""Exercise exact interrupted/resumed L0 training before distributed checkpoint work."""

from pathlib import Path

from forge.artifacts import ArtifactStore
from forge.canonical import canonical_bytes
from forge.contracts import Experiment
from forge.l0 import train_tiny_transformer


def check_l0_recovery(experiment: Experiment, workspace: Path, split_step: int) -> dict:
    if experiment.hardware.backend != "cpu" or experiment.workload.kind != "tiny_lm":
        raise ValueError("L0 recovery check requires a CPU tiny_lm experiment")
    if not 1 <= split_step < experiment.workload.steps:
        raise ValueError("split_step must be within 1..workload.steps-1")
    workload = experiment.workload
    uninterrupted = train_tiny_transformer(workload, seed=experiment.seed)
    interrupted = train_tiny_transformer(workload, seed=experiment.seed, stop_after=split_step)
    resumed = train_tiny_transformer(
        workload, seed=experiment.seed, resume_checkpoint=interrupted.checkpoint_bytes
    )
    store = ArtifactStore(workspace / ".forge" / "artifacts")
    uninterrupted_ref = store.put(uninterrupted.checkpoint_bytes)
    interrupted_ref = store.put(interrupted.checkpoint_bytes)
    resumed_ref = store.put(resumed.checkpoint_bytes)
    exact_losses = uninterrupted.losses == resumed.losses
    exact_checkpoint = uninterrupted_ref == resumed_ref
    report = {
        "schema_version": 1,
        "kind": "l0_cpu_recovery_proof",
        "status": "PASS" if exact_losses and exact_checkpoint else "FAIL",
        "config_digest": experiment.config_digest,
        "split_step": split_step,
        "total_steps": workload.steps,
        "uninterrupted_checkpoint_ref": uninterrupted_ref,
        "interrupted_checkpoint_ref": interrupted_ref,
        "resumed_checkpoint_ref": resumed_ref,
        "uninterrupted_losses": uninterrupted.losses,
        "resumed_losses": resumed.losses,
        "exact_loss_trace": exact_losses,
        "exact_checkpoint_bytes": exact_checkpoint,
        "claim_limit": (
            "Same-host CPU toy recovery only. This does not establish distributed, cross-version, "
            "A100, or Gaudi restart correctness."
        ),
    }
    report_ref = store.put(canonical_bytes(report))
    return {"report_ref": report_ref, "report": report}
