"""Bounded L0 function-repair verifier with a deliberately restricted language.

This is an AST interpreter, not Python ``exec`` and not a security boundary for
arbitrary code. A later containerized worker must own real untrusted submissions.
"""

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from forge.artifacts import ArtifactStore
from forge.canonical import canonical_bytes


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class TestCase(StrictModel):
    x: int = Field(strict=True, ge=-100_000, le=100_000)
    expected: int = Field(strict=True, ge=-1_000_000_000, le=1_000_000_000)


class FunctionTask(StrictModel):
    schema_version: Literal[1] = 1
    task_id: str = Field(min_length=3, pattern=r"^[a-z][a-z0-9_-]+$")
    public_cases: list[TestCase] = Field(min_length=1, max_length=128)
    heldout_cases: list[TestCase] = Field(min_length=1, max_length=128)
    step_limit: int = Field(default=1_000, ge=10, le=100_000)

    @model_validator(mode="after")
    def distinct_inputs(self) -> "FunctionTask":
        cases = self.public_cases + self.heldout_cases
        xs = [case.x for case in cases]
        if len(xs) != len(set(xs)):
            raise ValueError("public and held-out inputs must be distinct")
        return self


class InvalidSubmission(ValueError):
    pass


class TamperAttempt(ValueError):
    pass


class StepLimitExceeded(RuntimeError):
    pass


class SubmissionRuntimeError(RuntimeError):
    pass


_ALLOWED = (
    ast.Module,
    ast.FunctionDef,
    ast.arguments,
    ast.arg,
    ast.Assign,
    ast.AugAssign,
    ast.While,
    ast.If,
    ast.Return,
    ast.Pass,
    ast.Name,
    ast.Load,
    ast.Store,
    ast.Constant,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.BoolOp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.FloorDiv,
    ast.Mod,
    ast.UAdd,
    ast.USub,
    ast.Not,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.And,
    ast.Or,
)


def _program(source: str) -> ast.FunctionDef:
    if len(source.encode("utf-8")) > 16_384:
        raise InvalidSubmission("source exceeds 16 KiB")
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        raise InvalidSubmission(f"syntax error on line {error.lineno}") from error
    nodes = list(ast.walk(tree))
    if len(nodes) > 128:
        raise InvalidSubmission("program exceeds 128 syntax nodes")
    if any(not isinstance(node, _ALLOWED) for node in nodes):
        raise TamperAttempt("forbidden Python construct; only the bounded L0 DSL is accepted")
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise InvalidSubmission("submit exactly one function named solve")
    function = tree.body[0]
    if any(isinstance(node, ast.FunctionDef) and node is not function for node in nodes):
        raise TamperAttempt("nested functions are forbidden")
    args = function.args
    if (
        function.name != "solve"
        or len(args.args) != 1
        or args.args[0].arg != "x"
        or args.posonlyargs
        or args.kwonlyargs
        or args.defaults
        or args.kw_defaults
        or args.vararg
        or args.kwarg
        or function.decorator_list
        or function.returns is not None
        or args.args[0].annotation is not None
    ):
        raise InvalidSubmission("signature must be def solve(x): with no decorators or defaults")
    for node in nodes:
        if isinstance(node, ast.Name) and node.id.startswith("_"):
            raise TamperAttempt("private names are forbidden")
        if isinstance(node, ast.Constant):
            if type(node.value) not in (int, bool) or (
                type(node.value) is int and abs(node.value) > 1_000_000
            ):
                raise InvalidSubmission("only bounded integer and boolean literals are accepted")
        if isinstance(node, ast.Assign) and (
            len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name)
        ):
            raise InvalidSubmission("assignment requires one simple variable")
        if isinstance(node, ast.AugAssign) and not isinstance(node.target, ast.Name):
            raise InvalidSubmission("augmented assignment requires one simple variable")
        if isinstance(node, (ast.While, ast.If)) and node.orelse:
            raise InvalidSubmission("else on loops or conditionals is not supported in L0")
    return function


class _Budget:
    def __init__(self, limit: int):
        self.remaining = limit

    def tick(self) -> None:
        self.remaining -= 1
        if self.remaining < 0:
            raise StepLimitExceeded("bounded interpreter step limit exceeded")


def _bounded(value: int | bool) -> int | bool:
    if type(value) is int and abs(value) > 1_000_000_000:
        raise SubmissionRuntimeError("integer magnitude exceeded 1e9")
    return value


def _value(node: ast.expr, variables: dict[str, int], budget: _Budget) -> int | bool:
    budget.tick()
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in variables:
            raise SubmissionRuntimeError(f"undefined variable: {node.id}")
        return variables[node.id]
    if isinstance(node, ast.UnaryOp):
        operand = _value(node.operand, variables, budget)
        if isinstance(node.op, ast.Not):
            return not bool(operand)
        if type(operand) is not int:
            raise SubmissionRuntimeError("arithmetic needs integers")
        return _bounded(+operand if isinstance(node.op, ast.UAdd) else -operand)
    if isinstance(node, ast.BinOp):
        left = _value(node.left, variables, budget)
        right = _value(node.right, variables, budget)
        if type(left) is not int or type(right) is not int:
            raise SubmissionRuntimeError("arithmetic needs integers")
        if isinstance(node.op, ast.Add):
            result = left + right
        elif isinstance(node.op, ast.Sub):
            result = left - right
        elif isinstance(node.op, ast.Mult):
            result = left * right
        elif isinstance(node.op, ast.FloorDiv):
            if right == 0:
                raise SubmissionRuntimeError("division by zero")
            result = left // right
        else:
            if right == 0:
                raise SubmissionRuntimeError("modulo by zero")
            result = left % right
        return _bounded(result)
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            return all(bool(_value(item, variables, budget)) for item in node.values)
        return any(bool(_value(item, variables, budget)) for item in node.values)
    if isinstance(node, ast.Compare):
        left = _value(node.left, variables, budget)
        for operator, comparator in zip(node.ops, node.comparators):
            right = _value(comparator, variables, budget)
            if type(left) is not type(right):
                raise SubmissionRuntimeError("comparison types differ")
            matched = (
                left == right
                if isinstance(operator, ast.Eq)
                else left != right
                if isinstance(operator, ast.NotEq)
                else left < right
                if isinstance(operator, ast.Lt)
                else left <= right
                if isinstance(operator, ast.LtE)
                else left > right
                if isinstance(operator, ast.Gt)
                else left >= right
            )
            if not matched:
                return False
            left = right
        return True
    raise TamperAttempt("unsupported expression")


def _execute(statements: list[ast.stmt], variables: dict[str, int], budget: _Budget) -> int | None:
    for statement in statements:
        budget.tick()
        if isinstance(statement, ast.Return):
            if statement.value is None:
                raise SubmissionRuntimeError("solve must return an integer")
            answer = _value(statement.value, variables, budget)
            if type(answer) is not int:
                raise SubmissionRuntimeError("solve must return an integer")
            return answer
        if isinstance(statement, (ast.Assign, ast.AugAssign)):
            target = statement.targets[0] if isinstance(statement, ast.Assign) else statement.target
            value = _value(statement.value, variables, budget)
            if type(value) is not int:
                raise SubmissionRuntimeError("assigned values must be integers")
            if isinstance(statement, ast.AugAssign):
                current = variables.get(target.id)
                if current is None:
                    raise SubmissionRuntimeError(f"undefined variable: {target.id}")
                value = _value(
                    ast.BinOp(
                        left=ast.Constant(current), op=statement.op, right=ast.Constant(value)
                    ),
                    variables,
                    budget,
                )
            variables[target.id] = _bounded(value)
        elif isinstance(statement, ast.If):
            if bool(_value(statement.test, variables, budget)):
                answer = _execute(statement.body, variables, budget)
                if answer is not None:
                    return answer
        elif isinstance(statement, ast.While):
            while bool(_value(statement.test, variables, budget)):
                answer = _execute(statement.body, variables, budget)
                if answer is not None:
                    return answer
        elif not isinstance(statement, ast.Pass):
            raise TamperAttempt("unsupported statement")
    return None


def evaluate(task: FunctionTask, source: str) -> dict:
    """Score public and held-out cases without exposing held-out expected values."""
    source_hash = "sha256:" + hashlib.sha256(source.encode("utf-8")).hexdigest()
    try:
        function = _program(source)
    except InvalidSubmission as error:
        return {"status": "MALFORMED_OUTPUT", "reason": str(error), "source_hash": source_hash}
    except TamperAttempt as error:
        return {"status": "TAMPER_ATTEMPT", "reason": str(error), "source_hash": source_hash}

    outcomes = []
    for split, cases in (("public", task.public_cases), ("heldout", task.heldout_cases)):
        for index, case in enumerate(cases):
            try:
                answer = _execute(function.body, {"x": case.x}, _Budget(task.step_limit))
                if answer is None:
                    raise SubmissionRuntimeError("solve ended without a return")
                status = "PASS" if answer == case.expected else "TASK_FAILURE"
                reason = None if status == "PASS" else "wrong answer"
            except StepLimitExceeded as error:
                status, reason = "TIMEOUT", str(error)
            except SubmissionRuntimeError as error:
                status, reason = "TASK_FAILURE", str(error)
            except Exception as error:
                status, reason = "INFRASTRUCTURE_ERROR", type(error).__name__
            outcomes.append(
                {"split": split, "case_index": index, "status": status, "reason": reason}
            )
    public = [item for item in outcomes if item["split"] == "public"]
    heldout = [item for item in outcomes if item["split"] == "heldout"]
    statuses = {item["status"] for item in outcomes}
    overall = (
        "INFRASTRUCTURE_ERROR"
        if "INFRASTRUCTURE_ERROR" in statuses
        else "TIMEOUT"
        if "TIMEOUT" in statuses
        else "SOLVED"
        if statuses == {"PASS"}
        else "TASK_FAILURE"
    )
    return {
        "status": overall,
        "source_hash": source_hash,
        "task_id": task.task_id,
        "public_passed": sum(item["status"] == "PASS" for item in public),
        "public_total": len(public),
        "heldout_passed": sum(item["status"] == "PASS" for item in heldout),
        "heldout_total": len(heldout),
        "outcomes": outcomes,
        "claim_limit": "Bounded L0 DSL only; not a secure arbitrary-Python sandbox or final RLVR reward.",
    }


def evaluate_in_worker(task: FunctionTask, source: str, *, timeout_seconds: float = 5.0) -> dict:
    """Score through a fresh bounded process; child failures never become wrong answers."""
    source_hash = "sha256:" + hashlib.sha256(source.encode("utf-8")).hexdigest()

    def infrastructure_error(reason: str) -> dict:
        return {
            "status": "INFRASTRUCTURE_ERROR",
            "reason": reason,
            "task_id": task.task_id,
            "source_hash": source_hash,
        }

    if timeout_seconds <= 0:
        raise ValueError("worker timeout must be positive")
    request = canonical_bytes(
        {"schema_version": 1, "task": task.model_dump(mode="json"), "source": source}
    )
    if len(request) > 262_144:
        return infrastructure_error("worker_input_limit")
    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-m", "forge.verifier_worker"],
            input=request,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            env={"PYTHONUTF8": "1"},
        )
    except subprocess.TimeoutExpired:
        return infrastructure_error("worker_wall_timeout")
    except OSError:
        return infrastructure_error("worker_launch_failure")
    if completed.returncode != 0:
        return infrastructure_error(f"worker_exit_{completed.returncode}")
    if len(completed.stdout) > 262_144 or completed.stderr:
        return infrastructure_error("worker_protocol_output")
    try:
        payload = json.loads(completed.stdout)
        if (
            not isinstance(payload, dict)
            or set(payload) != {"schema_version", "result"}
            or payload["schema_version"] != 1
            or not isinstance(payload["result"], dict)
            or payload["result"].get("source_hash") != source_hash
            or (
                payload["result"].get("task_id") is not None
                and payload["result"]["task_id"] != task.task_id
            )
        ):
            raise ValueError("invalid worker response")
        if canonical_bytes(payload) != completed.stdout:
            raise ValueError("worker response is not canonical")
        return payload["result"]
    except (ValueError, UnicodeError):
        return infrastructure_error("worker_protocol_invalid")


def score_and_store(task_path: Path, source_path: Path, workspace: Path) -> dict:
    task = FunctionTask.model_validate_json(task_path.read_bytes())
    source = source_path.read_text(encoding="utf-8")
    result = evaluate_in_worker(task, source)
    store = ArtifactStore(workspace / ".forge" / "artifacts")
    result["task_ref"] = store.put(canonical_bytes(task.model_dump(mode="json")))
    result["source_ref"] = store.put(source.encode("utf-8"))
    result["report_ref"] = store.put(canonical_bytes(result))
    return result
