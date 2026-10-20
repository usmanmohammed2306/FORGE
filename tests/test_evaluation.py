import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from forge.artifacts import ArtifactStore
from forge.canonical import canonical_bytes
from forge.cli import app
from forge.evaluation import ComparisonManifest, audit_comparison, compare_submissions


def test_paired_verifier_campaign_is_traceable_and_conservative(tmp_path: Path):
    result = compare_submissions(Path("configs/l0_comparison.json"), tmp_path)
    report = result["report"]
    assert report["task_count"] == 2
    assert report["baseline_solved"] == 0
    assert report["candidate_solved"] == 2
    assert report["paired_solve_rate_delta"]["estimate"] == 1
    assert report["verdict"] == "TOY_SAMPLE_ONLY"
    store = ArtifactStore(tmp_path / ".forge" / "artifacts")
    assert json.loads(store.get(result["report_ref"])) == report
    for row in report["tasks"]:
        assert store.get(row["task_ref"])
        assert store.get(row["baseline_report_ref"])
        assert store.get(row["candidate_report_ref"])
    cli = CliRunner().invoke(
        app, ["verifier", "compare", "configs/l0_comparison.json", "--workspace", str(tmp_path)]
    )
    assert cli.exit_code == 0
    audited = audit_comparison(result["report_ref"], tmp_path)
    assert audited["status"] == "VALID"
    audit_cli = CliRunner().invoke(
        app, ["verifier", "audit", result["report_ref"], "--workspace", str(tmp_path)]
    )
    assert audit_cli.exit_code == 0


def test_comparison_rejects_duplicate_task_entries():
    payload = json.loads(Path("configs/l0_comparison.json").read_text(encoding="utf-8"))
    payload["entries"][1]["task"] = payload["entries"][0]["task"]
    with pytest.raises(ValueError, match="unique"):
        ComparisonManifest.model_validate(payload)


def test_infrastructure_failure_invalidates_comparison(tmp_path: Path, monkeypatch):
    def broken(*args, **kwargs):
        return {"status": "INFRASTRUCTURE_ERROR", "report_ref": "bad", "task_ref": "bad"}

    monkeypatch.setattr("forge.evaluation.score_and_store", broken)
    with pytest.raises(RuntimeError, match="comparison is invalid"):
        compare_submissions(Path("configs/l0_comparison.json"), tmp_path)


def test_audit_rejects_validly_rehashed_fabricated_comparison(tmp_path: Path):
    result = compare_submissions(Path("configs/l0_comparison.json"), tmp_path)
    forged = dict(result["report"])
    forged["candidate_solved"] = 1
    forged_ref = ArtifactStore(tmp_path / ".forge" / "artifacts").put(canonical_bytes(forged))
    audited = audit_comparison(forged_ref, tmp_path)
    assert audited["status"] == "INVALID"
    assert "differs from replayed evidence" in audited["errors"][0]


def test_audit_rejects_fabricated_individual_score(tmp_path: Path):
    result = compare_submissions(Path("configs/l0_comparison.json"), tmp_path)
    store = ArtifactStore(tmp_path / ".forge" / "artifacts")
    forged = dict(result["report"])
    forged["tasks"] = [dict(row) for row in forged["tasks"]]
    score = json.loads(store.get(forged["tasks"][0]["candidate_report_ref"]))
    score["status"] = "TASK_FAILURE"
    score_ref = store.put(canonical_bytes(score))
    forged["tasks"][0]["candidate_report_ref"] = score_ref
    forged_ref = store.put(canonical_bytes(forged))
    audited = audit_comparison(forged_ref, tmp_path)
    assert audited["status"] == "INVALID"
    assert "score differs from replay" in audited["errors"][0]
