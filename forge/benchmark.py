"""Preregistered, evidence-linked analysis for the first A100 SFT comparison.

This consumes reports created elsewhere; it does not run training or authenticate
their origin. A real Forge runner and release audit must establish provenance.
"""

import json
import random
import re
from collections import defaultdict
from pathlib import Path
from statistics import median
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from forge.artifacts import ArtifactStore
from forge.canonical import canonical_bytes, digest
from forge.stats import Interval, judge_centerpiece_target, paired_relative_change

SHA256 = r"^sha256:[0-9a-f]{64}$"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class A100BenchmarkSpec(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["a100_sft_centerpiece"] = "a100_sft_centerpiece"
    campaign_id: str = Field(min_length=3, pattern=r"^[a-z][a-z0-9_-]+$")
    model_id: str = Field(min_length=1)
    model_revision: str = Field(min_length=8)
    model_license: str = Field(min_length=2)
    tokenizer_revision: str = Field(min_length=8)
    dataset_digest: str = Field(pattern=SHA256)
    dataset_license: str = Field(min_length=2)
    heldout_digest: str = Field(pattern=SHA256)
    hardware_name: str = Field(min_length=5)
    context_length: Literal[2048] = 2048
    precision: Literal["bf16"] = "bf16"
    effective_batch_size: int = Field(ge=1)
    target_useful_tokens_per_trial: int = Field(ge=2048)
    warmup_steps: int = Field(ge=3)
    measured_steps: int = Field(ge=10)
    trial_repeats: int = Field(ge=3, le=20)
    seeds: list[int] = Field(min_length=3, max_length=10)
    heldout_task_ids: list[str] = Field(min_length=30)
    intervention_key: str = Field(min_length=1)
    baseline_config: dict
    candidate_config: dict
    hypothesis: str = Field(min_length=20)
    useful_token_definition: Literal["nonpadding_input_tokens"] = "nonpadding_input_tokens"
    timing_definition: Literal["synchronized_measured_training_interval"] = (
        "synchronized_measured_training_interval"
    )
    memory_definition: Literal["cuda_max_memory_allocated_bytes"] = (
        "cuda_max_memory_allocated_bytes"
    )

    @model_validator(mode="after")
    def controls_are_frozen(self) -> "A100BenchmarkSpec":
        if len(set(self.seeds)) != len(self.seeds):
            raise ValueError("seeds must be unique")
        if len(set(self.heldout_task_ids)) != len(self.heldout_task_ids):
            raise ValueError("held-out task IDs must be unique")
        if self.dataset_digest == self.heldout_digest:
            raise ValueError("training and held-out dataset digests must differ")
        keys = set(self.baseline_config) | set(self.candidate_config)
        changed = {
            key for key in keys if self.baseline_config.get(key) != self.candidate_config.get(key)
        }
        if changed != {self.intervention_key}:
            raise ValueError("candidate must change exactly the declared intervention key")
        return self


class TrialRecord(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["a100_sft_trial"] = "a100_sft_trial"
    spec_ref: str = Field(pattern=SHA256)
    arm: Literal["baseline", "candidate"]
    seed: int
    repeat: int = Field(ge=0)
    hardware_passport_ref: str = Field(pattern=SHA256)
    software_lock_ref: str = Field(pattern=SHA256)
    model_revision: str
    dataset_digest: str = Field(pattern=SHA256)
    arm_config_digest: str = Field(pattern=SHA256)
    context_length: Literal[2048] = 2048
    precision: Literal["bf16"] = "bf16"
    effective_batch_size: int = Field(ge=1)
    warmup_steps: int = Field(ge=0)
    measured_steps: int = Field(ge=1)
    useful_tokens: int = Field(gt=0)
    elapsed_seconds: float = Field(gt=0)
    peak_device_memory_bytes: int = Field(gt=0)
    step_latencies_ms: list[float] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_latencies(self) -> "TrialRecord":
        if len(self.step_latencies_ms) != self.measured_steps:
            raise ValueError("step latency count must equal measured_steps")
        if any(value <= 0 for value in self.step_latencies_ms):
            raise ValueError("step latencies must be positive")
        return self


class QualityOutcome(StrictModel):
    task_id: str = Field(min_length=1)
    solved: bool = Field(strict=True)
    verifier_report_ref: str = Field(pattern=SHA256)


class QualityRecord(StrictModel):
    schema_version: Literal[1] = 1
    kind: Literal["a100_sft_quality"] = "a100_sft_quality"
    spec_ref: str = Field(pattern=SHA256)
    arm: Literal["baseline", "candidate"]
    seed: int
    outcomes: list[QualityOutcome] = Field(min_length=30)


class BenchmarkIndex(StrictModel):
    schema_version: Literal[1] = 1
    spec_ref: str = Field(pattern=SHA256)
    trial_refs: list[str] = Field(min_length=1)
    quality_refs: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def no_duplicate_refs(self) -> "BenchmarkIndex":
        for refs in (self.trial_refs, self.quality_refs):
            if len(refs) != len(set(refs)):
                raise ValueError("duplicate evidence references are forbidden")
            if any(not re.fullmatch(SHA256, ref) for ref in refs):
                raise ValueError("evidence references must be sha256 digests")
        return self


def _load_model(store: ArtifactStore, ref: str, model_type):
    payload = store.get(ref)
    value = json.loads(payload)
    if canonical_bytes(value) != payload:
        raise ValueError(f"noncanonical evidence artifact: {ref}")
    if model_type is dict:
        if not isinstance(value, dict):
            raise ValueError(f"evidence artifact is not a JSON object: {ref}")
        return value
    return model_type.model_validate(value)


def preregister(spec_path: Path, workspace: Path) -> dict:
    spec = A100BenchmarkSpec.model_validate_json(spec_path.read_bytes())
    ref = ArtifactStore(workspace / ".forge" / "artifacts").put(
        canonical_bytes(spec.model_dump(mode="json"))
    )
    return {"status": "PREREGISTERED", "spec_ref": ref, "campaign_id": spec.campaign_id}


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def _hierarchical_quality_interval(qualities: dict, spec: A100BenchmarkSpec) -> Interval:
    """Resample training seeds and held-out tasks, preserving paired arms."""
    task_ids = spec.heldout_task_ids
    task_count = len(task_ids)
    seed_count = len(spec.seeds)
    delta_matrix = []
    for seed in spec.seeds:
        baseline = {item.task_id: item.solved for item in qualities[seed, "baseline"].outcomes}
        candidate = {item.task_id: item.solved for item in qualities[seed, "candidate"].outcomes}
        delta_matrix.append([int(candidate[task]) - int(baseline[task]) for task in task_ids])
    estimate = sum(sum(row) for row in delta_matrix) / (seed_count * task_count)
    rng = random.Random(0)
    draws = []
    for _ in range(10_000):
        sampled_seeds = [rng.randrange(seed_count) for _ in range(seed_count)]
        sampled_tasks = [rng.randrange(task_count) for _ in range(task_count)]
        draws.append(
            sum(delta_matrix[seed][task] for seed in sampled_seeds for task in sampled_tasks)
            / (seed_count * task_count)
        )
    return Interval(
        estimate, _percentile(draws, 0.025), _percentile(draws, 0.975), 0.95, seed_count
    )


def analyze(index_path: Path, workspace: Path) -> dict:
    """Reject incomparable records and compute paired, descriptive evidence."""
    store = ArtifactStore(workspace / ".forge" / "artifacts")
    index = BenchmarkIndex.model_validate_json(index_path.read_bytes())
    spec = _load_model(store, index.spec_ref, A100BenchmarkSpec)
    expected_pairs = {(seed, repeat) for seed in spec.seeds for repeat in range(spec.trial_repeats)}
    trials: dict[tuple[int, int], dict[str, TrialRecord]] = defaultdict(dict)
    software_locks = set()
    for ref in index.trial_refs:
        trial = _load_model(store, ref, TrialRecord)
        key = (trial.seed, trial.repeat)
        if trial.spec_ref != index.spec_ref or key not in expected_pairs:
            raise ValueError("trial belongs to another protocol or unexpected seed/repeat")
        if trial.arm in trials[key]:
            raise ValueError("duplicate trial arm for seed/repeat")
        if (
            trial.model_revision != spec.model_revision
            or trial.dataset_digest != spec.dataset_digest
            or trial.arm_config_digest
            != digest(
                spec.baseline_config if trial.arm == "baseline" else spec.candidate_config,
                domain="forge-benchmark-arm-v1",
            )
            or trial.context_length != spec.context_length
            or trial.precision != spec.precision
            or trial.effective_batch_size != spec.effective_batch_size
            or trial.warmup_steps != spec.warmup_steps
            or trial.measured_steps != spec.measured_steps
            or trial.useful_tokens != spec.target_useful_tokens_per_trial
        ):
            raise ValueError("trial changed a frozen workload control")
        passport = _load_model(store, trial.hardware_passport_ref, dict)
        if (
            passport.get("kind") != "accelerator_preflight"
            or passport.get("status") != "READY"
            or passport.get("backend") != "cuda"
            or passport.get("device", {}).get("name") != spec.hardware_name
            or passport.get("smoke", {}).get("float32", {}).get("status") != "PASS"
            or passport.get("smoke", {}).get("bfloat16", {}).get("status") != "PASS"
        ):
            raise ValueError("trial lacks matching READY CUDA hardware passport")
        if not _load_model(store, trial.software_lock_ref, dict):
            raise ValueError("trial software lock must be a nonempty JSON object")
        software_locks.add(trial.software_lock_ref)
        trials[key][trial.arm] = trial
    if set(trials) != expected_pairs or any(
        set(pair) != {"baseline", "candidate"} for pair in trials.values()
    ):
        raise ValueError("every seed/repeat needs one baseline and one candidate trial")
    if len(software_locks) != 1:
        raise ValueError("all trials must use one frozen software lock")
    baseline_tps, candidate_tps, baseline_memory, candidate_memory = [], [], [], []
    per_arm_latencies = {"baseline": [], "candidate": []}
    for seed in spec.seeds:
        seed_tps = {"baseline": [], "candidate": []}
        seed_memory = {"baseline": [], "candidate": []}
        for repeat in range(spec.trial_repeats):
            baseline, candidate = (
                trials[seed, repeat]["baseline"],
                trials[seed, repeat]["candidate"],
            )
            if (
                baseline.hardware_passport_ref != candidate.hardware_passport_ref
                or baseline.software_lock_ref != candidate.software_lock_ref
            ):
                raise ValueError("paired arms used different hardware or software locks")
            for arm, record in (("baseline", baseline), ("candidate", candidate)):
                seed_tps[arm].append(record.useful_tokens / record.elapsed_seconds)
                seed_memory[arm].append(float(record.peak_device_memory_bytes))
                per_arm_latencies[arm].extend(record.step_latencies_ms)
        baseline_tps.append(sum(seed_tps["baseline"]) / spec.trial_repeats)
        candidate_tps.append(sum(seed_tps["candidate"]) / spec.trial_repeats)
        baseline_memory.append(sum(seed_memory["baseline"]) / spec.trial_repeats)
        candidate_memory.append(sum(seed_memory["candidate"]) / spec.trial_repeats)

    qualities: dict[tuple[int, str], QualityRecord] = {}
    expected_quality = {(seed, arm) for seed in spec.seeds for arm in ("baseline", "candidate")}
    task_ids = set(spec.heldout_task_ids)
    for ref in index.quality_refs:
        record = _load_model(store, ref, QualityRecord)
        key = (record.seed, record.arm)
        if record.spec_ref != index.spec_ref or key not in expected_quality or key in qualities:
            raise ValueError("quality record belongs to another protocol or duplicates an arm")
        if {outcome.task_id for outcome in record.outcomes} != task_ids or len(
            record.outcomes
        ) != len(task_ids):
            raise ValueError("quality record changed held-out task set")
        for outcome in record.outcomes:
            verifier = _load_model(store, outcome.verifier_report_ref, dict)
            if (
                verifier.get("task_id") != outcome.task_id
                or verifier.get("status")
                not in {"SOLVED", "TASK_FAILURE", "TIMEOUT", "MALFORMED_OUTPUT", "TAMPER_ATTEMPT"}
                or (verifier.get("status") == "SOLVED") != outcome.solved
            ):
                raise ValueError("quality outcome disagrees with verifier evidence")
        qualities[key] = record
    if set(qualities) != expected_quality:
        raise ValueError("every seed needs baseline and candidate held-out evaluation")

    throughput = paired_relative_change(baseline_tps, candidate_tps, lower_is_better=False)
    memory = paired_relative_change(baseline_memory, candidate_memory, lower_is_better=True)
    quality = _hierarchical_quality_interval(qualities, spec)
    target = judge_centerpiece_target(throughput, memory, quality)
    report = {
        "schema_version": 1,
        "kind": "a100_sft_preliminary_comparison",
        "status": "PRELIMINARY_UNAUTHENTICATED",
        "campaign_id": spec.campaign_id,
        "spec_ref": index.spec_ref,
        "trial_refs": sorted(index.trial_refs),
        "quality_refs": sorted(index.quality_refs),
        "trial_pairs": len(expected_pairs),
        "heldout_tasks": len(spec.heldout_task_ids),
        "uncertainty_method": (
            "Paired seed-level bootstrap after averaging repeats for throughput and memory; "
            "paired two-level seed-and-task bootstrap for solve-rate delta."
        ),
        "throughput_relative_change": throughput.as_dict(),
        "peak_memory_reduction": memory.as_dict(),
        "heldout_solve_rate_delta": quality.as_dict(),
        "target_bounds_check": target,
        "step_latency_ms": {
            arm: {"p50": median(values), "p95": _percentile(values, 0.95)}
            for arm, values in per_arm_latencies.items()
        },
        "claim_limit": (
            "Input reports are content-addressed and context-checked but not independently "
            "authenticated as hardware measurements. This is not release evidence until "
            "instrumented runner, raw logs, verifier, licenses, and clean-room audit pass."
        ),
    }
    report_ref = store.put(canonical_bytes(report))
    return {"report_ref": report_ref, "report": report}
