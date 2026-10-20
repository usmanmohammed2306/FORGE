"""Pre-index pairwise reference for the CPU data-lineage microbenchmark only."""

import hashlib
from pathlib import Path

from forge.artifacts import ArtifactStore
from forge.canonical import canonical_bytes, digest
from forge.data import jaccard, normalized_text, read_jsonl, shingles


def _fingerprint(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_dataset_pairwise(
    training_path: Path,
    evaluation_path: Path,
    workspace: Path,
    *,
    near_duplicate_threshold: float = 0.8,
) -> dict:
    """Preserve the original pairwise loop as a reproducible baseline, not production code."""
    if not 0 < near_duplicate_threshold <= 1:
        raise ValueError("near-duplicate threshold must be in (0, 1]")
    training = read_jsonl(training_path)
    evaluation = read_jsonl(evaluation_path)
    eval_groups = {row.source_group for row in evaluation}
    eval_prompts = {normalized_text(row.prompt) for row in evaluation}
    kept = []
    signatures = []
    removals = []
    for row in training:
        normalized = normalized_text(row.prompt)
        if row.source_group in eval_groups or normalized in eval_prompts:
            reason = "eval_contamination"
        elif any(
            row.prompt == other.prompt and row.completion == other.completion for other in kept
        ):
            reason = "exact_duplicate"
        else:
            signature = shingles(row.prompt)
            reason = (
                "near_duplicate"
                if any(
                    jaccard(signature, previous) >= near_duplicate_threshold
                    for previous in signatures
                )
                else None
            )
        if reason:
            removals.append(
                {"id": row.id, "reason": reason, "prompt_fingerprint": _fingerprint(row.prompt)}
            )
        else:
            kept.append(row)
            signatures.append(shingles(row.prompt))
    if not kept:
        raise ValueError("all training rows were removed; cannot publish an empty dataset")
    clean_rows = [row.model_dump(mode="json") for row in sorted(kept, key=lambda row: row.id)]
    store = ArtifactStore(workspace / ".forge" / "artifacts")
    data_ref = store.put(b"\n".join(canonical_bytes(row) for row in clean_rows) + b"\n")
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
        "dedup_algorithm": "exact and pairwise prompt-shingle Jaccard; small CPU inputs only",
        "contamination_rule": "normalized prompt or source_group overlap with evaluation",
        "claim_limit": (
            "This is a small CPU lineage fixture. It has no model tokenizer, sequence packing, "
            "MinHash scaling, or guarantee against pretraining contamination."
        ),
    }
    manifest_ref = store.put(canonical_bytes(manifest))
    return {"manifest": manifest, "manifest_ref": manifest_ref}
