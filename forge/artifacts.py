"""Filesystem content-addressed store with verified reads and atomic publish."""

import hashlib
import os
import tempfile
from pathlib import Path


class ArtifactCorruption(ValueError):
    pass


class ArtifactStore:
    def __init__(self, root: Path):
        self.root = root

    def _path(self, ref: str) -> Path:
        algorithm, separator, hexdigest = ref.partition(":")
        if algorithm != "sha256" or not separator or len(hexdigest) != 64:
            raise ValueError("artifact reference must be sha256:<64 hex characters>")
        if any(char not in "0123456789abcdef" for char in hexdigest):
            raise ValueError("artifact digest must use lowercase hexadecimal")
        return self.root / "sha256" / hexdigest[:2] / hexdigest

    def put(self, payload: bytes) -> str:
        ref = "sha256:" + hashlib.sha256(payload).hexdigest()
        target = self._path(ref)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            self.get(ref)
            return ref
        descriptor, temporary = tempfile.mkstemp(prefix=".forge-", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return ref

    def get(self, ref: str) -> bytes:
        payload = self._path(ref).read_bytes()
        actual = "sha256:" + hashlib.sha256(payload).hexdigest()
        if actual != ref:
            raise ArtifactCorruption(f"artifact digest mismatch: expected {ref}, found {actual}")
        return payload
