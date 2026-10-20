import io
import json
import tarfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from forge.artifacts import ArtifactStore
from forge.audit import audit_run
from forge.bundle import BundleError, export_bundle, import_bundle, verify_bundle
from forge.cli import app
from forge.contracts import Experiment
from forge.runner import load_report, run_experiment


def _packing_run(workspace: Path) -> str:
    experiment = Experiment.model_validate_json(Path("configs/l0_packing.json").read_bytes())
    return run_experiment(experiment, workspace)["passport"]["run_id"]


def _write_archive(path: Path, members: list[tuple[str, bytes, str]]) -> None:
    with tarfile.open(path, "w:gz") as archive:
        for name, payload, kind in members:
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            if kind == "symlink":
                info.type = tarfile.SYMTYPE
                info.linkname = "../outside"
                info.size = 0
                archive.addfile(info)
            else:
                archive.addfile(info, io.BytesIO(payload))


def test_deterministic_bundle_round_trip_and_cli(tmp_path: Path):
    source = tmp_path / "source"
    target = tmp_path / "clean"
    run_id = _packing_run(source)
    first = tmp_path / "one.tar.gz"
    second = tmp_path / "two.tar.gz"
    assert export_bundle(run_id, source, first)["status"] == "VALID"
    export_bundle(run_id, source, second)
    assert first.read_bytes() == second.read_bytes()
    assert import_bundle(first, target)["status"] == "IMPORTED"
    assert import_bundle(first, target)["status"] == "ALREADY_PRESENT"
    assert audit_run(run_id, target)["status"] == "VALID"
    assert load_report(run_id, source) == load_report(run_id, target)
    reproduced = CliRunner().invoke(app, ["reproduce", run_id, "--workspace", str(target)])
    assert reproduced.exit_code == 0
    assert json.loads(reproduced.stdout)["status"] == "EXACT_REPORT_MATCH"
    assert CliRunner().invoke(app, ["bundle", "verify", str(first)]).exit_code == 0
    third = tmp_path / "three.tar.gz"
    assert (
        CliRunner()
        .invoke(app, ["bundle", "export", run_id, str(third), "--workspace", str(source)])
        .exit_code
        == 0
    )
    assert third.read_bytes() == first.read_bytes()
    clean_cli = tmp_path / "clean-cli"
    assert (
        CliRunner()
        .invoke(app, ["bundle", "import", str(third), "--workspace", str(clean_cli)])
        .exit_code
        == 0
    )
    assert audit_run(run_id, clean_cli)["status"] == "VALID"
    assert (
        CliRunner()
        .invoke(app, ["bundle", "export", run_id, str(first), "--workspace", str(source)])
        .exit_code
        == 2
    )


def test_bundle_with_checkpoint_round_trips(tmp_path: Path):
    pytest.importorskip("torch")
    source = tmp_path / "source"
    target = tmp_path / "target"
    experiment = Experiment.model_validate_json(Path("configs/l0_train.json").read_bytes())
    run_id = run_experiment(experiment, source)["passport"]["run_id"]
    bundle = tmp_path / "train.tar.gz"
    summary = export_bundle(run_id, source, bundle)
    assert summary["artifact_count"] == 4
    assert import_bundle(bundle, target)["status"] == "IMPORTED"
    assert (
        load_report(run_id, target)["checkpoint_ref"]
        == load_report(run_id, source)["checkpoint_ref"]
    )


def test_archive_traversal_and_symlink_rejected_without_extraction(tmp_path: Path):
    outside = tmp_path / "outside"
    bundle = tmp_path / "malicious.tar.gz"
    _write_archive(
        bundle,
        [
            ("manifest.json", b"{}", "file"),
            ("../outside", b"owned", "file"),
            ("artifacts/sha256/x", b"x", "symlink"),
            ("extra", b"x", "file"),
        ],
    )
    assert verify_bundle(bundle)["status"] == "INVALID"
    with pytest.raises(BundleError):
        import_bundle(bundle, tmp_path / "clean")
    assert not outside.exists()
    assert not (tmp_path / "clean").exists()


def test_validly_rehashed_fabricated_manifest_fails_semantic_checks(tmp_path: Path):
    source = tmp_path / "source"
    run_id = _packing_run(source)
    original = tmp_path / "original.tar.gz"
    export_bundle(run_id, source, original)
    with tarfile.open(original, "r:gz") as archive:
        members = [
            (member.name, archive.extractfile(member).read(), "file")
            for member in archive.getmembers()
        ]
    manifest = json.loads(members[0][1])
    manifest["run"]["config_digest"] = "sha256:" + "0" * 64
    from forge.canonical import canonical_bytes

    members[0] = ("manifest.json", canonical_bytes(manifest), "file")
    forged = tmp_path / "forged.tar.gz"
    _write_archive(forged, members)
    result = verify_bundle(forged)
    assert result["status"] == "INVALID"
    assert "config digest disagrees" in result["errors"][0]


def test_bundle_rejects_claim_escalation_in_manifest(tmp_path: Path):
    source = tmp_path / "source"
    run_id = _packing_run(source)
    original = tmp_path / "original.tar.gz"
    export_bundle(run_id, source, original)
    with tarfile.open(original, "r:gz") as archive:
        members = [
            (member.name, archive.extractfile(member).read(), "file")
            for member in archive.getmembers()
        ]
    from forge.canonical import canonical_bytes

    manifest = json.loads(members[0][1])
    manifest["claim_limit"] = "A100 speedup proven"
    members[0] = ("manifest.json", canonical_bytes(manifest), "file")
    forged = tmp_path / "escalated.tar.gz"
    _write_archive(forged, members)
    result = verify_bundle(forged)
    assert result["status"] == "INVALID"
    assert "CPU-only contract" in result["errors"][0]


def test_bundle_rejects_artifact_bytes_changed_without_ref_change(tmp_path: Path):
    source = tmp_path / "source"
    run_id = _packing_run(source)
    original = tmp_path / "original.tar.gz"
    export_bundle(run_id, source, original)
    with tarfile.open(original, "r:gz") as archive:
        members = [
            (member.name, archive.extractfile(member).read(), "file")
            for member in archive.getmembers()
        ]
    name, payload, kind = members[1]
    members[1] = (name, payload + b"changed", kind)
    corrupted = tmp_path / "corrupted.tar.gz"
    _write_archive(corrupted, members)
    result = verify_bundle(corrupted)
    assert result["status"] == "INVALID"
    assert "artifact digest mismatch" in result["errors"][0]


def test_bundle_rejects_duplicate_archive_names(tmp_path: Path):
    bundle = tmp_path / "duplicate.tar.gz"
    _write_archive(bundle, [("manifest.json", b"{}", "file")] * 4)
    assert verify_bundle(bundle)["status"] == "INVALID"


def test_export_refuses_invalid_run_without_writing(tmp_path: Path):
    destination = tmp_path / "not-created.tar.gz"
    with pytest.raises(BundleError, match="run audit failed"):
        export_bundle("RUN-doesnotexist", tmp_path / "workspace", destination)
    assert not destination.exists()


def test_import_refuses_preexisting_corrupt_artifact(tmp_path: Path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    run_id = _packing_run(source)
    bundle = tmp_path / "run.tar.gz"
    export_bundle(run_id, source, bundle)
    from forge.registry import RunRegistry

    row = RunRegistry(source / ".forge" / "registry.sqlite3").get(run_id)
    store = ArtifactStore(target / ".forge" / "artifacts")
    corrupt_path = store._path(row["config_ref"])
    corrupt_path.parent.mkdir(parents=True)
    corrupt_path.write_bytes(b"wrong bytes")
    result = CliRunner().invoke(app, ["bundle", "import", str(bundle), "--workspace", str(target)])
    assert result.exit_code == 2
    assert "artifact digest mismatch" in result.stderr
    assert not (target / ".forge" / "registry.sqlite3").exists()
