import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from forge.cli import app
from forge.contracts import Experiment
from forge.release import verify_release_index
from forge.runner import load_experiment, load_report, run_experiment, verify_reproduction_source


def test_run_passport_reproduction_and_doctor(tmp_path: Path):
    experiment = Experiment.model_validate_json(Path("configs/l0_packing.json").read_bytes())
    first = run_experiment(experiment, tmp_path)
    run_id = first["passport"]["run_id"]
    assert first["passport"]["config_digest"] == experiment.config_digest
    assert first["report"]["claim_limit"].startswith("Token-count utilization only")
    assert load_experiment(run_id, tmp_path) == experiment
    verify_reproduction_source(run_id, tmp_path)
    assert load_report(run_id, tmp_path) == first["report"]
    second = run_experiment(load_experiment(run_id, tmp_path), tmp_path)
    assert first["passport"]["report_ref"] == second["passport"]["report_ref"]
    runner = CliRunner()
    result = runner.invoke(app, ["doctor", run_id, "--workspace", str(tmp_path)])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["diagnosis"]["status"] == "PADDING_PRESSURE"


def test_release_gate_fails_with_named_missing_evidence(tmp_path: Path):
    report = verify_release_index(tmp_path)
    assert report["status"] == "FAIL"
    assert "sft" in report["missing"]
    result = CliRunner().invoke(app, ["release", "verify", "--workspace", str(tmp_path)])
    assert result.exit_code != 0
    assert '"status": "FAIL"' in result.stdout


def test_reproduction_refuses_source_drift(tmp_path: Path, monkeypatch):
    experiment = Experiment.model_validate_json(Path("configs/l0_packing.json").read_bytes())
    run_id = run_experiment(experiment, tmp_path)["passport"]["run_id"]
    monkeypatch.setattr("forge.runner.source_digest", lambda: "changed-source")
    with pytest.raises(ValueError, match="not be an exact reproduction"):
        verify_reproduction_source(run_id, tmp_path)
    result = CliRunner().invoke(app, ["reproduce", run_id, "--workspace", str(tmp_path)])
    assert result.exit_code == 2
    assert "source code or CPU lock changed" in result.stderr


def test_reproduction_refuses_package_drift(tmp_path: Path, monkeypatch):
    experiment = Experiment.model_validate_json(Path("configs/l0_packing.json").read_bytes())
    run_id = run_experiment(experiment, tmp_path)["passport"]["run_id"]
    monkeypatch.setattr("forge.runner.environment_versions", lambda kind: {"pydantic": "0.0"})
    with pytest.raises(ValueError, match="installed package versions changed"):
        verify_reproduction_source(run_id, tmp_path)


def test_non_cpu_config_is_refused_without_false_run(tmp_path: Path):
    config = json.loads(Path("configs/l0_packing.json").read_text(encoding="utf-8"))
    config["hardware"]["backend"] = "cuda"
    experiment = Experiment.model_validate(config)
    try:
        run_experiment(experiment, tmp_path)
    except ValueError as error:
        assert "CPU data analysis only" in str(error)
    else:
        raise AssertionError("CUDA config was accepted by a CPU-only runner")
    assert not (tmp_path / ".forge").exists()


def test_unknown_command_exits_nonzero():
    result = CliRunner().invoke(app, ["there-is-no-such-command"])
    assert result.exit_code != 0
