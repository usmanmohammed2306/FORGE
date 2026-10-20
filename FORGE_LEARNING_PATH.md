# FORGE - Student-First Learning Pyramid

Status: **BINDING WORKING METHOD**  
Effective date: **2026-09-20**

Forge must produce two outcomes at the same time:

1. a complete, release-quality AI-systems product; and
2. an engineer who can explain, test, change, and defend the system.

Possessing a large generated repository is not success. The project grows through small executable bricks. Every upper layer depends on measured and understood lower-layer evidence.

## 1. Pyramid model

```text
                              RELEASE PROOF
                 clean-room, evaluation, demo, checkpoint
                                  /\
                                 /  \
                          PRODUCT JUDGMENT
                 Doctor, Failure Museum, Atlas, playbook
                              /          \
                             /            \
                     SERVING AND QUANTIZATION
                  PTQ, QAT, vLLM, TTFT, TPOT, load
                          /                  \
                         /                    \
                       POST-TRAINING AND RLVR
               SFT, DPO, GRPO, rewards, rollout systems
                    /                            \
                   /                              \
              SCALE AND RELIABILITY
       collectives, DDP/FSDP/ZeRO, checkpoints, failures
                /                                    \
               /                                      \
          SPEED AND PRECISION
     compile, buckets, FP8, kernels, attention
             /                                            \
            /                                              \
       MEMORY AND ADAPTATION
  autopsy, full FT, LoRA, QLoRA, checkpointing, variants
          /                                                    \
         /                                                      \
                    TRUSTWORTHY FOUNDATION
       config identity, passports, artifacts, data, verifier
```

We do not build a polished Atlas over unproven experiments, run expensive L3 jobs before L0/L1 correctness, or accept a benchmark before numerical validity.

## 2. Student-first execution contract

### One brick at a time

A normal implementation session advances the active slice in `FORGE_STATUS.md`, or a smaller sub-brick when the concept is substantial. The assistant must not implement several stages in one unexplained batch.

Each brick must be:

- small enough to understand in one sitting;
- runnable independently or through the current harness;
- protected by a meaningful test;
- observable through a command, report, profile, database row, or UI state;
- explicitly connected to the preceding layer;
- useful to the frozen product rather than a throwaway tutorial.

### Explain before abstraction

For every mechanism:

1. state the concrete systems problem;
2. state the invariant or hypothesis in plain language;
3. predict a result or show the smallest failure;
4. write or inspect the failing test/baseline;
5. implement the simplest correct behavior;
6. run it and inspect real evidence;
7. only then introduce a reusable abstraction;
8. explain what remains outside the claim.

Example: before wrapping memory metrics in Forge Doctor, manually estimate one L0 model's weights, gradients, optimizer state, and activations; compare that estimate with the profiler; explain the residual; then encode the rule.

### Assistant role

The assistant may:

- teach concepts and tradeoffs;
- propose the next smallest implementation step;
- pair-write focused code and tests;
- prepare a run matrix after the user understands its controls;
- diagnose failures and review diffs;
- connect evidence to or against a claim.

The assistant must:

- name every changed file and its purpose;
- explain non-obvious code paths, assumptions, and invariants;
- avoid unexplained large code generation;
- stop at the active brick's acceptance point;
- ask the user for one prediction, modification, or teach-back when it improves ownership;
- update the lab note and `FORGE_STATUS.md` with observed evidence;
- never claim a run passed unless the relevant command actually ran;
- distinguish verified results, inference, unsupported combinations, and hardware unavailability.

### Student role

For every accepted brick, the student should be able to:

- state the problem and why Forge needs it;
- explain the central invariant or experimental hypothesis;
- predict at least one failure mode;
- run the focused test and visible command;
- locate the primary implementation, test, config, and report;
- make or direct one small code/config/test variation;
- interpret the observed result without reading a scripted answer;
- explain how the next brick depends on this one.

The student need not type every line. Understanding, testing, modifying, measuring, and defending are the ownership signals.

## 3. Session build-test-learn loop

Every session, including later sessions on a hard slice, follows:

### A. Recall the base

- read the active slice in `FORGE_STATUS.md`;
- rerun the smallest command proving the previous brick;
- review the previous teach-back and unresolved limitation.

### B. Learn just enough

- define today's problem without framework jargon;
- draw or calculate the smallest useful mechanism;
- state one failure and the evidence that would expose it;
- predict the result of the planned change.

Do not spend a whole session passively studying a broad topic. Learn the concept needed for today's feature, then use it immediately.

### C. Design the smallest experiment or behavior

- identify inputs, outputs, controls, and failure states;
- name files to create or change;
- choose L0, L1, L2, or L3 intentionally;
- define the metric units and acceptance threshold;
- avoid adding components not required by the active proof.

### D. Make the baseline or failure visible

- write a failing test, trigger a controlled failure, or run the untreated baseline;
- confirm it fails or behaves for the intended reason;
- save the command and short observation in the lab note.

### E. Build the brick

- implement the minimum behavior that satisfies the invariant;
- keep the code path readable;
- comments explain why, not obvious syntax;
- do not optimize before the reference is correct.

### F. Test and inspect

- run focused tests first;
- run all currently required regression checks;
- inspect actual configs, database rows, artifacts, profiles, metrics, or UI output;
- compare the result with the prediction;
- distinguish signal, noise, and invalid measurement.

### G. Modify once

The student makes or directs one change, such as:

- add a malformed config;
- change a sequence length or adapter rank;
- introduce a graph break;
- corrupt an artifact or checkpoint;
- add a kernel shape;
- slow or kill one rank;
- reverse a preference pair;
- create a zero-variance reward group;
- increase serving concurrency past the knee.

### H. Teach back and publish

- explain the concept, evidence, and limitation;
- complete the lab note;
- update `FORGE_STATUS.md`;
- commit coherent changes;
- push the short-lived branch;
- open and self-review the focused PR;
- merge only after CI and the slice gate pass.

Suggested session rhythm:

```text
10 min  recall and rerun
20 min  concept, invariant, and prediction
20 min  failing test or untreated baseline
90 min  smallest implementation or experiment
30 min  tests, inspection, and one edge case
20 min  student modification and teach-back
20 min  lab note, PR, CI, and status
```

Time is guidance. A hard slice continues rather than being rushed or split into fake completions.

## 4. Slice definition of done

A slice is `DONE` only when all applicable items are true:

- [ ] The problem is described in plain language.
- [ ] The invariant or hypothesis is explicit.
- [ ] The user made a prediction before the main result.
- [ ] A failure or untreated baseline was observed.
- [ ] The smallest implementation passes focused tests.
- [ ] Relevant regression, numerical, and safety tests pass.
- [ ] A real output or artifact was inspected.
- [ ] Performance context and units are complete.
- [ ] Invalid, unsupported, and failed runs remain visible.
- [ ] The user can locate implementation, test, config, and report files.
- [ ] One student variation or edge case was completed.
- [ ] Three teach-back prompts were answered.
- [ ] The lab note and `FORGE_STATUS.md` were updated.
- [ ] The focused branch/PR passed CI and self-review.
- [ ] The accepted result is merged into `main`.

Working code without learning evidence remains `ACTIVE`. A good explanation without executable behavior also remains `ACTIVE`.

## 5. Layer-by-layer learning outcomes

### Layer 1 - Trustworthy foundation

Schedule: Stages 1-2.

Builds:

- versioned experiment schemas and stable digests;
- PostgreSQL registry and content-addressed artifacts;
- metric events, hardware passports, and run passports;
- isolated verifier and paired statistics;
- complete data lineage, deduplication, decontamination, and packing study.

The student learns:

- why a YAML file is not automatically a reproducible experiment;
- why artifacts need immutable identity and integrity checks;
- how units and run states prevent misleading reports;
- why data leakage invalidates later quality claims;
- how data layout changes hardware efficiency.

Gate teach-back:

1. Trace a config into its digest, database row, artifact, metrics, and passport.
2. Demonstrate an injected evaluation leak and its evidence.
3. Explain why packing can improve tokens/s without changing model math.
4. Reproduce DS-001 from pinned sources.

### Layer 2 - Memory and adaptation

Schedule: Stage 3.

Builds: memory autopsy, full FT, LoRA, QLoRA, checkpointing, selected adapter variants, and Doctor memory rules.

The student learns:

- the difference among parameter, optimizer, gradient, activation, temporary, and KV memory;
- when PEFT changes trainable state but not frozen-weight storage;
- why QLoRA helps one memory term and checkpointing another;
- why a reference full fine-tune remains useful;
- how convergence, throughput, and quality can disagree.

Gate teach-back:

1. Predict memory changes from sequence length, batch, precision, and adapter choice.
2. Defend QLoRA for one run and reject it for another.
3. Explain the throughput cost of activation checkpointing.
4. Name what the memory autopsy cannot attribute exactly.

### Layer 3 - Compiler, precision, kernels, and attention

Schedule: Stages 4-5.

Builds: eager/compile studies, HPU shape diagnosis, bucket optimizer, FP8 experiment, three Triton kernels, Liger comparisons, Gaudi fused/custom path, and attention comparisons.

The student learns:

- cold compile versus warm throughput;
- graph breaks, dynamic shapes, and recipe proliferation;
- why bucket choice trades padding for graph stability;
- numerical validation before speed claims;
- memory-bound versus compute-bound behavior;
- fusion, launch overhead, and HBM traffic;
- why accelerator optimization vocabularies differ.

Gate teach-back:

1. Cause and diagnose one graph break.
2. Derive the bucket objective and explain one selected ladder.
3. Show a fast invalid kernel and why Forge rejects it.
4. Explain why attention benefits grow with context length.
5. Explain why FP8 evidence on Gaudi does not imply A100 FP8 training evidence.

### Layer 4 - Scale and reliability

Schedule: Stages 6-7.

Builds: collectives, DDP, FSDP2/ZeRO, QLoRA-versus-FSDP, scaling knee, distributed checkpoints, fault injection, recovery, and Failure Museum entries.

The student learns:

- AllReduce, AllGather, and ReduceScatter data movement;
- strong versus weak scaling and why efficiency falls;
- communication/compute overlap;
- compression versus distribution;
- rank synchronization and straggler behavior;
- what full training state means;
- how to verify recovery instead of trusting a resumed loss line.

Gate teach-back:

1. Draw FSDP's gather/compute/reshard lifecycle.
2. Relate a collective curve to the measured training knee.
3. Identify which rank blocked in a controlled failure.
4. Prove a resumed run neither repeated nor skipped data.

### Layer 5 - Post-training and RL systems

Schedule: Stages 8-9.

Builds: SFT, preference data, DPO, fused DPO, deterministic rewards, rollout benchmarks, reward collapse/recovery, and GRPO.

The student learns:

- how systems evidence selects a training recipe;
- label masking and effective-batch correctness;
- the DPO reference/policy relationship;
- why fused loss can reduce materialization;
- why RLVR reward safety matters;
- why GRPO often becomes an inference bottleneck;
- how zero within-group variance collapses learning signal;
- why multiple seeds and stop rules matter.

Gate teach-back:

1. Trace base -> SFT -> DPO -> GRPO lineage.
2. Reverse one preference pair and explain the loss effect.
3. Separate verifier failure from a zero reward.
4. Explain the vLLM colocated memory tradeoff.
5. Diagnose one reward-collapse group from raw completions.

### Layer 6 - Quantization and serving

Schedule: Stage 10.

Builds: PTQ, QAT, conversion, A100/Gaudi vLLM, load testing, saturation, and training-versus-serving decision report.

The student learns:

- QLoRA versus PTQ versus QAT;
- calibration and quantization error;
- TTFT versus TPOT;
- throughput versus latency and concurrency;
- stable-load testing and saturation;
- why a training-optimal checkpoint or dtype may not be serving-optimal.

Gate teach-back:

1. Explain the lifecycle differences among QLoRA, PTQ, and QAT.
2. Show where latency worsens as concurrency grows.
3. Defend or reject quantized serving from quality and systems evidence.
4. Name the backend compatibility limits.

### Layer 7 - Product judgment and release proof

Schedule: Stages 11-12.

Builds: Doctor, Failure Museum, empirical playbook, Atlas, integrated beta, final statistics, clean-room reproduction, checkpoint/recipe publication, demo, and automated release gate.

The student learns:

- turning measurements into bounded recommendations;
- admitting insufficient evidence;
- linking product language to raw proof;
- schema-driven UI rather than hardcoded charts;
- reproducible public artifact design;
- claim auditing and honest negative results;
- explaining a complex system at several levels of detail.

Gate teach-back:

1. Trace one Atlas chart back to raw run evidence.
2. Defend one Doctor recommendation and its counterexample.
3. Reproduce one result from a clean checkout.
4. Explain Forge in 30 seconds and one signature experiment in five minutes.
5. State the strongest remaining limitation without minimizing it.

## 6. Learning artifacts

Each active slice creates or updates:

```text
docs/learning/SNN-short-name.md
```

Use `LEARNING_LOG_TEMPLATE.md`. Raw generated reports belong under the configured report/artifact store and are linked by digest; do not manually copy numbers into notes.

At stage gates, create a compact stage report containing:

- capabilities accepted;
- experiments and failures;
- key diagrams or profiles;
- claims supported and not supported;
- compute used;
- lessons and changed assumptions;
- next-stage risks;
- current calendar forecast range.

## 7. Boredom and difficulty rules

Boredom is a design signal when a session contains only passive reading, broad scaffolding, manual documentation, or repeated plumbing without a visible capability. Respond by shrinking the brick and making the failure or output visible sooner.

Difficulty is not a signal to skip evidence. When a concept takes longer:

1. keep the current slice active;
2. reduce the next sub-brick, model size, shape, or run duration;
3. preserve the invariant, test, inspection, and teach-back;
4. cut incidental polish and duplicate code;
5. do not replace understanding with a large generated implementation;
6. add a remediation sub-brick when the gate exposes a real gap.

## 8. Final standard

Forge succeeds only when:

- the complete product passes its release gates;
- the repository history shows small, meaningful, tested growth;
- every important claim is reproducible from artifacts;
- failed hypotheses remain visible;
- the user can answer the frozen charter's systems questions from experiments personally run.

The pyramid is complete when both the product and the student's engineering judgment are release-ready.
