"""One-shot process for the bounded L0 verifier protocol.

It never executes submitted Python. The parent supplies parsed task data and source
text, and kills this process if it exceeds a wall-clock deadline. This is failure
containment, not a container or security isolation for arbitrary user programs.
"""

import json
import sys

from forge.canonical import canonical_bytes
from forge.verifier import FunctionTask, evaluate

MAX_INPUT_BYTES = 262_144


def _limits() -> None:
    try:
        import resource
    except ImportError:
        return
    resource.setrlimit(resource.RLIMIT_CPU, (2, 3))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1_048_576, 1_048_576))


def main() -> int:
    try:
        _limits()
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError("worker request exceeds size limit")
        request = json.loads(raw)
        if not isinstance(request, dict) or set(request) != {"schema_version", "task", "source"}:
            raise ValueError("invalid worker request shape")
        if request["schema_version"] != 1 or not isinstance(request["source"], str):
            raise ValueError("unsupported worker request")
        task = FunctionTask.model_validate(request["task"])
        response = {"schema_version": 1, "result": evaluate(task, request["source"])}
        sys.stdout.buffer.write(canonical_bytes(response))
        return 0
    except Exception as error:
        print(f"worker failure: {type(error).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
