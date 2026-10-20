import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from forge.artifacts import ArtifactStore
from forge.cli import app
from forge.verifier import FunctionTask, evaluate, evaluate_in_worker, score_and_store

TASK = FunctionTask.model_validate_json(Path("configs/l0_factorial_task.json").read_bytes())
SOLUTION = Path("configs/l0_factorial_solution.py").read_text(encoding="utf-8")


def test_function_repair_public_and_heldout_and_artifacts(tmp_path: Path):
    result = evaluate(TASK, SOLUTION)
    assert result["status"] == "SOLVED"
    assert (result["public_passed"], result["heldout_passed"]) == (3, 2)
    assert "expected" not in json.dumps(result)
    stored = score_and_store(
        Path("configs/l0_factorial_task.json"), Path("configs/l0_factorial_solution.py"), tmp_path
    )
    store = ArtifactStore(tmp_path / ".forge" / "artifacts")
    assert store.get(stored["source_ref"]) == SOLUTION.encode("utf-8")
    assert json.loads(store.get(stored["report_ref"]))["status"] == "SOLVED"
    cli = CliRunner().invoke(
        app,
        [
            "verifier",
            "score",
            "configs/l0_factorial_task.json",
            "configs/l0_factorial_solution.py",
            "--workspace",
            str(tmp_path),
        ],
    )
    assert cli.exit_code == 0


@pytest.mark.parametrize(
    ("source", "status"),
    [
        ("def solve(x):\n    return 1\n", "TASK_FAILURE"),
        ("def solve(x):\n    while True:\n        pass\n", "TIMEOUT"),
        ("import os\ndef solve(x):\n    return x\n", "TAMPER_ATTEMPT"),
        ("def solve(x):\n    return open('secret')\n", "TAMPER_ATTEMPT"),
        ("def solve(x) return x", "MALFORMED_OUTPUT"),
        ("def solve(x):\n    return 1 // 0\n", "TASK_FAILURE"),
        ("def solve(x):\n    return x ** 1000000\n", "TAMPER_ATTEMPT"),
        ("def solve(x):\n    def nested():\n        return 1\n    return x\n", "TAMPER_ATTEMPT"),
    ],
)
def test_distinct_failure_semantics(source: str, status: str):
    assert evaluate(TASK, source)["status"] == status


def test_infrastructure_failure_is_not_a_wrong_answer(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("simulated worker failure")

    monkeypatch.setattr("forge.verifier._execute", fail)
    result = evaluate(TASK, SOLUTION)
    assert result["status"] == "INFRASTRUCTURE_ERROR"
    assert result["heldout_passed"] == 0


def test_task_rejects_overlapping_public_and_heldout_inputs():
    payload = TASK.model_dump(mode="json")
    payload["heldout_cases"][0]["x"] = payload["public_cases"][0]["x"]
    with pytest.raises(ValueError, match="distinct"):
        FunctionTask.model_validate(payload)


def test_worker_matches_bounded_interpreter_for_success_and_attacks():
    for source in (
        SOLUTION,
        "def solve(x):\n    while True:\n        pass\n",
        "import os\ndef solve(x):\n    return x\n",
    ):
        assert evaluate_in_worker(TASK, source) == evaluate(TASK, source)


def test_worker_wall_timeout_is_infrastructure_failure(monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="worker", timeout=5)

    monkeypatch.setattr("forge.verifier.subprocess.run", timeout)
    result = evaluate_in_worker(TASK, SOLUTION)
    assert result["status"] == "INFRASTRUCTURE_ERROR"
    assert result["reason"] == "worker_wall_timeout"


def test_worker_protocol_failure_is_not_a_wrong_answer(monkeypatch):
    class BadWorker:
        returncode = 0
        stdout = b'{"schema_version":1,"result":{"status":"SOLVED"}}'
        stderr = b""

    monkeypatch.setattr("forge.verifier.subprocess.run", lambda *a, **k: BadWorker())
    result = evaluate_in_worker(TASK, SOLUTION)
    assert result["status"] == "INFRASTRUCTURE_ERROR"
    assert result["reason"] == "worker_protocol_invalid"


def test_worker_rejects_invalid_timeout_and_oversized_case_set():
    with pytest.raises(ValueError, match="positive"):
        evaluate_in_worker(TASK, SOLUTION, timeout_seconds=0)
    payload = TASK.model_dump(mode="json")
    payload["public_cases"] = [{"x": i + 1000, "expected": i} for i in range(129)]
    with pytest.raises(ValueError, match="128"):
        FunctionTask.model_validate(payload)
