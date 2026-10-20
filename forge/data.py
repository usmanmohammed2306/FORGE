"""Small, deterministic CPU lineage builder for the first real data-plane slices."""

import hashlib
import re
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from forge.artifacts import ArtifactStore
from forge.canonical import canonical_bytes, digest


class DataRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    completion: str = Field(min_length=1)
    source: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    source_group: str = Field(min_length=1)


def read_jsonl(path: Path) -> list[DataRow]:
    rows = []
    seen = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = DataRow.model_validate_json(line)
        except Exception as error:
            raise ValueError(f"{path}:{line_number}: {error}") from error
        if row.id in seen:
            raise ValueError(f"{path}:{line_number}: duplicate row id {row.id}")
        seen.add(row.id)
        rows.append(row)
    if not rows:
        raise ValueError(f"{path}: no data rows")
    return rows


def normalized_text(text: str) -> str:
    return " ".join(re.findall(r"\w+", text.lower(), flags=re.UNICODE))


def shingles(text: str, width: int = 3) -> set[str]:
    tokens = normalized_text(text).split()
    if len(tokens) < width:
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[index : index + width]) for index in range(len(tokens) - width + 1)}


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def _fingerprint(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_dataset(
    training_path: Path,
    evaluation_path: Path,
    workspace: Path,
    *,
    near_duplicate_threshold: float = 0.8,
) -> dict:
    if not 0 < near_duplicate_threshold <= 1:
        raise ValueError("near-duplicate threshold must be in (0, 1]")
    training = read_jsonl(training_path)
    evaluation = read_jsonl(evaluation_path)
    eval_groups = {row.source_group for row in evaluation}
    eval_prompts = {normalized_text(row.prompt) for row in evaluation}
    kept: list[DataRow] = []
    signatures: list[set[str]] = []
    exact_pairs: set[tuple[str, str]] = set()
    shingle_postings: dict[str, set[int]] = {}
    empty_signatures: set[int] = set()
    removals = []
    for row in training:
        normalized = normalized_text(row.prompt)
        if row.source_group in eval_groups or normalized in eval_prompts:
            reason = "eval_contamination"
        elif (row.prompt, row.completion) in exact_pairs:
            reason = "exact_duplicate"
        else:
            signature = shingles(row.prompt)
            candidates: set[int] = set()
            if signature:
                for shingle in signature:
                    candidates.update(shingle_postings.get(shingle, ()))
            else:
                candidates.update(empty_signatures)
            reason = (
                "near_duplicate"
                if any(
                    jaccard(signature, signatures[index]) >= near_duplicate_threshold
                    for index in candidates
                )
                else None
            )
        if reason:
            removals.append(
                {"id": row.id, "reason": reason, "prompt_fingerprint": _fingerprint(row.prompt)}
            )
        else:
            index = len(kept)
            kept.append(row)
            signatures.append(signature)
            exact_pairs.add((row.prompt, row.completion))
            if signature:
                for shingle in signature:
                    shingle_postings.setdefault(shingle, set()).add(index)
            else:
                empty_signatures.add(index)

    if not kept:
        raise ValueError("all training rows were removed; cannot publish an empty dataset")
    clean_rows = [row.model_dump(mode="json") for row in sorted(kept, key=lambda row: row.id)]
    artifact_store = ArtifactStore(workspace / ".forge" / "artifacts")
    data_ref = artifact_store.put(b"\n".join(canonical_bytes(row) for row in clean_rows) + b"\n")
    manifest = {
        "schema_version": 1,
        "kind": "small_cpu_data_lineage",
        "dataset_id": digest(clean_rows, domain="forge.dataset.v1"),
        "training_source_ref": _fingerprint(training_path.read_text(encoding="utf-8")),
        "evaluation_source_ref": _fingerprint(evaluation_path.read_text(encoding="utf-8")),
        "raw_rows": len(training),
        "kept_rows": len(kept),
        "removed_rows": len(removals),
        "removals": removals,
        "clean_data_ref": data_ref,
        "dedup_algorithm": (
            "exact-pair lookup and shared-shingle candidate Jaccard; small CPU inputs only"
        ),
        "contamination_rule": "normalized prompt or source_group overlap with evaluation",
        "claim_limit": (
            "This is a small CPU lineage fixture. It has no model tokenizer, sequence packing, "
            "MinHash scaling, or guarantee against pretraining contamination."
        ),
    }
    manifest_ref = artifact_store.put(canonical_bytes(manifest))
    return {"manifest": manifest, "manifest_ref": manifest_ref}
