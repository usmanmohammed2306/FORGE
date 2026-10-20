from pathlib import Path

import pytest

from forge.artifacts import ArtifactCorruption, ArtifactStore


def test_content_addressed_round_trip_and_corruption(tmp_path: Path):
    store = ArtifactStore(tmp_path / "artifacts")
    first = store.put(b"evidence")
    assert first == store.put(b"evidence")
    assert store.get(first) == b"evidence"
    target = store._path(first)
    target.write_bytes(b"tampered")
    with pytest.raises(ArtifactCorruption):
        store.get(first)
    with pytest.raises(ArtifactCorruption):
        store.put(b"evidence")


def test_artifact_reference_cannot_escape_store(tmp_path: Path):
    store = ArtifactStore(tmp_path / "artifacts")
    with pytest.raises(ValueError):
        store.get("sha256:../../outside")
