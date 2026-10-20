# FORGE - Binding Feature-First Execution Plan

Status: **LOCKED, ACTIVE, AND BINDING**  
Plan version: **2.0.0**  
Effective date: **2026-09-20**  
Owner: **one student engineer learning by building**  
Schedule model: **sixty evidence-gated slices; no fixed calendar deadline**  
Systems alpha: **after S27 and Stage 5 gate**  
Training alpha: **after S42 and Stage 8 gate**  
Feature-complete beta: **after S56 and Stage 11 gate**  
Complete V1: **after S60 and all release gates**

This plan replaces the earlier forty-day plan. That plan was faster because it omitted required parts of the frozen product. This plan retains the useful project-led rhythm but restores the complete scope: data, memory, adapters, compiler, precision, kernels, attention, communication, distributed training, reliability, SFT, DPO, GRPO, quantization, serving, Doctor, Atlas, and release proof.

A slice is an ordered capability unit, not a promised day. One focused session may complete a small slice; a hard kernel, distributed, or training slice may need several sessions. No session exists merely to read, prepare, or create GitHub activity.

## 1. Authority

The authority order is:

1. `FORGE_V1_PLAN.md` - frozen product and release contract;
2. accepted ADRs - technical semantics and compatibility decisions;
3. `FORGE_LEARNING_PATH.md` - binding student-first method;
4. this execution plan - implementation order and evidence gates;
5. `FORGE_SCOPE_TRACEABILITY.md` - source-to-evidence audit;
6. `FORGE_STATUS.md` - the single active slice;
7. tested implementation and generated reports.

When documents conflict, the higher authority wins until the conflict is corrected explicitly.

## 2. Feature-first rule

Every focused session advances runnable behavior or its acceptance evidence. A difficult slice may continue across sessions, but each session should leave at least one inspectable test, code path, experiment result, diagnosis, or generated artifact.

Every slice includes, when applicable:

1. a visible outcome through the CLI, report, benchmark, Atlas, or artifact;
2. a concrete failure or baseline observed first;
3. one focused automated test;
4. a property or numerical test when the invariant has a meaningful generated space;
5. the smallest correct implementation;
6. inspection of real output, not only a green test;
7. one student-directed change, prediction, or edge case;
8. a lab note and teach-back;
9. a focused pull request merged after tests and self-review.

Documentation, security, statistics, and profiling are attached to the feature that needs them. They are not isolated filler phases.

## 3. Completion states

- `TODO`: no accepted evidence exists.
- `ACTIVE`: the only current slice.
- `BLOCKED`: a named dependency prevents progress and a recovery action is recorded.
- `HARDWARE-UNAVAILABLE`: allowed only for a charter-defined hardware-contingent measurement, with a hardware passport proving why.
- `DONE`: behavior, tests, inspected output, student variation, teach-back, lab note, CI, and merged PR all exist.

Only one slice is active. Long accelerator jobs may run while the student documents or tests the same slice, but a second slice is not declared complete from parallel activity.

## 4. Fastest credible path without compromise

Time is reduced by removing duplication, not evidence:

- one task domain, verifier, dataset lineage system, metric schema, and evaluation harness serve every training stage;
- one declarative experiment model generates local, CUDA, and HPU launches;
- one event/report schema feeds passports, Doctor, Atlas, and release verification;
- L0 proves numerical and control-flow correctness, L1 proves pipelines, L2 produces most experiments, and L3 is reserved for final demonstrations;
- CPU work and L0/L1 tests happen before scarce accelerator reservations;
- HPU and A100 reservations are prepared as validated run matrices and executed in contiguous blocks;
- a valid run may support multiple reports when it was preregistered to collect all required metrics, but one run is never duplicated merely to fill a schedule;
- smoke, pilot, and final runs have explicit budgets and promotion gates;
- failed hypotheses become evidence and Failure Museum entries rather than repeated until they look positive;
- UI work consumes generated schemas, so charts are not rebuilt for each lab;
- exact dependency versions are frozen separately for CUDA and HPU environments after compatibility probes.

Forecasts are informational. At four to five focused sessions per week, a complete student-owned V1 is more plausibly a multi-month project than a ten-week promise. The first evidence-based calendar range is created after Stage 2, then updated at every gate. Scope and evidence never shrink to protect it.

## 5. Fixed architecture choices

| Layer | Choice |
| --- | --- |
| Core | Python 3.12 where supported; exact runtime pinned per backend lock |
| Environment | `uv` for core; reproducible CUDA and HPU lock/container manifests |
| CLI | Typer |
| Schemas | Pydantic v2 and versioned JSON/Parquet report schemas |
| Metadata | PostgreSQL, SQLAlchemy 2, Alembic |
| Artifact store | filesystem content-addressed store behind an interface |
| Training | PyTorch, Transformers, PEFT, TRL; DeepSpeed where owned by the slice |
| Quantization | bitsandbytes and/or torchao according to support contract |
| Kernels | Triton and Liger on A100; supported HPU compiled/fused/custom path |
| Serving | vLLM and the supported Gaudi plugin |
| API | FastAPI for Atlas data access |
| Web | Next.js, TypeScript, React, Tailwind, Recharts |
| Tests | pytest, Hypothesis, numerical reference tests, Playwright |
| CI | GitHub Actions for CPU checks; explicit self-hosted/manual evidence for accelerators |

An ADR is required when changing a choice affects a frozen behavior, comparison, or guarantee. CUDA and HPU do not need a forced single environment when their supported stacks conflict.

## 6. Target repository layout

```text
forge/
  cli/
  contracts/
  registry/
  artifacts/
  data/
  training/{common,sft,dpo,grpo}/
  adapters/
  distributed/
  backends/{cuda,gaudi}/
  compiler/
  kernels/
  collectives/
  profiling/
  quantization/
  inference/
  eval/
  doctor/
  failures/
  atlas/
configs/
tests/
benchmarks/
reports/
docs/{adr,learning,playbook}/
scripts/
```

A directory is created only when its owning slice gives it executable behavior.

## 7. Cross-cutting invariants

### Reproducibility

- configs, manifests, reports, and passports are schema-versioned and content-addressed;
- model and dataset names without immutable revisions are invalid for release runs;
- a run records code, environment, hardware, seed, topology, and launch command;
- resumed runs record the parent checkpoint and preserve data/RNG progress where supported;
- raw evidence is immutable; interpretations are versioned derived artifacts.

### Comparison validity

- portable comparisons hold declared controls constant;
- backend-best comparisons are labeled and never presented as hardware-only comparisons;
- warm-up, measurement window, repetitions, and aggregation are preregistered;
- OOM, compile failure, timeout, unsupported operation, and verifier failure are outcomes, not silently dropped samples;
- no best-seed reporting;
- quality and performance claims link to raw reports.

### Safety

- generated code executes only in an isolated, resource-limited verifier;
- secrets and credentials never enter configs, logs, artifacts, screenshots, or checkpoints;
- remote dataset/model licenses and redistribution rules are recorded before public release;
- experimental fault injection is restricted to owned jobs and isolated environments;
- cleanup commands target explicit run directories, never broad user or workspace roots.

### Learning ownership

- the user can locate the implementation and test for every accepted slice;
- the user predicts one result or failure before running the main experiment;
- unexplained large code drops do not satisfy a gate;
- a slice stays active until its teach-back is credible.

## 8. Required checks

Checks grow just in time:

```text
make format-check
make lint
make typecheck
make unit
make property
make integration
make numerical
make data-test
make cuda-smoke
make hpu-smoke
make distributed-smoke
make web-test
make e2e
make release-verify
```

Once introduced by a slice, a check remains mandatory unless an ADR documents a valid platform boundary. Accelerator checks must publish their hardware passport and report; a CPU-only CI badge cannot stand in for them.

## 9. Sixty executable slices

### Stage 1 - Make one measured run real

Goal: create the smallest end-to-end path from declarative config to a tested run passport and inspected artifact.

#### S01 - Project pulse

Visible outcome: `forge version` works locally and in CPU CI.

Build:

- verify Git identity and contribution attribution before the first push;
- initialize the package, Typer CLI, formatter, linter, typing, pytest, and GitHub Actions;
- start from a failing CLI smoke test;
- publish the reviewed planning baseline, then use a short-lived branch and PR for code.

Student edge case: an unknown command exits nonzero with useful help.

Gate: clean install plus CI execute `forge version`; the user can explain every introduced file.

#### S02 - Experiment identity and content-addressed artifact

Visible outcome: `forge experiment validate configs/l0_smoke.yaml` prints a stable digest and stores a verified manifest blob.

Build:

- versioned experiment schema and canonical serialization;
- model, dataset, objective, precision, parallelism, compile, profiling, and seed fields;
- streaming content-addressed artifact store with atomic publish and verified read;
- golden and property tests for order-independent mapping digests and order-sensitive lists.

Student edge case: change one meaningful field and explain why the digest changes; reorder YAML keys and explain why it does not.

Gate: manifest and artifact round-trip, corruption, and path-safety tests pass.

#### S03 - Run registry, metrics, and hardware passport

Visible outcome: `forge hardware probe` and `forge runs show RUN_ID` display real local hardware and timing data.

Build:

- PostgreSQL migrations for experiments, runs, metrics, hardware profiles, and artifacts;
- run state machine and metric event schema;
- monotonic phase timers and hardware/software probe adapters;
- minimal run passport linked to config and artifact digests.

Student edge case: simulate an interrupted run and verify it cannot be reported as successful.

Gate: migration, rollback, registry, metric-unit, and passport integration tests pass against PostgreSQL.

#### S04 - L0 workload, isolated verifier, and evaluation statistic

Visible outcome: one tiny function-repair example trains/evaluates through the common runner and isolated verifier.

Build:

- L0 model or deterministic training fixture;
- prompt, completion extraction, public tests, hidden tests, and bounded verifier result schema;
- separate task failure, malformed output, timeout, tamper attempt, and infrastructure error;
- paired solve-rate delta and bootstrap interval implementation.

Student edge case: submit an infinite loop and a forbidden import; inspect distinct results.

Gate: verifier escape tests, deterministic fixture, and statistical golden tests pass.

#### S05 - First complete run passport

Visible outcome: `forge run configs/l0_smoke.yaml` produces a passport, metrics, evaluation, and reproducible report.

Build:

- common run lifecycle from config validation through artifact publication;
- exact reproduction command and environment lock digest;
- CPU smoke plus real A100 and HPU availability probes when accessible;
- L1 promotion checklist without spending final-run budget.

Student edge case: corrupt an artifact after the run and observe verification failure.

Stage 1 gate: from a clean checkout, the user can run, inspect, reproduce, and explain one tiny measured experiment.

### Stage 2 - Build the data plane and prove packing

Goal: freeze an auditable dataset and show that layout changes hardware efficiency without changing semantics.

#### S06 - Source capture and normalization

Visible outcome: `forge data build` ingests pinned sources into normalized records with source provenance.

Build: source adapters, license metadata, normalized schema, rejected-record reasons, deterministic IDs, and raw-count report.

Tests: malformed records, Unicode, duplicate IDs, missing revisions, and deterministic rebuild.

Student edge case: add one new source record and trace it through normalization.

#### S07 - Quality filtering and near-duplicate detection

Visible outcome: the data report shows kept, rejected, and duplicate clusters with reasons.

Build: deterministic quality rules, exact hashing, MinHash/LSH candidate generation, similarity confirmation, and cluster policy.

Tests: exact duplicates, near duplicates, false-positive guard fixtures, and seed stability.

Student edge case: design two deceptively similar examples and inspect the threshold decision.

#### S08 - Decontamination and immutable splits

Visible outcome: train/preference/eval splits are frozen and an injected leak is detected.

Build: canonical fingerprints, semantic-near-match policy, grouped split assignment, hidden-eval boundary, and contamination report with five license-safe redacted examples or keyed fingerprints.

Tests: exact leak, paraphrased/structural leak fixture, group leakage, and unchanged rebuild digest.

Student edge case: inject one contaminated sample and explain its removal evidence.

#### S09 - Tokenization, length analysis, and packer correctness

Visible outcome: dataset manifest contains token counts, sequence histogram, padding projection, and packed examples.

Build: pinned tokenizer, label masking, truncation policy, length histogram, boundary-safe packing, attention/loss masks, and unpack validation.

Tests: no cross-example label leakage, token conservation, deterministic packing, long-example policy.

Student edge case: create a boundary case at exactly the maximum sequence length.

#### S10 - Data efficiency experiment

Visible outcome: a report compares naive padding, length grouping, and packing on identical examples.

Measure: real-token utilization, padding waste, tokens/s, step latency, peak memory, and held-out equivalence.

Method: L1 smoke, then L2 on the most available backend with fixed token budget and preregistered warm-up.

Student prediction: rank the three methods before the run and explain any mismatch.

Stage 2 gate: DS-001 is immutable, leak-tested, reproducible, and accompanied by a real packing study. Create the first calendar forecast from observed slice throughput.

### Stage 3 - Explain memory and choose adaptation

Goal: diagnose what consumes memory and compare interventions that target different terms.

#### S11 - Memory autopsy

Visible outcome: `forge profile RUN_ID --memory` separates estimated weights, adapters, gradients, optimizer, activations, temporary buffers, and KV cache.

Build: analytical estimates, allocator snapshots, phase peaks, reserved-versus-allocated fields, unattributed residual, and uncertainty notes.

Tests: L0 closed-form cases, monotonic shape properties, and report-sum consistency.

Student edge case: change sequence length and predict which term grows fastest.

#### S12 - Full fine-tuning versus LoRA

Visible outcome: controlled L1/L2 comparison of trainable parameters, memory, throughput, checkpoint size, time-to-loss, and held-out quality.

Build: shared adapter interface, full and LoRA configs, target-module validation, merge/export check.

Tests: trainable parameter set, frozen-base invariants, adapter save/load equivalence.

Student prediction: explain when the full baseline is useful even if it is not the selected recipe.

#### S13 - QLoRA versus LoRA

Visible outcome: A100 report shows whether weight storage was large enough for QLoRA to matter.

Build: supported 4-bit loading, compute dtype checks, adapter training, export, and quantization metadata.

Tests: base parameters stay frozen, dtype flow is explicit, reload preserves outputs within tolerance.

Student edge case: run a case where activations dominate and show why QLoRA is not the first fix.

#### S14 - Activation checkpointing

Visible outcome: no-checkpoint, checkpoint, and selective-checkpoint-if-practical comparison.

Measure: peak memory, step time, tokens/s, recompute overhead, and output/gradient agreement.

Tests: deterministic L0 gradient equivalence and saved-activation reduction.

Student prediction: identify the sequence-length region where checkpointing should become worthwhile.

#### S15 - Selected modern adapter variants

Visible outcome: rsLoRA, one of DoRA or PiSSA, and LoftQ plus QLoRA are compared with the standard baselines.

Build: a capability probe chooses DoRA or PiSSA based on support; every unsupported combination is recorded, not hidden.

Measure: memory, throughput, trainable parameters, checkpoint size, convergence, and held-out result.

Student edge case: change adapter rank and explain rsLoRA's scaling expectation.

#### S16 - Memory decision report and first Doctor rules

Visible outcome: Doctor distinguishes weights, activations, and KV/rollout memory and recommends the next discriminating experiment.

Build: deterministic rules with thresholds, evidence links, confidence labels, and `INSUFFICIENT EVIDENCE`.

Tests: synthetic passports for each dominant term plus ambiguous cases.

Stage 3 gate: the user can defend full FT, LoRA, QLoRA, checkpointing, and selected adapter tradeoffs from personal measurements.

### Stage 4 - Control compilation, shapes, and precision

Goal: understand cold compile cost, graph stability, dynamic shapes, bucketing, and supported low precision.

#### S17 - A100 eager versus `torch.compile`

Visible outcome: cold-start and steady-state comparison with graph-break and recompilation evidence.

Build: compile event schema, warm-up separation, fixed-shape benchmark, graph-break capture, and fallback labeling.

Tests: L0 numerical/gradient agreement and a deliberate graph-break fixture.

Student edge case: introduce a shape or Python control-flow break and inspect the report.

#### S18 - Gaudi dynamic-shape study

Visible outcome: variable-length HPU workload reports graph/recipe counts, compile time, and warm throughput.

Build: supported HPU compile path, metrics adapter, fixed versus variable shapes, single/multi-card compatibility probe.

Tests: report parsing and an L1 correctness comparison against the portable reference.

Student prediction: estimate how many unique shapes will compile before observing the metric.

#### S19 - Bucket optimizer and recipe-cache experiment

Visible outcome: `forge buckets recommend DS-001` emits a bounded ladder, expected waste, and expected shape classes; the recommendation is then measured.

Build: objective combining padding waste and compile count, bounded candidate search, user-visible weights, recipe-cache configuration, and baseline comparison.

Tests: brute-force agreement on small distributions, deterministic ties, no-underflow bucket coverage.

Student edge case: change the objective weights and explain the chosen ladder.

#### S20 - A100 BF16 and Gaudi BF16-versus-FP8

Visible outcome: A100 BF16 reference and a Gaudi precision report when the detected generation/stack supports FP8.

Measure: throughput, memory, compile behavior, loss curve, finite-value checks, held-out quality, and instability events.

Fallback rule: unsupported FP8 produces a signed compatibility report and no invented measurement.

Student edge case: inject an overflow/non-finite fixture into the precision monitor.

#### S21 - Compiler and precision reproduction gate

Visible outcome: clean reruns reproduce the selected bucket ladder and precision conclusion within preregistered tolerances.

Build: report comparator, cold/warm separation validator, confidence intervals across repetitions, and Doctor recompilation/numerical-instability rules.

Stage 4 gate: Forge can explain whether a change improved steady state, merely shifted startup cost, or harmed numerical behavior.

### Stage 5 - Go below the framework

Goal: implement, validate, and explain three kernels plus attention on both optimization paths.

#### S22 - Kernel benchmark and numerical harness

Visible outcome: `forge kernel check` compares a candidate against a reference across shapes and dtypes before timing it.

Build: forward/backward tolerances, finite-difference or autograd gradient checks, warm-up, synchronization, randomized shape sweep, median/tail timing, and environment metadata.

Student edge case: create a numerically wrong but fast kernel and verify release timing refuses it.

#### S23 - RMSNorm: eager, compiled, Liger, Triton

Visible outcome: a correctness and A100 latency/bandwidth report for all four paths.

Build: student-owned Triton RMSNorm, safe fallbacks, shape/dtype sweep, profiler trace.

Teach-back: explain why RMSNorm is often memory-bound and how fusion changes HBM traffic.

#### S24 - SwiGLU: eager, compiled, Liger, Triton

Visible outcome: correct forward/backward comparison with launch and bandwidth analysis.

Build: student-owned Triton path, reference tests, representative hidden sizes, and profiler evidence.

Student edge case: choose a shape that performs poorly and explain occupancy or launch effects.

#### S25 - Fused linear plus cross-entropy

Visible outcome: eager/compiled/Liger/custom path comparison with memory and numerical evidence.

Build: memory-safe reference, vocabulary/sequence shape sweep, gradient agreement, and OOM-as-result handling.

Teach-back: explain why avoiding a full logits materialization can matter.

#### S26 - Gaudi fused or custom-operation path

Visible outcome: PyTorch HPU operation, compiled HPU path, and at least one supported fused/custom operation are compared.

Build: capability probe, correctness fixture, compile/runtime metrics, and explicit custom-TPC feasibility record.

Rule: custom TPC is implemented when the detected SDK and allocation support the development flow; otherwise the required evidence is a real supported fused/custom-op study plus the compatibility boundary.

Student teach-back: explain why Triton's optimization vocabulary does not automatically transfer to HPU.

#### S27 - Attention implementation study

Visible outcome: A100 SDPA versus FlashAttention-2 and Gaudi ordinary versus supported fused SDPA across context lengths.

Measure: forward time, backward time, peak memory, tokens/s, correctness, and OOM/unsupported outcomes at 512/1024/2048/4096 where supported.

Tests: masked/causal correctness, gradient tolerances, and backend feature detection.

Stage 5 gate - systems alpha: all required kernel/attention reports pass correctness gates, and the user can explain why each winner wins or loses.

### Stage 6 - Measure communication, sharding, and scale

Goal: connect collective behavior to end-to-end training scalability.

#### S28 - Collective benchmark harness

Visible outcome: message-size sweeps for AllReduce, AllGather, and ReduceScatter produce effective-bandwidth reports.

Build: rank-safe launch, warm-up, synchronization, payload validation, topology capture, HCCL support, and NCCL when multiple A100s are available.

Tests: L0/multiprocess correctness and a mismatched-collective timeout fixture.

#### S29 - HCCL 2/4/8 topology campaign

Visible outcome: real HCCL curves for every allocated topology, with unavailable points explicitly proven.

Build: prepared run matrix, per-rank logs, topology metadata, aggregate report, and outlier handling.

Student prediction: identify the message-size region where latency versus bandwidth should dominate.

#### S30 - DDP scaling

Visible outcome: 1/2/4/8-HPU throughput, latency, memory, communication fraction, speedup, and efficiency where allocated.

Build: fixed global-work and weak-scaling modes, sampler correctness, gradient equivalence, and per-rank metric reduction.

Student edge case: deliberately misconfigure per-rank batch and make the validator catch an invalid comparison.

#### S31 - FSDP2 and ZeRO comparison

Visible outcome: single/DDP/FSDP2/ZeRO-where-appropriate comparison for fit, throughput, memory, and communication.

Build: wrap policy, mixed precision, state-dict mode, optimizer handling, and explicit unsupported paths.

Tests: L0 loss/gradient equivalence, checkpoint round-trip smoke, and parameter-sharding inspection.

#### S32 - QLoRA versus FSDP signature experiment

Visible outcome: LoRA, QLoRA, FSDP2, and supported FSDP2-plus-QLoRA are compared as compression versus distribution strategies.

Measure: memory, tokens/s, quality, communication, complexity, and failure modes.

Student teach-back: explain why two methods solve the same fit symptom through different costs.

#### S33 - Scaling Atlas and knee detection

Visible outcome: common speedup/efficiency chart automatically annotates the scaling knee and links collective evidence.

Build: knee rule, uncertainty, cost-normalized optional view, and Doctor communication-bottleneck diagnosis.

Tests: synthetic ideal, sublinear, noisy, and regressing curves.

Stage 6 gate: real collective curves and distributed runs explain where scaling stops paying off. Multi-A100 remains optional and clearly separated.

### Stage 7 - Fail, checkpoint, and recover

Goal: prove the training system handles and explains failures rather than only succeeding once.

#### S34 - Complete distributed checkpoint

Visible outcome: a checkpoint contains model, optimizer, scheduler, scaler/precision state, RNG, data progress, run metadata, and digests.

Build: atomic publication, incomplete-save marker, schema version, manifest verification, and retention policy.

Tests: component omission, corruption, interrupted write, and deterministic resume fixture.

#### S35 - Kill, restart, and topology-aware recovery

Visible outcome: a real job is killed, restarted, and verified for loss/data continuity; changed rank topology is tested where supported.

Measure: checkpoint time, recovery time, repeated/omitted samples, loss discontinuity, and final equivalence tolerance.

Student edge case: resume from an intentionally incompatible config and require a readable refusal.

#### S36 - Straggler and failure matrix

Visible outcome: controlled slow rank, killed rank, mismatched microbatch, OOM, corrupt batch, and interrupted checkpoint each produce classified evidence.

Build: isolated fault injectors, bounded timeouts, per-rank log collation, hang detector, and safe cleanup.

Rule: inject faults only into owned test jobs.

#### S37 - Reliability report and Failure Museum pack A

Visible outcome: each failure has symptom, evidence, cause, mechanism, fix, before/after, and residual limitation.

Build: Doctor rules for stragglers, checkpoint corruption, input errors, and OOM; generate entries from real reports.

Stage 7 gate: recovery is demonstrated, not described, and the user can identify which rank blocked and why.

### Stage 8 - Build the SFT and preference checkpoint chain

Goal: turn systems evidence into justified training recipes and reproducible checkpoints.

#### S38 - SFT smoke and recipe selection

Visible outcome: L1 SFT succeeds on CUDA and HPU where supported; the final recipe cites memory, packing, compiler, and scaling evidence.

Build: common trainer callbacks, metric schema, checkpoint lineage, eval hook, and promotion budget.

Tests: label masking, effective-batch calculation, resume, and small overfit fixture.

#### S39 - Final SFT

Visible outcome: selected L2/L3 SFT run produces a checkpoint, passport, ten-part recipe/model card draft, performance dashboard, and paired evaluation.

Track: loss, validation loss, tokens/s, MFU where defensible, memory, compile time, and communication.

Rule: negative or noisy quality movement is published honestly.

#### S40 - Preference data and DPO correctness

Visible outcome: deterministic chosen/rejected pairs trace to source tasks and a tiny DPO fixture moves the preferred log-ratio correctly.

Build: pair schema, tie/conflict policy, reference-model contract, beta/config validation, and contamination checks.

Student edge case: reverse a pair and predict the loss-direction change.

#### S41 - Vanilla versus fused DPO

Visible outcome: vanilla DPO and supported Liger fused linear DPO are compared for outputs, gradients, memory, throughput, and quality.

Tests: numerical equivalence across shapes/dtypes and failure on unsupported configuration.

Teach-back: explain why preference losses can create larger memory pressure than SFT.

#### S42 - Final DPO and checkpoint-chain audit

Visible outcome: base -> SFT -> DPO lineage is reproducible, evaluated, and exportable.

Build: parent-checkpoint digest enforcement, final DPO runs, paired uncertainty, and clean reload/serve smoke.

Stage 8 gate - training alpha: data through DPO is executable on the selected real backends and every checkpoint has a valid passport.

### Stage 9 - Make RLVR a measured inference system

Goal: implement safe rewards, diagnose rollout cost, reproduce reward collapse, and complete GRPO.

#### S43 - Transformers rollout baseline

Visible outcome: one prompt produces G completions, verifier rewards, timing breakdown, and KV-memory evidence.

Build: generation adapter, group schema, seed handling, prefill/decode timers, completion limits, and outcome classification.

Tests: deterministic fixture, malformed completion, timeout, and repeated-prompt accounting.

#### S44 - vLLM colocated rollout and prefix reuse

Visible outcome: Transformers versus vLLM colocated and prefix-cache off/on comparisons on one A100.

Measure: generation tokens/s, training tokens/s, prefill/decode time, VRAM, rollout wall fraction, and contention failures.

Optional: server mode only if a second A100 is briefly available; it is not a release dependency.

#### S45 - Reward verifier and anti-tamper evidence

Visible outcome: reward results separate solved, failed, malformed, timed-out, tamper, and infrastructure cases.

Build: isolated worker, allowlist, resource limits, hidden tests, tamper flags, reward schema, and audit artifact. Tampering earns negative reward; infrastructure error is neutral and excluded from the update.

Tests: filesystem, network, process, import, timeout, output spoofing, and test-discovery attacks.

#### S46 - Reward-variance collapse and recovery

Visible outcome: an intentionally easy batch yields near-zero group variance, then adjusted difficulty/sampling restores useful variance.

Measure: reward mean/variance, group composition, KL, success rate, completion length, and training-signal health.

Build: Doctor rule, alert threshold, and Failure Museum entry.

#### S47 - GRPO smoke, safeguards, and final seeds

Visible outcome: L1 smoke passes before preregistered L2/L3 runs for at least three seeds.

Build: GRPO objective tests, ratio/KL/clipping metrics, checkpoint lineage, NaN, variance-collapse, KL-blowup, and rising-tamper guardrails, plus seed aggregation.

Rule: if a preregistered safety or validity rule stops training, the honest failure report satisfies evidence, but an invalid run does not become a successful model claim.

Stage 9 gate: base -> SFT -> DPO -> GRPO is reproducible, rollout cost is quantified, and reward health is diagnosed from real groups.

### Stage 10 - Quantize and serve the result

Goal: distinguish training quantization from inference quantization and benchmark final checkpoints as services.

#### S48 - Post-training quantization

Visible outcome: BF16 and at least one supported PTQ int4/int8 path are compared on memory, latency, throughput, and quality.

Build: calibration contract where needed, export metadata, reload verification, and unsupported-op report.

Student edge case: choose a calibration subset that causes a visible regression and explain why.

#### S49 - Quantization-aware training

Visible outcome: QAT -> converted quantized model is compared with PTQ and BF16 under the same serving/eval harness.

Build: fake-quant training smoke, conversion, reload, quality/performance comparison, and distinction from QLoRA.

Tests: observer/fake-quant state transition and converted-model smoke.

#### S50 - A100 serving benchmark

Visible outcome: vLLM serves the final eligible checkpoints and emits TTFT, TPOT, p50/p95, requests/s, tokens/s, memory, and stable concurrency.

Build: open-loop/closed-loop load definitions, warm-up, request-length distribution, correctness spot checks, and saturation detection.

#### S51 - Gaudi serving benchmark

Visible outcome: supported Gaudi vLLM path serves the same portable workload on real allocated topology.

Build: plugin compatibility probe, single/multi-card launch where available, BF16 and supported quantized path, and explicit gaps.

Tests: response schema, health checks, failed-worker behavior, and metric completeness.

#### S52 - Training-optimal versus serving-optimal

Visible outcome: a decision report shows why the best training recipe may not be the best serving recipe.

Build: common cost/quality comparison, concurrency knee, quantization regression threshold, and Doctor serving rules.

Stage 10 gate: every publishable final checkpoint is loadable, evaluated, and served on A100 plus the supported Gaudi path.

### Stage 11 - Turn evidence into the product

Goal: complete Doctor, Failure Museum, Atlas, and the integrated beta without inventing data.

#### S53 - Forge Doctor complete rule set

Visible outcome: `forge doctor RUN_ID` covers every diagnosis in the frozen charter and links each conclusion to metrics; comparable run reports produce a verified Campaign frontier.

Build: rule versions, thresholds, confidence, counterevidence, next experiment, regression fixtures, `INSUFFICIENT EVIDENCE`, and registry-backed frontier construction with uncertainty and context validation.

Tests: synthetic and real passports for memory, padding, compile, communication, input, rollout, reward, quantization, serving, and numerical cases.

#### S54 - Failure Museum and empirical playbook

Visible outcome: required failures and eleven "When should I use X?" pages render from real experiments.

Build: report-to-page generator, use/don't-use claims, linked passports, negative results, limitations, and reproducibility commands.

Rule: no page is published with placeholder metrics.

#### S55 - Forge Atlas web application

Visible outcome: Overview, Runs, Data, Memory, Scaling, Kernels, Compiler, Training, Inference, Failures, and Playbook are usable.

Build: FastAPI query layer including inference, run, throughput, evaluation, scaling, Campaign frontier, and health endpoints; typed frontend client; problem-first cards; run comparison; chart provenance links; training dashboards; loading/error/empty states; and accessibility basics.

Tests: API contracts, generated-report fixtures, Playwright critical paths, and no-hardcoded-benchmark check.

#### S56 - Integrated feature-complete beta

Visible outcome: one command builds or opens the evidence-backed path:

```text
DATA -> MEMORY -> COMPILE/KERNEL/SCALE -> SFT -> DPO -> GRPO
     -> PTQ/QAT -> SERVE -> DOCTOR -> ATLAS
```

The 90-second demo path shows model-fit, communication, recompilation, DPO memory, rollout cost, checkpoint chain, quantization, and serving without manual data edits.

Stage 11 gate - feature-complete beta: all frozen features exist; an automated audit lists only hardening or release-proof gaps, not missing headline scope.

### Stage 12 - Reproduce, audit, and release

Goal: turn feature completeness into defensible public proof.

#### S57 - Final evaluation and experiment audit

Visible outcome: every mandatory experiment has a complete context record, repetitions/seeds, uncertainty, conclusion, and traceability link.

Build: release comparison validator, paired bootstrap reports, `NOT DISTINGUISHABLE FROM NOISE` enforcement, invalid-run accounting, and duplicate-evidence detection.

Gate: no result is manually transcribed into release reports.

#### S58 - Clean-room A100 and Gaudi reproduction

Visible outcome: from fresh environments, a reviewer can reproduce representative CUDA and HPU runs, the checkpoint chain, Doctor output, and Atlas data.

Build: pinned backend manifests, migrations, data/model retrieval with license checks, checkpoint/recipe publication, the charter's ten-part model card, data card, public-or-local dashboard reproduction, inference endpoint smoke, and recovery rehearsal.

Rule: secrets and provider-specific credentials are documented as inputs, never embedded.

#### S59 - Public proof package

Visible outcome: README, architecture, scope, limitations, measured claims, Failure Museum, Atlas screenshots, resume bullets, and a continuous 90-second video all point to executable evidence.

Build: final documentation links, demo rehearsal, artifact integrity check, release notes, license/SBOM/security scan, and honest hardware-availability table.

Student teach-back: explain the project in 30 seconds, defend one experiment in five minutes, and name the largest limitations.

#### S60 - Automated V1 release gate

Visible outcome:

```text
forge release verify
FORGE V1 RELEASE GATE: PASS
```

The verifier checks the sixteen charter definition-of-done clauses, all forty-six traceability rows, every mandatory experiment, required clean-room evidence, published digests, tests, licenses, and demo inputs. A missing or invalid clause returns nonzero and names the gap.

Stage 12 gate: all applicable rows pass, hardware-contingent rows carry truthful availability evidence, the release candidate is tagged, and only measured claims appear publicly.

## 10. Stage gates

| Stage | Executable gate |
| --- | --- |
| 1 | config -> run -> passport -> artifact -> reproduction works |
| 2 | DS-001 and the padding/grouping/packing study are reproducible |
| 3 | memory attribution and adapter decisions are measured and explainable |
| 4 | compile, bucketing, and precision conclusions reproduce |
| 5 | kernels and attention pass correctness before benchmark claims |
| 6 | collectives explain distributed scaling and its knee |
| 7 | failure, checkpoint, restart, and continuity evidence pass |
| 8 | base -> SFT -> DPO is reproducible and evaluated |
| 9 | GRPO, rollout, verifier, and reward-health evidence pass |
| 10 | PTQ/QAT and A100/Gaudi serving evidence pass |
| 11 | Doctor, Museum, Atlas, and integrated beta use real reports |
| 12 | clean-room, traceability, publication, and automated release gates pass |

## 11. Accelerator launch gate

Before any paid or scarce run:

- config validates and digest is recorded;
- L0 unit/numerical tests pass;
- L1 smoke passes on the target backend or a documented compatible probe;
- model and dataset revisions are cached or fetch-tested;
- expected memory and wall-time budget are written;
- warm-up, samples, seeds, metrics, and stopping rule are preregistered;
- output and checkpoint destinations are explicit;
- failure cleanup is safe;
- the experiment answers a named traceability row.

If any item fails, the accelerator job does not launch.

## 12. Progress and forecasting

At every accepted slice, update `FORGE_STATUS.md` with:

- state and visible behavior;
- failing and passing commands;
- inspected output/artifact;
- student prediction, variation, and teach-back;
- PR and merge commit;
- accelerator time and cost when applicable;
- next single slice;
- systems-alpha, training-alpha, beta, and release confidence;
- calendar range based on rolling median sessions per slice, never a fixed promise.

Expected shape, not a deadline:

- S01-S10: fast foundation and data slices;
- S11-S27: moderate experiments plus difficult kernel work;
- S28-S37: dependent on contiguous multi-HPU access;
- S38-S52: dependent on training and serving queue time;
- S53-S60: integration, hardening, clean-room, and proof.

The detailed learning guide maps the sixty slices to **120 focused build sessions**. At five substantial sessions per week, that is at least **24 calendar weeks** before hardware waits and remediation. At six to eight substantial sessions per week with timely hardware, roughly **15-20 focused weeks** may be possible. Reforecast from observed evidence after Stage 2; these are not release promises.

## 13. Scope control

No frozen capability is removed by this schedule. Optional items are only those explicitly labeled optional in the charter, such as SimPO, a second-A100 vLLM server-mode run, NCCL multi-A100 data, and custom TPC when the detected environment cannot support its development path.

If a release gate fails, add named remediation slices after S60 while retaining the failed row. Do not rewrite the plan to make the failure disappear. A change request must state the behavior, evidence, affected guarantee, compatibility impact, and whether the charter or an ADR changes.

## 14. Immediate next action

The current and only active slice is `S01 - Project pulse`. It ends only when the first code brick works locally and in CI, its focused PR is merged, contribution attribution is confirmed, and the user can explain every introduced file.
