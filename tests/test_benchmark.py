"""Synthetic protocol fixtures only; these are never accelerator measurements."""

import json

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from forge.artifacts import ArtifactStore
from forge.benchmark import A100BenchmarkSpec, analyze, preregister
from forge.canonical import canonical_bytes, digest
from forge.cli import app


def _spec():
    return {
        "campaign_id": "synthetic_a100_protocol",
        "model_id": "test/model-2b",
        "model_revision": "revision123",
        "model_license": "test-only",
        "tokenizer_revision": "revision123",
        "dataset_digest": "sha256:" + "a" * 64,
        "dataset_license": "test-only",
        "heldout_digest": "sha256:" + "b" * 64,
        "hardware_name": "NVIDIA A100-SXM4-80GB",
        "effective_batch_size": 8,
        "target_useful_tokens_per_trial": 32768,
        "warmup_steps": 3,
        "measured_steps": 10,
        "trial_repeats": 3,
        "seeds": [11, 22, 33],
        "heldout_task_ids": [f"task_{i:02d}" for i in range(30)],
        "intervention_key": "packing",
        "baseline_config": {"packing": False, "lora_rank": 16},
        "candidate_config": {"packing": True, "lora_rank": 16},
        "hypothesis": "Packing may improve measured useful token throughput.",
    }


def _fixture(tmp_path):
    store = ArtifactStore(tmp_path / ".forge" / "artifacts")
    spec_path = tmp_path / "spec.json"
    spec_path.write_bytes(canonical_bytes(_spec()))
    spec_ref = preregister(spec_path, tmp_path)["spec_ref"]
    passport_ref = store.put(
        canonical_bytes(
            {
                "kind": "accelerator_preflight",
                "status": "READY",
                "backend": "cuda",
                "device": {"name": "NVIDIA A100-SXM4-80GB"},
                "smoke": {"float32": {"status": "PASS"}, "bfloat16": {"status": "PASS"}},
                "synthetic_test_fixture": True,
            }
        )
    )
    software_ref = store.put(canonical_bytes({"torch": "synthetic-test-only"}))
    trial_refs = []
    quality_refs = []
    for seed in [11, 22, 33]:
        for arm in ("baseline", "candidate"):
            for repeat in range(3):
                record = {
                    "spec_ref": spec_ref,
                    "arm": arm,
                    "seed": seed,
                    "repeat": repeat,
                    "hardware_passport_ref": passport_ref,
                    "software_lock_ref": software_ref,
                    "model_revision": "revision123",
                    "dataset_digest": "sha256:" + "a" * 64,
                    "arm_config_digest": digest(
                        _spec()["baseline_config" if arm == "baseline" else "candidate_config"],
                        domain="forge-benchmark-arm-v1",
                    ),
                    "effective_batch_size": 8,
                    "warmup_steps": 3,
                    "measured_steps": 10,
                    "useful_tokens": 32768,
                    "elapsed_seconds": 100.0 if arm == "baseline" else 80.0,
                    "peak_device_memory_bytes": 80_000 if arm == "baseline" else 56_000,
                    "step_latencies_ms": [10_000.0 if arm == "baseline" else 8_000.0] * 10,
                }
                trial_refs.append(store.put(canonical_bytes(record)))
            outcomes = []
            for task_id in _spec()["heldout_task_ids"]:
                solved = task_id != "task_29"
                verifier_ref = store.put(
                    canonical_bytes(
                        {"task_id": task_id, "status": "SOLVED" if solved else "TASK_FAILURE"}
                    )
                )
                outcomes.append(
                    {"task_id": task_id, "solved": solved, "verifier_report_ref": verifier_ref}
                )
            quality_refs.append(
                store.put(
                    canonical_bytes(
                        {"spec_ref": spec_ref, "arm": arm, "seed": seed, "outcomes": outcomes}
                    )
                )
            )
    index = {"spec_ref": spec_ref, "trial_refs": trial_refs, "quality_refs": quality_refs}
    index_path = tmp_path / "index.json"
    index_path.write_bytes(canonical_bytes(index))
    return store, index_path, index


def test_spec_requires_one_isolated_intervention_and_unique_evaluation():
    bad = _spec()
    bad["candidate_config"]["lora_rank"] = 32
    with pytest.raises(ValidationError, match="exactly the declared intervention"):
        A100BenchmarkSpec.model_validate(bad)
    bad = _spec()
    bad["heldout_task_ids"][-1] = bad["heldout_task_ids"][0]
    with pytest.raises(ValidationError, match="task IDs must be unique"):
        A100BenchmarkSpec.model_validate(bad)


def test_synthetic_paired_analysis_never_claims_authenticated_measurement(tmp_path):
    _, index_path, _ = _fixture(tmp_path)
    result = analyze(index_path, tmp_path)
    report = result["report"]
    assert report["status"] == "PRELIMINARY_UNAUTHENTICATED"
    assert report["trial_pairs"] == 9
    assert report["heldout_tasks"] == 30
    assert report["target_bounds_check"]["target_met"]
    assert "not independently authenticated" in report["claim_limit"]


def test_missing_pair_or_duplicate_evidence_is_rejected(tmp_path):
    _, index_path, index = _fixture(tmp_path)
    index["trial_refs"].pop()
    index_path.write_bytes(canonical_bytes(index))
    with pytest.raises(ValueError, match="one baseline and one candidate"):
        analyze(index_path, tmp_path)
    index["trial_refs"].append(index["trial_refs"][0])
    index_path.write_bytes(canonical_bytes(index))
    with pytest.raises(ValidationError, match="duplicate evidence"):
        analyze(index_path, tmp_path)


def test_changed_workload_or_hardware_is_rejected(tmp_path):
    store, index_path, index = _fixture(tmp_path)
    trial = json.loads(store.get(index["trial_refs"][0]))
    trial["effective_batch_size"] = 16
    index["trial_refs"][0] = store.put(canonical_bytes(trial))
    index_path.write_bytes(canonical_bytes(index))
    with pytest.raises(ValueError, match="frozen workload control"):
        analyze(index_path, tmp_path)
    trial["effective_batch_size"] = 8
    trial["hardware_passport_ref"] = store.put(
        canonical_bytes(
            {
                "kind": "accelerator_preflight",
                "status": "READY",
                "backend": "cuda",
                "device": {"name": "different GPU"},
            }
        )
    )
    index["trial_refs"][0] = store.put(canonical_bytes(trial))
    index_path.write_bytes(canonical_bytes(index))
    with pytest.raises(ValueError, match="matching READY CUDA"):
        analyze(index_path, tmp_path)


def test_infrastructure_failure_cannot_be_scored_as_quality_failure(tmp_path):
    store, index_path, index = _fixture(tmp_path)
    record = json.loads(store.get(index["quality_refs"][0]))
    first = record["outcomes"][0]
    first["solved"] = False
    first["verifier_report_ref"] = store.put(
        canonical_bytes({"task_id": first["task_id"], "status": "INFRASTRUCTURE_ERROR"})
    )
    index["quality_refs"][0] = store.put(canonical_bytes(record))
    index_path.write_bytes(canonical_bytes(index))
    with pytest.raises(ValueError, match="disagrees with verifier"):
        analyze(index_path, tmp_path)


def test_mixed_software_locks_are_rejected(tmp_path):
    store, index_path, index = _fixture(tmp_path)
    trial = json.loads(store.get(index["trial_refs"][0]))
    trial["software_lock_ref"] = store.put(canonical_bytes({"torch": "different"}))
    index["trial_refs"][0] = store.put(canonical_bytes(trial))
    index_path.write_bytes(canonical_bytes(index))
    with pytest.raises(ValueError, match="one frozen software lock"):
        analyze(index_path, tmp_path)


def test_cli_can_preregister_but_no_hardware_claim(tmp_path):
    spec_path = tmp_path / "spec.json"
    spec_path.write_bytes(canonical_bytes(_spec()))
    result = CliRunner().invoke(
        app, ["benchmark", "preregister", str(spec_path), "--workspace", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["status"] == "PREREGISTERED"
