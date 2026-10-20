import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from forge.artifacts import ArtifactStore
from forge.cli import app
from forge.contracts import Experiment
from forge.l0 import train_tiny_transformer
from forge.recovery import check_l0_recovery

torch = pytest.importorskip("torch")
EXPERIMENT = Experiment.model_validate_json(Path("configs/l0_train.json").read_bytes())


def test_interrupted_training_recovers_exact_loss_and_checkpoint():
    workload = EXPERIMENT.workload
    uninterrupted = train_tiny_transformer(workload, seed=EXPERIMENT.seed)
    interrupted = train_tiny_transformer(workload, seed=EXPERIMENT.seed, stop_after=5)
    resumed = train_tiny_transformer(
        workload, seed=EXPERIMENT.seed, resume_checkpoint=interrupted.checkpoint_bytes
    )
    assert interrupted.completed_steps == 5
    assert resumed.completed_steps == workload.steps
    assert uninterrupted.losses == resumed.losses
    assert uninterrupted.checkpoint_bytes == resumed.checkpoint_bytes
    assert interrupted.training_tokens < resumed.training_tokens


def test_recovery_report_and_cli_are_content_addressed(tmp_path: Path):
    result = check_l0_recovery(EXPERIMENT, tmp_path, split_step=5)
    assert result["report"]["status"] == "PASS"
    assert result["report"]["exact_checkpoint_bytes"] is True
    assert (
        json.loads(ArtifactStore(tmp_path / ".forge" / "artifacts").get(result["report_ref"]))
        == result["report"]
    )
    cli = CliRunner().invoke(
        app,
        [
            "l0",
            "recovery-check",
            "configs/l0_train.json",
            "--split-step",
            "5",
            "--workspace",
            str(tmp_path),
        ],
    )
    assert cli.exit_code == 0
    assert json.loads(cli.stdout)["report"]["status"] == "PASS"


def test_checkpoint_rejects_wrong_seed_workload_and_corrupt_bytes():
    workload = EXPERIMENT.workload
    partial = train_tiny_transformer(workload, seed=EXPERIMENT.seed, stop_after=5)
    with pytest.raises(ValueError, match="incompatible"):
        train_tiny_transformer(
            workload, seed=EXPERIMENT.seed + 1, resume_checkpoint=partial.checkpoint_bytes
        )
    altered = workload.model_copy(update={"learning_rate": workload.learning_rate / 2})
    with pytest.raises(ValueError, match="incompatible"):
        train_tiny_transformer(
            altered, seed=EXPERIMENT.seed, resume_checkpoint=partial.checkpoint_bytes
        )
    with pytest.raises(ValueError, match="cannot be resumed"):
        train_tiny_transformer(
            workload, seed=EXPERIMENT.seed, resume_checkpoint=b"not a checkpoint"
        )


def test_invalid_split_and_resume_order_are_rejected():
    workload = EXPERIMENT.workload
    with pytest.raises(ValueError, match="stop_after"):
        train_tiny_transformer(workload, seed=EXPERIMENT.seed, stop_after=0)
    partial = train_tiny_transformer(workload, seed=EXPERIMENT.seed, stop_after=5)
    with pytest.raises(ValueError, match="checkpoint step"):
        train_tiny_transformer(
            workload,
            seed=EXPERIMENT.seed,
            resume_checkpoint=partial.checkpoint_bytes,
            stop_after=5,
        )
