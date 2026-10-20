"""Fail-closed inventory for the mandatory V1 evidence set."""

import json
from pathlib import Path

from forge.artifacts import ArtifactStore

REQUIRED_EVIDENCE = (
    "lora_vs_qlora",
    "activation_checkpointing",
    "packing_efficiency",
    "torch_compile",
    "gaudi_bucketing",
    "a100_triton_liger_kernels",
    "gaudi_fused_op",
    "attention_comparison",
    "hccl_collectives",
    "ddp_vs_sharding",
    "distributed_checkpoint_recovery",
    "sft",
    "dpo",
    "grpo",
    "reward_variance_failure",
    "vllm_rollout",
    "serving_a100",
    "serving_gaudi",
    "ptq",
    "qat",
    "forge_doctor",
    "campaign_frontier",
    "forge_atlas",
    "published_checkpoint_recipe",
    "clean_room_reproduction",
)


def verify_release_index(workspace: Path) -> dict:
    """Check referenced bytes; later slices add experiment-specific semantic gates."""
    index_path = workspace / ".forge" / "release-evidence.json"
    if not index_path.exists():
        return {"status": "FAIL", "missing": list(REQUIRED_EVIDENCE), "invalid": []}
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
        if not isinstance(index, dict):
            raise ValueError("release index must be a JSON object")
    except (json.JSONDecodeError, ValueError) as error:
        return {"status": "FAIL", "missing": [], "invalid": [f"index: {error}"]}
    store = ArtifactStore(workspace / ".forge" / "artifacts")
    missing = []
    invalid = []
    for name in REQUIRED_EVIDENCE:
        ref = index.get(name)
        if ref is None:
            missing.append(name)
            continue
        if not isinstance(ref, str):
            invalid.append(f"{name}: reference must be a string")
            continue
        try:
            store.get(ref)
        except (ValueError, FileNotFoundError) as error:
            invalid.append(f"{name}: {error}")
    return {
        "status": "FAIL",
        "missing": missing,
        "invalid": invalid,
        "unimplemented_gate": (
            "Experiment semantics, clean-room proof, statistical review, and hardware "
            "compatibility checks are not implemented yet. Digest presence cannot release V1."
        ),
    }
