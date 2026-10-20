# FORGE - Frozen Product Charter

This document defines the target V1 product. The published `0.1.0` implementation is the CPU evidence foundation described in `README.md` and `FORGE_STATUS.md`; the charter's full training, accelerator, and serving capabilities are not yet implemented or validated.

Status: **FROZEN AND LOCKED**  
Charter revision: **2.0.0 (2026-09-20 complete flagship plan)**  
Release class: **Complete Flagship V1 - not a prototype**  
Schedule model: **evidence-gated; no calendar deadline**  
Systems alpha: **after accepted Slice 27 and its gate**  
Training alpha: **after accepted Slice 42 and its gate**  
Feature-complete beta: **after accepted Slice 56 and its gate**  
V1 release: **after accepted Slice 60 and every release gate**

## 1. Product definition

Forge is an empirical AI-systems laboratory and problem-first engineering atlas. It trains, profiles, optimizes, evaluates, and serves language models across NVIDIA A100 and Intel Gaudi accelerators. It turns each run into reproducible evidence about which intervention helps a measured bottleneck, when it does not help, and why.

Public tagline:

> Don't memorize AI optimizations. Measure when they work.

One-line pitch:

> Forge takes the same language-model workloads through NVIDIA A100 and Intel Gaudi systems and empirically answers when to use LoRA, QLoRA, FSDP, activation checkpointing, quantization, fused kernels, `torch.compile`, distributed collectives, vLLM, SFT, DPO, and GRPO - and why.

Guaranteed result:

> A functioning, measured, reproducible cross-accelerator pipeline and engineering playbook. Model-quality improvement is measured, never promised.

### Complete Flagship V1 contract

V1 means the complete forty-six-section product specification supplied on 2026-09-20. It is not the earlier forty-day core plan, a collection of disconnected notebooks, or a dashboard over invented numbers. The following are release requirements and may not be deferred merely to protect a date:

- the CPU data plane, immutable lineage, quality filtering, deduplication, decontamination, tokenization, length analysis, and packing;
- the L0-L3 model ladder and a single task/evaluation contract reused across labs;
- declarative experiments, stable configuration digests, run passports, PostgreSQL metadata, and content-addressed artifacts;
- memory autopsy and evidence-backed comparisons of full fine-tuning, LoRA, QLoRA, selected adapter variants, activation checkpointing, and QLoRA versus FSDP;
- A100 and Gaudi compiler studies, dynamic-shape diagnosis, a measured bucket optimizer, recipe caching, and Gaudi BF16-versus-FP8 where the detected hardware and supported stack permit it;
- A100 eager/compiled/Liger/custom-Triton kernel studies for RMSNorm, SwiGLU, and fused linear plus cross-entropy;
- a Gaudi fused-operation or custom-operation study, with custom TPC work required only where the detected SDK and allocation make it feasible;
- A100 SDPA-versus-FlashAttention-2 and Gaudi ordinary-versus-supported-fused-SDPA studies;
- HCCL collective measurements, DDP and FSDP2/ZeRO comparisons, scaling curves, knee detection, controlled stragglers and failures, and distributed checkpoint recovery;
- end-to-end SFT, DPO, and GRPO/RLVR with deterministic verification, reward-health diagnostics, vLLM rollout measurement, and prefix-reuse measurement;
- PTQ, QAT, A100 serving, Gaudi serving, and training-optimal-versus-serving-optimal comparison;
- Forge Doctor, the Failure Museum, the problem-first Forge Atlas, and evidence-backed "When should I use X?" pages;
- Forge Campaigns: a measured multi-objective frontier over comparable run passports, showing throughput, memory, quality, and the experiment that should distinguish close choices;
- paired evaluation, uncertainty intervals, honest negative results, clean-room reproduction, a published checkpoint and recipe, and an executable final demonstration.

Nothing above can be marked complete from a mocked chart, an unverified log, a documentation-only implementation, or a single cherry-picked run.

## 2. The question Forge answers

For a declared model workload, hardware topology, and bottleneck:

1. What resource or phase is dominant?
2. Which intervention targets that dominant term?
3. What does the intervention cost in throughput, memory, quality, compile time, communication, or complexity?
4. Does the measured before/after result support the hypothesis?
5. When should an engineer use it, avoid it, or test something else first?

Every Atlas node follows:

```text
Problem
  -> Measurement
  -> Hypothesis
  -> Intervention
  -> Controlled before/after
  -> When to use it
  -> When not to use it
```

## 3. Frozen product shape

```text
                    MODERN AI SYSTEM
                          |
       +------------------+------------------+
       |                  |                  |
     MEMORY             SPEED              SCALE
       |                  |                  |
 LoRA / QLoRA       kernels / compile    DDP / FSDP
 checkpointing      packing / attention  collectives
 quantization       fusion               recovery
       |                  |                  |
       +------------------+------------------+
                          |
                    POST-TRAINING
                     SFT -> DPO -> GRPO
                          |
                       SERVING
                          |
                   DOCTOR + ATLAS
```

The labs are separate enough to isolate causes but share the same contracts, instrumentation, data lineage, and report schema. Forge is an Atlas, not one uncontrolled mega-benchmark.

## 4. Hardware and portability contract

Required success envelope:

```text
COMMON
1 x NVIDIA A100

COMMON / REALISTIC
1-8 x Intel Gaudi HPU

OPTIONAL OPPORTUNITY
2 x A100, and rarely 4 x A100 40 GB
```

Rules:

- multi-A100 is not required for release;
- the exact GPU, Gaudi SKU, memory capacity, driver, runtime, framework, firmware, topology, and library versions are detected and recorded rather than assumed;
- Gaudi 1/2/4/8 scaling is required when those topologies are actually allocated; unavailable topology points are labeled `NOT MEASURED - HARDWARE UNAVAILABLE`, never simulated or silently omitted;
- HCCL must be measured on the largest real multi-HPU topology available and on 2/4/8 HPUs whenever available;
- FP8 and custom TPC claims are gated by the detected hardware and supported software matrix;
- unsupported combinations produce an explicit compatibility artifact and do not become false performance claims;
- A100 is the primary CUDA, Triton, FlashAttention, NCCL-when-available, vLLM, and GRPO platform;
- Gaudi is the primary multi-accelerator, HCCL, HPU compiler, FP8-when-supported, fused/custom-op, distributed-training, and Gaudi-vLLM platform.

Hardware availability may change the measured topology, not the integrity of the evidence.

## 5. Workload and model contract

### Task domain

The primary end-to-end workload is small, deterministic Python function repair and generation:

- prompts describe a bounded function contract;
- outputs are extracted into an isolated verifier;
- public tests provide training signals;
- hidden tests provide evaluation and reward signals;
- time, memory, imports, filesystem, process, and network access are restricted;
- verifier tampering, malformed outputs, timeouts, and infrastructure errors are separate from task failure.

This workload supports SFT, preference pairs, verifiable rewards, repeatable quality evaluation, and an honest Failure Museum without an LLM judge in the critical path.

### Model ladder

| Level | Approximate size | Purpose |
| --- | ---: | --- |
| L0 | tiny two-layer transformer or deterministic fixture | unit, numerical, and distributed correctness |
| L1 | roughly 0.5B | pipeline and backend smoke tests |
| L2 | roughly 1.5-3B | most systems experiments |
| L3 | roughly 3-8B | final showcase runs only |

Promotion rule:

> A workload does not receive L3 accelerator budget until its contracts and failure paths pass at L0/L1 and its run plan is justified by L2 evidence.

The exact public models and revisions are selected only after license, backend support, context-length, tokenizer, and memory probes. Their revisions are then frozen in the experiment registry.

### Comparison lanes

- **portable lane:** same model revision, dataset manifest, token budget, objective, effective batch, sequence policy, and evaluation across backends;
- **backend-best lane:** best supported configuration on each backend, clearly labeled as a systems comparison rather than a hardware-only comparison;
- **diagnostic lane:** deliberately altered shapes, failures, or bottlenecks used to test Forge Doctor and the Failure Museum.

## 6. Frozen laboratory set

### Data and data efficiency

- normalization, filtering, near-duplicate detection, evaluation decontamination, tokenization, length analysis, and immutable dataset manifests;
- a decontamination report with counts and five license-safe redacted examples or keyed fingerprints showing what was removed and why;
- naive padding versus length-grouped batching versus sequence packing;
- real-token utilization, padding waste, tokens/second, step latency, peak memory, and held-out quality.

### Memory and adapters

- analytical and measured attribution for weights, adapters, gradients, optimizer state, activations, temporary buffers, and KV cache;
- full fine-tuning, LoRA, QLoRA, rsLoRA, one of DoRA or PiSSA, and LoftQ plus QLoRA;
- no checkpointing, activation checkpointing, and selective checkpointing when practical;
- QLoRA versus FSDP2, plus FSDP2 plus QLoRA if supported and scientifically interpretable.

### Compiler and precision

- eager versus `torch.compile` on A100;
- HPU compile behavior, graph breaks, recompilation, dynamic shapes, length bucketing, and recipe caching;
- A100 BF16 baseline;
- Gaudi BF16 versus FP8 when supported, including numerical stability and quality.

### Kernels and attention

- RMSNorm, SwiGLU, and fused linear plus cross-entropy;
- A100 eager versus compiled versus Liger versus a student-owned Triton implementation;
- correctness against a reference, gradient checks, shape/dtype sweeps, warm-up, and robust timing;
- Gaudi PyTorch op versus compiled/fused path and a custom operation where feasible;
- A100 SDPA versus FlashAttention-2 at 512, 1024, 2048, and 4096 tokens when the model supports those lengths;
- Gaudi ordinary attention versus the supported fused SDPA path.

### Communication, distributed training, and reliability

- AllReduce, AllGather, and ReduceScatter versus message size using HCCL and NCCL when multiple A100s are available;
- single device, DDP, FSDP2, and ZeRO where appropriate;
- throughput, step latency, memory, communication fraction, speedup, efficiency, and scaling-knee annotation;
- controlled slow rank, killed rank, mismatched microbatch, interrupted save, OOM, and corrupt batch;
- model, optimizer, scheduler, RNG, data progress, and metadata checkpointing;
- kill/restart recovery, loss-continuity verification, and changed rank topology where supported.

### Post-training and rollout

- SFT chosen from prior memory and throughput evidence;
- DPO as mandatory preference optimization, with SimPO optional;
- vanilla versus fused DPO loss implementation;
- GRPO/RLVR on A100 with deterministic verifier rewards;
- Transformers generation versus vLLM colocated generation;
- prefix caching off versus on;
- an intentionally collapsed reward-variance case followed by demonstrated signal recovery;
- live guardrails for reward-variance collapse, KL blowup, and rising verifier-tamper rate;
- at least three final GRPO seeds unless a preregistered stopping rule declares the method invalid.

### Quantization and serving

- QLoRA as training-time base-weight quantization;
- PTQ as post-training inference quantization;
- QAT followed by real quantized conversion;
- BF16 versus quantized serving on A100 and Gaudi where supported;
- TTFT, TPOT, request throughput, token throughput, p50, p95, peak memory, and maximum stable concurrency;
- training-optimal versus serving-optimal configuration comparison.

## 7. Data, experiment, and artifact contract

Every dataset manifest includes:

```text
dataset_id, source revisions, raw count, filtered count,
duplicates removed, contamination removed, token count,
length histogram, packing efficiency, tokenizer revision,
seed, git commit, schema version, and SHA-256 digest
```

Every declarative experiment produces a stable configuration digest from normalized, versioned fields. Every run receives a passport containing at least:

```text
run ID and config digest
model ID and immutable revision
dataset ID and digest
hardware inventory and topology
software/container/driver/runtime versions
objective, precision, PEFT, parallelism, compile settings
batch, sequence, seed, and token budget
throughput, timing, memory, utilization, and communication
quality result and uncertainty
artifact/checkpoint/profile/report digests
primary bottleneck and Doctor recommendation
git commit and exact reproduction command
```

Storage contract:

- PostgreSQL holds normalized metadata for datasets, experiments, runs, checkpoints, metrics, hardware profiles, kernel and collective benchmarks, evaluation results, failure cases, and recommendations;
- large artifacts live behind a content-addressed store under `.forge/` or an equivalent configured backend;
- database rows reference digests and schema versions, not mutable unnamed files;
- unit tests may use a lightweight test database, but V1 integration evidence uses PostgreSQL;
- secrets, tokens, private data, and provider credentials never enter passports, logs, artifacts, screenshots, or public reports.

## 8. Evaluation and measurement contract

### Quality

- freeze the evaluation set before final comparisons;
- report base rate, tuned rate, paired delta, and bootstrap confidence interval;
- use paired seeds or paired examples where applicable;
- separate correctness failures, verifier failures, and infrastructure failures;
- report verifier-tamper rate as a first-class outcome; a tamper attempt is negative reward while an infrastructure error is neutral and excluded from optimization;
- label exploratory analyses as exploratory;
- when the interval includes zero, display `NOT DISTINGUISHABLE FROM NOISE`;
- never select the best seed and present it as the method result.

### Performance

No performance number is valid without model, shape, dtype, hardware, software versions, batch, sequence, method, warm-up policy, sample count, and aggregation rule.

MFU, when reported, includes its FLOPs-per-token numerator, hardware peak denominator, dense-versus-sparse assumption, and adapter/full-fine-tuning caveat. A bare MFU percentage is invalid.

Required metric families:

| Area | Metrics |
| --- | --- |
| Data | packing efficiency, padding waste, real-token utilization |
| Training | tokens/s, samples/s, step time, time to target loss |
| Hardware | utilization, MFU where defensible, peak allocated/reserved memory |
| Compiler | cold compile time, warm throughput, graph breaks, compiled graph count |
| Kernel | latency, effective bandwidth, throughput where meaningful, correctness error |
| Distributed | collective time, effective bandwidth, overlap, speedup, efficiency |
| RL | rollout time, optimizer time, reward mean/variance, KL, success rate |
| Serving | TTFT, TPOT, p50/p95, requests/s, tokens/s, stable concurrency |
| Reliability | checkpoint time, recovery time, continuity error, failure detection latency |
| Quality | solve rate, loss, preference accuracy, paired delta, confidence interval |

## 9. Forge Doctor contract

Command:

```text
forge doctor RUN_ID
```

Doctor is deterministic and rule-based in V1. Every recommendation exposes the measurements, thresholds, confidence class, and next discriminating experiment. It must diagnose at least:

- weights or optimizer state dominating memory;
- activations dominating memory;
- KV cache or rollout concurrency dominating memory;
- excessive padding or poor packing;
- dynamic recompilation or graph breaks;
- communication on the critical path and a scaling knee;
- input starvation or host bottleneck;
- rollout generation dominating GRPO;
- near-zero group reward variance;
- quantization quality regression;
- serving saturation or unstable concurrency;
- numerical instability.

Doctor may say `INSUFFICIENT EVIDENCE`. It may not recommend an optimization solely because the optimization exists.

### Forge Campaigns

For runs sharing a declared comparison context, Forge shows every nondominated choice in throughput, peak memory, and held-out quality. It refuses mixed contexts, missing report digests, and invalid samples. Each point links to its source passport and uncertainty intervals. A recommendation includes the next controlled experiment that would resolve the remaining tradeoff; it does not invent an expected gain. The current CPU code implements only the tested frontier calculation. The release feature requires registry-backed, verified real run evidence and Atlas presentation.

## 10. Frozen product surfaces

### CLI

```text
forge version
forge hardware probe
forge data build CONFIG
forge experiment validate CONFIG
forge run CONFIG
forge compare RUN_ID...
forge profile RUN_ID
forge doctor RUN_ID
forge atlas build
forge reproduce RUN_ID
forge release verify
```

### Atlas

Required navigation:

- Overview
- Runs
- Data
- Memory
- Scaling
- Kernels
- Compiler
- Training
- Inference
- Failures
- Playbook

Required problem-first entry points:

- Model doesn't fit
- Training is slow
- Scaling collapses
- Compilation is slow
- RL isn't learning
- Rollouts are slow
- Inference is too expensive
- Quantization hurts quality

Required evidence-backed pages:

- LoRA
- QLoRA
- FSDP
- activation checkpointing
- FlashAttention
- `torch.compile`
- FP8
- packing
- vLLM
- prefix caching
- QAT

Every chart links to source passports and raw reports. Placeholder or manually typed benchmark values are forbidden in release mode.

### API, dashboards, and publication

- `POST /infer` serves an eligible tuned checkpoint and reports token counts;
- run, throughput, evaluation, scaling, and health endpoints support the Atlas;
- training dashboards expose loss, reward, memory, graph/recipe count, and throughput from real runs;
- the final recipe/model card contains: identity and non-goals; base revision and license; data lineage and removals; SFT/DPO/GRPO configs and commands; hardware/topology; throughput and MFU derivation; three-seed evaluation and tamper rate; what did not work; reproduction commands; boundaries and intended use.

## 11. Mandatory release experiments

| Experiment | V1 rule |
| --- | --- |
| LoRA versus QLoRA | required |
| activation checkpointing | required |
| packing efficiency | required |
| `torch.compile` study | required |
| Gaudi dynamic-shape and bucketing study | required |
| A100 Triton and Liger kernel study | required |
| Gaudi kernel or fused-operation study | required |
| attention implementation comparison | required |
| Gaudi 1/2/4/8 scaling | required when topology is allocated; availability recorded |
| HCCL collective benchmark | required on real multi-HPU allocation |
| DDP versus FSDP2/ZeRO | required |
| distributed checkpoint recovery | required |
| SFT | required |
| DPO | required |
| GRPO | required |
| reward-variance failure and recovery | required |
| vLLM rollout benchmark | required |
| serving benchmark | required on A100 and Gaudi where supported |
| PTQ and QAT | required |
| Forge Doctor | required |
| Forge Atlas | required |
| published checkpoint and recipe | required, subject to upstream licenses |

The authoritative mapping from all forty-six source sections to implementation and evidence is `FORGE_SCOPE_TRACEABILITY.md`.

## 12. Mandatory definition of done

`forge release verify` must fail closed when evidence is absent and must produce, without manual editing:

1. a valid dataset manifest and contamination report;
2. a complete run passport and retrievable content-addressed artifacts;
3. the required data-efficiency report;
4. the required memory and adapter report;
5. the compiler, bucketing, precision, kernel, and attention reports;
6. the collective, scaling, sharding, failure, and recovery reports;
7. a reproducible base-to-SFT-to-DPO-to-GRPO checkpoint chain;
8. the reward-collapse and rollout-efficiency evidence;
9. PTQ, QAT, A100 serving, and supported Gaudi serving evidence;
10. deterministic Doctor diagnoses linked to their measurements;
11. a Forge Campaign frontier, Failure Museum, and problem-first Atlas generated from real reports;
12. paired final evaluation with uncertainty and honest negative-result labels;
13. a clean-room A100 reproduction and a clean-room Gaudi reproduction;
14. a publishable checkpoint, recipe, model card, data card, limitations, and licenses;
15. public or locally reproducible dashboards, an inference endpoint, and a continuous 90-second demo path backed by the same executable artifacts;
16. a traceability report in which every applicable V1 row is `PASS` and every hardware-contingent row has truthful availability evidence.

The product is not complete if only the training scripts or Atlas UI work. The evidence path from declarative configuration to run, artifact, diagnosis, comparison, and reproduction must be executable.

## 13. Explicit non-goals

- pretraining a model from scratch;
- 70B training;
- multi-node A100 training;
- Megatron-style 3D parallelism;
- custom CUDA attention from scratch;
- a custom compiler;
- AMD hardware;
- reinventing FlashAttention;
- beating Liger or vLLM;
- inventing a new RL algorithm;
- inventing a new PEFT method;
- claiming universal accelerator comparability from non-equivalent software paths.

These are genuine non-goals. The required laboratories in Sections 6 and 11 are not optional future work.

## 14. Scope and change control

This charter is frozen. A change is permitted only when it:

1. corrects a contradiction or false technical guarantee;
2. preserves the user-visible capability through a simpler implementation;
3. responds to measured evidence or an upstream compatibility boundary;
4. adds an explicit safety or reproducibility requirement; or
5. is approved as a charter revision.

The sixty slices are ordered scope units, not promised days. Failed gates create named remediation slices and the project continues until they pass. A schedule, contribution target, hardware expense, or polished demo may never convert missing evidence into a release claim.

## 15. Current lock

- the complete forty-six-section scope remains V1;
- the sixty evidence-gated slices are the only active execution sequence;
- one tested learning brick is built at a time;
- the GitHub workflow starts with the first implementation slice;
- systems alpha, training alpha, beta, and release are evidence states rather than dates;
- only the explicit non-goals and hardware-contingent clauses may be absent from measured behavior;
- `FORGE_STATUS.md` identifies the single active slice and the next proof required.

## Final definition

> Forge is an empirical AI-systems laboratory that trains, profiles, and serves language models across NVIDIA A100 and Intel Gaudi accelerators. It diagnoses memory, compute, compiler, kernel, communication, precision, data, reliability, and rollout bottlenecks; systematically evaluates the required interventions; runs end-to-end SFT, preference optimization, and GRPO; publishes reproducible run passports and failure analyses; and turns every experiment into a problem-oriented engineering playbook explaining not merely how to use an optimization, but when and why.
