import json
import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from forge.artifacts import ArtifactStore
from forge.audit import audit_run, audit_workspace
from forge.cli import app
from forge.contracts import Experiment
from forge.runner import run_experiment


def _run(tmp_path: Path) -> dict:
    experiment = Experiment.model_validate_json(Path("configs/l0_packing.json").read_bytes())
    return run_experiment(experiment, tmp_path)


def test_audit_valid_evidence_chain_and_cli(tmp_path: Path):
    outcome = _run(tmp_path)
    run_id = outcome["passport"]["run_id"]
    assert audit_run(run_id, tmp_path)["status"] == "VALID"
    assert audit_workspace(tmp_path)["valid"] == 1
    result = CliRunner().invoke(app, ["runs", "audit", "--workspace", str(tmp_path)])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["runs"][0]["run_id"] == run_id


def test_audit_detects_semantic_passport_tamper_even_with_valid_digest(tmp_path: Path):
    outcome = _run(tmp_path)
    run_id = outcome["passport"]["run_id"]
    passport = dict(outcome["passport"])
    passport["dataset"] = {"id": "forged", "revision": "v1"}
    from forge.canonical import canonical_bytes

    new_ref = ArtifactStore(tmp_path / ".forge" / "artifacts").put(canonical_bytes(passport))
    with sqlite3.connect(tmp_path / ".forge" / "registry.sqlite3") as connection:
        connection.execute("UPDATE runs SET passport_ref=? WHERE run_id=?", (new_ref, run_id))
    audited = audit_run(run_id, tmp_path)
    assert audited["status"] == "INVALID"
    assert "passport: dataset disagrees with config" in audited["errors"]
    result = CliRunner().invoke(app, ["runs", "audit", run_id, "--workspace", str(tmp_path)])
    assert result.exit_code == 1


def test_audit_detects_missing_and_corrupt_artifacts(tmp_path: Path):
    outcome = _run(tmp_path)
    run_id = outcome["passport"]["run_id"]
    report_ref = outcome["passport"]["report_ref"]
    store = ArtifactStore(tmp_path / ".forge" / "artifacts")
    report_path = store._path(report_ref)
    report_path.write_bytes(b"not the original report")
    audited = audit_run(run_id, tmp_path)
    assert audited["status"] == "INVALID"
    assert any("artifact digest mismatch" in error for error in audited["errors"])


def test_audit_reports_invalid_utf8_without_crashing(tmp_path: Path):
    outcome = _run(tmp_path)
    run_id = outcome["passport"]["run_id"]
    store = ArtifactStore(tmp_path / ".forge" / "artifacts")
    invalid_ref = store.put(b"\xff\xfe")
    with sqlite3.connect(tmp_path / ".forge" / "registry.sqlite3") as connection:
        connection.execute("UPDATE runs SET report_ref=? WHERE run_id=?", (invalid_ref, run_id))
    audited = audit_run(run_id, tmp_path)
    assert audited["status"] == "INVALID"
    assert any(error.startswith("report:") for error in audited["errors"])


def test_empty_workspace_does_not_pass(tmp_path: Path):
    assert audit_workspace(tmp_path)["status"] == "EMPTY"
    result = CliRunner().invoke(app, ["runs", "audit", "--workspace", str(tmp_path)])
    assert result.exit_code == 1
    assert not (tmp_path / ".forge").exists()


def test_audit_does_not_create_missing_registry_table(tmp_path: Path):
    root = tmp_path / ".forge"
    root.mkdir()
    registry = root / "registry.sqlite3"
    with sqlite3.connect(registry) as connection:
        connection.execute("CREATE TABLE unrelated (value INTEGER)")
    audited = audit_workspace(tmp_path)
    assert audited["status"] == "INVALID"
    with sqlite3.connect(registry) as connection:
        names = [row[0] for row in connection.execute("SELECT name FROM sqlite_master")]
    assert "runs" not in names
