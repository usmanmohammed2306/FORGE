"""Paired task evaluation with verifiable artifacts and conservative interpretation."""

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from forge.artifacts import ArtifactStore
from forge.canonical import canonical_bytes
from forge.stats import paired_rate_delta
from forge.verifier import FunctionTask, evaluate, score_and_store


class ComparisonEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    task: Path
    baseline: Path
    candidate: Path


class ComparisonManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    name: str = Field(min_length=3, pattern=r"^[a-z][a-z0-9_-]+$")
    entries: list[ComparisonEntry] = Field(min_length=2)
    bootstrap_repeats: int = Field(default=10_000, ge=100, le=100_000)
    seed: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def distinct_tasks(self) -> "ComparisonManifest":
        tasks = [str(entry.task) for entry in self.entries]
        if len(tasks) != len(set(tasks)):
            raise ValueError("comparison tasks must be unique")
        return self


def _build_report(
    manifest: ComparisonManifest,
    manifest_ref: str,
    task_rows: list[dict],
    baseline_outcomes: list[bool],
    candidate_outcomes: list[bool],
) -> dict:
    interval = paired_rate_delta(
        baseline_outcomes,
        candidate_outcomes,
        repeats=manifest.bootstrap_repeats,
        seed=manifest.seed,
    )
    if len(task_rows) < 30:
        verdict = "TOY_SAMPLE_ONLY"
    elif interval.low > 0:
        verdict = "CANDIDATE_BETTER_ON_THIS_DISTRIBUTION"
    elif interval.high < 0:
        verdict = "CANDIDATE_WORSE_ON_THIS_DISTRIBUTION"
    else:
        verdict = "NOT_DISTINGUISHABLE_FROM_NOISE"
    report = {
        "schema_version": 1,
        "kind": "paired_l0_function_repair_comparison",
        "name": manifest.name,
        "manifest_ref": manifest_ref,
        "task_count": len(task_rows),
        "baseline_solved": sum(baseline_outcomes),
        "candidate_solved": sum(candidate_outcomes),
        "paired_solve_rate_delta": interval.as_dict(),
        "verdict": verdict,
        "tasks": task_rows,
        "claim_limit": (
            "Bounded local L0 DSL and supplied tasks only. Not an A100/Gaudi model evaluation, "
            "not a private hidden test set, and not a release-grade quality claim."
        ),
    }
    return report


def compare_submissions(manifest_path: Path, workspace: Path) -> dict:
    """Compare held-out solve outcomes task-by-task, never treating infra errors as losses."""
    manifest = ComparisonManifest.model_validate_json(manifest_path.read_bytes())
    base_dir = manifest_path.resolve().parent
    store = ArtifactStore(workspace / ".forge" / "artifacts")
    manifest_ref = store.put(canonical_bytes(manifest.model_dump(mode="json")))
    baseline_outcomes: list[bool] = []
    candidate_outcomes: list[bool] = []
    task_rows = []
    seen_ids = set()
    for entry in manifest.entries:
        task_path = base_dir / entry.task
        task = FunctionTask.model_validate_json(task_path.read_bytes())
        if task.task_id in seen_ids:
            raise ValueError(f"duplicate task ID: {task.task_id}")
        seen_ids.add(task.task_id)
        baseline = score_and_store(task_path, base_dir / entry.baseline, workspace)
        candidate = score_and_store(task_path, base_dir / entry.candidate, workspace)
        if "INFRASTRUCTURE_ERROR" in (baseline["status"], candidate["status"]):
            raise RuntimeError(f"infrastructure error on {task.task_id}; comparison is invalid")
        baseline_outcomes.append(baseline["status"] == "SOLVED")
        candidate_outcomes.append(candidate["status"] == "SOLVED")
        task_rows.append(
            {
                "task_id": task.task_id,
                "task_ref": baseline["task_ref"],
                "baseline_report_ref": baseline["report_ref"],
                "candidate_report_ref": candidate["report_ref"],
                "baseline_status": baseline["status"],
                "candidate_status": candidate["status"],
            }
        )
    report = _build_report(manifest, manifest_ref, task_rows, baseline_outcomes, candidate_outcomes)
    report_ref = store.put(canonical_bytes(report))
    return {"report_ref": report_ref, "report": report}


def audit_comparison(report_ref: str, workspace: Path) -> dict:
    """Replay stored submissions and recompute the entire paired comparison."""
    store = ArtifactStore(workspace / ".forge" / "artifacts")
    errors = []

    def read_json(ref: str) -> dict:
        payload = store.get(ref)
        value = json.loads(payload)
        if not isinstance(value, dict) or canonical_bytes(value) != payload:
            raise ValueError(f"noncanonical JSON artifact: {ref}")
        return value

    try:
        original = read_json(report_ref)
        manifest_ref = original["manifest_ref"]
        manifest = ComparisonManifest.model_validate(read_json(manifest_ref))
        rows = original["tasks"]
        if not isinstance(rows, list) or len(rows) != len(manifest.entries):
            raise ValueError("task rows disagree with manifest")
        rebuilt_rows = []
        baseline_outcomes = []
        candidate_outcomes = []
        seen_ids = set()
        for row in rows:
            task_ref = row["task_ref"]
            task = FunctionTask.model_validate(read_json(task_ref))
            if task.task_id in seen_ids:
                raise ValueError("duplicate task ID in comparison evidence")
            seen_ids.add(task.task_id)
            rebuilt = {"task_id": task.task_id, "task_ref": task_ref}
            for role in ("baseline", "candidate"):
                score_ref = row[f"{role}_report_ref"]
                score = read_json(score_ref)
                source_ref = score["source_ref"]
                source = store.get(source_ref).decode("utf-8")
                expected = evaluate(task, source)
                expected["task_ref"] = task_ref
                expected["source_ref"] = source_ref
                if score != expected:
                    raise ValueError(f"{task.task_id}: {role} score differs from replay")
                if score["status"] == "INFRASTRUCTURE_ERROR":
                    raise ValueError(f"{task.task_id}: infrastructure error invalidates comparison")
                rebuilt[f"{role}_report_ref"] = score_ref
                rebuilt[f"{role}_status"] = score["status"]
                (baseline_outcomes if role == "baseline" else candidate_outcomes).append(
                    score["status"] == "SOLVED"
                )
            rebuilt_rows.append(rebuilt)
        expected_report = _build_report(
            manifest, manifest_ref, rebuilt_rows, baseline_outcomes, candidate_outcomes
        )
        if original != expected_report:
            raise ValueError("comparison report differs from replayed evidence")
    except (KeyError, TypeError, ValueError, UnicodeError, FileNotFoundError) as error:
        errors.append(str(error))
    return {
        "report_ref": report_ref,
        "status": "VALID" if not errors else "INVALID",
        "errors": errors,
        "claim_limit": "L0 evidence integrity only; this does not validate external benchmark quality.",
    }
