"""Portable, deterministic, fail-closed bundles for local CPU run evidence.

The archive is inspected in memory and never extracted by path. The format is
bounded for L0/CPU development; large accelerator checkpoints need a streaming
artifact transport in a later slice.
"""

import gzip
import hashlib
import io
import json
import os
import tarfile
import tempfile
from pathlib import Path

from forge.artifacts import ArtifactStore
from forge.audit import audit_run
from forge.canonical import canonical_bytes
from forge.contracts import Experiment
from forge.registry import RunRegistry
from forge.runner import CPU_LAYOUT_CLAIM_LIMIT, CPU_TRAIN_CLAIM_LIMIT

MAX_ARTIFACT_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 80 * 1024 * 1024
MAX_ARCHIVE_BYTES = 90 * 1024 * 1024
MAX_MEMBERS = 6
MANIFEST_NAME = "manifest.json"
BUNDLE_CLAIM_LIMIT = "Portable local CPU evidence only; no accelerator or release claim."


class BundleError(ValueError):
    pass


def _artifact_name(ref: str) -> str:
    algorithm, separator, hexdigest = ref.partition(":")
    if (
        algorithm != "sha256"
        or not separator
        or len(hexdigest) != 64
        or any(character not in "0123456789abcdef" for character in hexdigest)
    ):
        raise BundleError(f"invalid artifact reference: {ref}")
    return f"artifacts/sha256/{hexdigest}"


def _canonical_object(payload: bytes, label: str) -> dict:
    try:
        value = json.loads(payload)
        if not isinstance(value, dict) or canonical_bytes(value) != payload:
            raise BundleError(f"{label} is not a canonical JSON object")
        return value
    except (ValueError, UnicodeError) as error:
        raise BundleError(f"{label}: {error}") from error


def _validate_graph(manifest: dict, blobs: dict[str, bytes]) -> None:
    if manifest.get("schema_version") != 1 or manifest.get("kind") != "forge_cpu_run_bundle":
        raise BundleError("unsupported bundle schema or kind")
    if manifest.get("claim_limit") != BUNDLE_CLAIM_LIMIT:
        raise BundleError("bundle claim limit differs from the CPU-only contract")
    row = manifest.get("run")
    refs = manifest.get("artifact_refs")
    if not isinstance(row, dict) or not isinstance(refs, list):
        raise BundleError("bundle manifest lacks run or artifact references")
    if row.get("status") != "complete" or row.get("error") is not None:
        raise BundleError("only complete, error-free runs can be bundled")
    if not isinstance(row.get("run_id"), str) or not row["run_id"].startswith("RUN-"):
        raise BundleError("invalid run ID")
    required_refs = [row.get("config_ref"), row.get("report_ref"), row.get("passport_ref")]
    if any(not isinstance(ref, str) for ref in required_refs):
        raise BundleError("run has missing artifact references")
    if any(not isinstance(ref, str) for ref in refs) or refs != sorted(set(refs)):
        raise BundleError("artifact references must be sorted and unique")
    if set(refs) != set(blobs):
        raise BundleError("archive artifacts disagree with manifest")
    config = _canonical_object(blobs[row["config_ref"]], "config")
    report = _canonical_object(blobs[row["report_ref"]], "report")
    passport = _canonical_object(blobs[row["passport_ref"]], "passport")
    experiment = Experiment.model_validate(config)
    if experiment.hardware.backend != "cpu":
        raise BundleError("bundle V1 supports CPU evidence only")
    if experiment.config_digest != row.get("config_digest"):
        raise BundleError("config digest disagrees with run record")
    expected_kind = (
        "analytical_cpu_data_layout"
        if experiment.workload.kind == "packing"
        else "real_cpu_l0_training"
    )
    if report.get("schema_version") != 1 or report.get("kind") != expected_kind:
        raise BundleError("report kind or schema disagrees with config")
    expected_claim = (
        CPU_LAYOUT_CLAIM_LIMIT if experiment.workload.kind == "packing" else CPU_TRAIN_CLAIM_LIMIT
    )
    if report.get("claim_limit") != expected_claim:
        raise BundleError("report CPU claim limit disagrees with workload")
    if report.get("config_digest") != experiment.config_digest:
        raise BundleError("report config digest disagrees with config")
    expected_passport = {
        "schema_version": 1,
        "run_id": row["run_id"],
        "created_at": row.get("created_at"),
        "status": "complete",
        "config_digest": experiment.config_digest,
        "config_ref": row["config_ref"],
        "report_ref": row["report_ref"],
        "checkpoint_ref": report.get("checkpoint_ref"),
        "model": experiment.model.model_dump(mode="json"),
        "dataset": experiment.dataset.model_dump(mode="json"),
        "claim_limit": report.get("claim_limit"),
    }
    for field, expected in expected_passport.items():
        if passport.get(field) != expected:
            raise BundleError(f"passport {field} disagrees with run/config/report")
    hardware = passport.get("hardware")
    if (
        not isinstance(hardware, dict)
        or hardware.get("backend") != "cpu"
        or hardware.get("world_size") != 1
    ):
        raise BundleError("passport hardware disagrees with CPU config")
    checkpoint_ref = report.get("checkpoint_ref")
    expected_refs = set(required_refs)
    if checkpoint_ref is not None:
        if not isinstance(checkpoint_ref, str):
            raise BundleError("checkpoint reference is not a string")
        expected_refs.add(checkpoint_ref)
    if set(refs) != expected_refs:
        raise BundleError("bundle is missing or adding run artifacts")


def _member(name: str, payload: bytes) -> tuple[tarfile.TarInfo, io.BytesIO]:
    info = tarfile.TarInfo(name)
    info.size = len(payload)
    info.mode = 0o644
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    return info, io.BytesIO(payload)


def export_bundle(run_id: str, workspace: Path, output: Path) -> dict:
    """Export an audited run without overwriting an existing destination."""
    audit = audit_run(run_id, workspace)
    if audit["status"] != "VALID":
        raise BundleError(f"run audit failed: {audit['errors']}")
    if output.exists():
        raise FileExistsError(f"bundle already exists: {output}")
    root = workspace / ".forge"
    row = RunRegistry(root / "registry.sqlite3").get(run_id)
    store = ArtifactStore(root / "artifacts")
    report = _canonical_object(store.get(row["report_ref"]), "report")
    refs = {row["config_ref"], row["report_ref"], row["passport_ref"]}
    if report.get("checkpoint_ref"):
        refs.add(report["checkpoint_ref"])
    blobs = {ref: store.get(ref) for ref in refs}
    if (
        any(len(blob) > MAX_ARTIFACT_BYTES for blob in blobs.values())
        or sum(map(len, blobs.values())) > MAX_TOTAL_BYTES
    ):
        raise BundleError("L0 bundle size limit exceeded")
    manifest = {
        "schema_version": 1,
        "kind": "forge_cpu_run_bundle",
        "run": row,
        "artifact_refs": sorted(refs),
        "claim_limit": BUNDLE_CLAIM_LIMIT,
    }
    _validate_graph(manifest, blobs)
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".forge-bundle-", dir=output.parent)
    try:
        with os.fdopen(descriptor, "wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode="w") as archive:
                    info, stream = _member(MANIFEST_NAME, canonical_bytes(manifest))
                    archive.addfile(info, stream)
                    for ref in sorted(blobs):
                        info, stream = _member(_artifact_name(ref), blobs[ref])
                        archive.addfile(info, stream)
            raw.flush()
            os.fsync(raw.fileno())
        os.link(temporary, output)
    finally:
        os.unlink(temporary)
    summary = verify_bundle(output)
    if summary["status"] != "VALID":
        raise BundleError(f"exported archive failed verification: {summary['errors']}")
    return summary


def _read_bundle(path: Path) -> tuple[dict, dict[str, bytes]]:
    try:
        if path.stat().st_size > MAX_ARCHIVE_BYTES:
            raise BundleError("compressed archive size limit exceeded")
        with tarfile.open(path, mode="r:gz") as archive:
            members = []
            total_size = 0
            while (member := archive.next()) is not None:
                if not member.isfile() or member.size > MAX_ARTIFACT_BYTES:
                    raise BundleError("unsafe member type or oversized member")
                total_size += member.size
                if total_size > MAX_TOTAL_BYTES:
                    raise BundleError("bundle uncompressed size limit exceeded")
                members.append(member)
                if len(members) > MAX_MEMBERS:
                    raise BundleError("unexpected number of archive members")
            if len(members) < 4 or len(members) > MAX_MEMBERS:
                raise BundleError("unexpected number of archive members")
            names = [member.name for member in members]
            if len(names) != len(set(names)) or names[0] != MANIFEST_NAME:
                raise BundleError("duplicate names or missing first manifest")
            manifest_stream = archive.extractfile(members[0])
            if manifest_stream is None or members[0].size > 65_536:
                raise BundleError("invalid manifest member")
            manifest = _canonical_object(manifest_stream.read(), "manifest")
            declared = manifest.get("artifact_refs")
            if not isinstance(declared, list) or len(declared) != len(members) - 1:
                raise BundleError("manifest artifact count disagrees with archive")
            expected_names = [_artifact_name(ref) for ref in declared]
            if names[1:] != expected_names:
                raise BundleError("unexpected or unsafe archive member name")
            blobs = {}
            for ref, member in zip(declared, members[1:]):
                stream = archive.extractfile(member)
                if stream is None:
                    raise BundleError("archive member cannot be read")
                payload = stream.read(member.size + 1)
                if len(payload) != member.size:
                    raise BundleError("archive member has an invalid size")
                if "sha256:" + hashlib.sha256(payload).hexdigest() != ref:
                    raise BundleError(f"artifact digest mismatch: {ref}")
                blobs[ref] = payload
        _validate_graph(manifest, blobs)
        return manifest, blobs
    except (tarfile.TarError, EOFError, OSError, KeyError, TypeError, ValueError) as error:
        if isinstance(error, BundleError):
            raise
        raise BundleError(f"invalid bundle: {error}") from error


def verify_bundle(path: Path) -> dict:
    """Validate archive names, bytes, and provenance without extracting files."""
    try:
        manifest, blobs = _read_bundle(path)
    except (BundleError, FileNotFoundError) as error:
        return {"status": "INVALID", "errors": [str(error)]}
    return {
        "status": "VALID",
        "run_id": manifest["run"]["run_id"],
        "artifact_count": len(blobs),
        "uncompressed_artifact_bytes": sum(map(len, blobs.values())),
        "bundle_sha256": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
        "claim_limit": manifest["claim_limit"],
    }


def import_bundle(path: Path, workspace: Path) -> dict:
    """Import a validated run; identical reimports are safe, conflicts fail."""
    manifest, blobs = _read_bundle(path)
    row = manifest["run"]
    root = workspace / ".forge"
    if (root / "registry.sqlite3").exists():
        existing_audit = audit_run(row["run_id"], workspace)
        if existing_audit["status"] == "VALID":
            existing = RunRegistry(root / "registry.sqlite3").get(row["run_id"])
            if existing == row:
                return {"status": "ALREADY_PRESENT", "run_id": row["run_id"]}
            raise BundleError("run ID already exists with different evidence")
        if "unknown run" not in " ".join(existing_audit["errors"]):
            raise BundleError("target registry has invalid or conflicting run evidence")
    store = ArtifactStore(root / "artifacts")
    for ref, payload in blobs.items():
        if store.put(payload) != ref:
            raise BundleError("artifact changed during import")
    registry = RunRegistry(root / "registry.sqlite3")
    registry.start(row["run_id"], row["created_at"], row["config_digest"], row["config_ref"])
    registry.complete(row["run_id"], row["report_ref"], row["passport_ref"])
    audit = audit_run(row["run_id"], workspace)
    if audit["status"] != "VALID":
        raise BundleError(f"imported run failed local audit: {audit['errors']}")
    return {"status": "IMPORTED", "run_id": row["run_id"], "warnings": audit["warnings"]}
