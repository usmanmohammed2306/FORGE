from pathlib import Path

import pytest

from forge.artifacts import ArtifactStore
from forge.contracts import Experiment
from forge.runner import run_experiment

torch = pytest.importorskip("torch")


def test_tiny_transformer_really_updates_and_saves_checkpoint(tmp_path):
    experiment = Experiment.model_validate_json(Path("configs/l0_train.json").read_bytes())
    outcome = run_experiment(experiment, tmp_path)
    report = outcome["report"]
    assert report["kind"] == "real_cpu_l0_training"
    losses = report["training"]["losses"]
    assert len(losses) == experiment.workload.steps
    assert losses[-1] < losses[0]
    checkpoint = ArtifactStore(tmp_path / ".forge" / "artifacts").get(report["checkpoint_ref"])
    assert len(checkpoint) > 1000
    assert outcome["passport"]["checkpoint_ref"] == report["checkpoint_ref"]
