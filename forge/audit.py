"""Read-only integrity audit of the local run evidence graph.

This verifies provenance links, not whether a scientific claim is true. A complete
release still needs backend measurements and semantic review.
"""

import json
import sqlite3
from pathlib import Path
from urllib.parse import quote

from pydantic import ValidationError

from forge.artifacts import ArtifactCorruption, ArtifactStore
from forge.canonical import canonical_bytes
from forge.contracts import Experiment
from forge.runner import CPU_LAYOUT_CLAIM_LIMIT, CPU_TRAIN_CLAIM_LIMIT, source_digest


def _read_registry(path: Path, run_id: str | None = None) -> list[dict]:
    """Open SQLite in read-only mode so an audit cannot create or repair evidence."""
    uri = f"file:{quote(str(path))}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        if run_id is None:
            rows = connection.execute("SELECT * FROM runs ORDER BY created_at DESC").fetchall()
        else:
            rows = connection.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchall()
    return [dict(row) for row in rows]


def audit_run(run_id: str, workspace: Path) -> dict:
    """Return named failures; never silently trust a digest-shaped reference."""
    root = workspace / ".forge"
    if not (root / "registry.sqlite3").exists():
        return {
            "run_id": run_id,
            "status": "INVALID",
            "errors": ["local registry does not exist"],
            "warnings": [],
        }
    try:
        rows = _read_registry(root / "registry.sqlite3", run_id)
    except sqlite3.DatabaseError as error:
        return {
            "run_id": run_id,
            "status": "INVALID",
            "errors": [f"registry: {error}"],
            "warnings": [],
        }
    if not rows:
        return {
            "run_id": run_id,
            "status": "INVALID",
            "errors": [f"unknown run: {run_id}"],
            "warnings": [],
        }
    row = rows[0]

    errors: list[str] = []
    warnings: list[str] = []
    if row["status"] != "complete":
        errors.append(f"run state is {row['status']}, not complete")
    store = ArtifactStore(root / "artifacts")

    def read_json(ref: str | None, label: str) -> dict | None:
        if not ref:
            errors.append(f"{label}: missing reference")
            return None
        try:
            payload = store.get(ref)
            value = json.loads(payload)
            if not isinstance(value, dict):
                raise ValueError("artifact is not a JSON object")
            if payload != canonical_bytes(value):
                errors.append(f"{label}: JSON is not canonical")
            return value
        except (ValueError, UnicodeError, FileNotFoundError, ArtifactCorruption) as error:
            errors.append(f"{label}: {error}")
            return None

    config = read_json(row["config_ref"], "config")
    report = read_json(row["report_ref"], "report")
    passport = read_json(row["passport_ref"], "passport")
    experiment = None
    if config is not None:
        try:
            experiment = Experiment.model_validate(config)
            if experiment.config_digest != row["config_digest"]:
                errors.append("config: digest disagrees with registry")
        except ValidationError as error:
            errors.append(f"config: invalid experiment contract: {error}")

    if report is not None:
        if report.get("config_digest") != row["config_digest"]:
            errors.append("report: config digest disagrees with registry")
        if report.get("schema_version") != 1:
            errors.append("report: unsupported schema version")
        checkpoint_ref = report.get("checkpoint_ref")
        if checkpoint_ref is not None:
            try:
                store.get(checkpoint_ref)
            except (ValueError, FileNotFoundError, ArtifactCorruption) as error:
                errors.append(f"checkpoint: {error}")

    if passport is not None:
        expected = {
            "run_id": run_id,
            "status": "complete",
            "schema_version": 1,
            "created_at": row["created_at"],
            "config_digest": row["config_digest"],
            "config_ref": row["config_ref"],
            "report_ref": row["report_ref"],
        }
        for key, value in expected.items():
            if passport.get(key) != value:
                errors.append(f"passport: {key} disagrees with registry")
        if report is not None and passport.get("checkpoint_ref") != report.get("checkpoint_ref"):
            errors.append("passport: checkpoint reference disagrees with report")
        if report is not None and passport.get("claim_limit") != report.get("claim_limit"):
            errors.append("passport: claim limit disagrees with report")
        if experiment is not None:
            if passport.get("model") != experiment.model.model_dump(mode="json"):
                errors.append("passport: model disagrees with config")
            if passport.get("dataset") != experiment.dataset.model_dump(mode="json"):
                errors.append("passport: dataset disagrees with config")
            hardware = passport.get("hardware")
            if (
                not isinstance(hardware, dict)
                or hardware.get("backend") != experiment.hardware.backend
            ):
                errors.append("passport: hardware backend disagrees with config")
            if (
                not isinstance(hardware, dict)
                or hardware.get("world_size") != experiment.hardware.world_size
            ):
                errors.append("passport: world size disagrees with config")
            expected_kind = (
                "analytical_cpu_data_layout"
                if experiment.workload.kind == "packing"
                else "real_cpu_l0_training"
            )
            if report is not None and report.get("kind") != expected_kind:
                errors.append("report: workload kind disagrees with config")
            expected_claim = (
                CPU_LAYOUT_CLAIM_LIMIT
                if experiment.workload.kind == "packing"
                else CPU_TRAIN_CLAIM_LIMIT
            )
            if report is not None and report.get("claim_limit") != expected_claim:
                errors.append("report: CPU claim limit disagrees with workload")
        if passport.get("source_digest") != source_digest():
            warnings.append("source code or CPU constraints differ from this checkout")

    return {
        "run_id": run_id,
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "warnings": warnings,
        "claim_limit": "Integrity only; this audit does not validate a hardware or quality claim.",
    }


def audit_workspace(workspace: Path) -> dict:
    root = workspace / ".forge"
    if not (root / "registry.sqlite3").exists():
        return {"status": "EMPTY", "runs": [], "valid": 0, "invalid": 0}
    try:
        rows = _read_registry(root / "registry.sqlite3")
    except sqlite3.DatabaseError as error:
        return {
            "status": "INVALID",
            "runs": [],
            "valid": 0,
            "invalid": 1,
            "errors": [f"registry: {error}"],
        }
    audited = [audit_run(row["run_id"], workspace) for row in rows]
    invalid = sum(row["status"] == "INVALID" for row in audited)
    return {
        "status": "INVALID" if invalid else "VALID" if audited else "EMPTY",
        "runs": audited,
        "valid": len(audited) - invalid,
        "invalid": invalid,
    }
