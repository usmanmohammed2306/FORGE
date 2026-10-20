# Forge: 120 build days, daily commits, and lifelong learning

Status: **working guide for the complete flagship V1**  
Updated: **2026-10-07**  
Authority: `FORGE_V1_PLAN.md` defines what must ship; `FORGE_EXECUTION_PLAN.md` defines slice gates. This guide explains how to learn and publish the work.

## 1. Read this first

The complete Forge product is a serious multi-month systems project. The 120 days below are **focused build sessions**, not a promise that the release will happen 120 calendar days from now. A hard slice can take more days. If a gate fails, insert a named remediation day and shift later numbers. Do not remove the experiment.

On 2026-10-20, the owner authorized publication of the existing bootstrap to a public repository directly on `main`, with incremental learning continuing separately on the laptop. The frozen slice gates for independent work, teach-back, and a focused learning PR remain open. Publication records the actual current snapshot without backdating or representing the reference implementation as student-written daily progress.

Use five focused sessions a week if possible. That is about 24 working weeks before hardware delays or remediation. Six to eight substantial sessions each week can compress elapsed time, but it does not reduce the required evidence. Rest days do not need a commit. A GitHub contribution square is useful only when it corresponds to real work.

The existing **AI-assisted CPU reference implementation** includes an experiment schema, stable digests, artifact store, local registry, evidence graph audit and portable CPU bundles, data-layout analysis, bucket optimizer, a tiny trainable causal transformer, a bounded L0 verifier and paired fixture comparison, early Doctor rule, statistics, tests, and a release gate that currently fails. On Day 1, review it line by line. The bootstrap publication records this reference honestly. Do not split already-written code into later commits and imply it was built on those dates. Later days should contain your own tests, changes, real experiments, and explanations.

No A100, Gaudi, SFT, DPO, GRPO, kernel, quantization, or serving result exists yet. The synthetic length fixture tests the evidence pipeline only; the tiny CPU training fixture establishes only that a toy loss decreases. `forge release verify` must continue to fail until the full measured product passes.

### The daily loop

Every build day:

1. Rerun yesterday's smallest visible command.
2. Write one prediction: what will change, and why?
3. Add a failing test or measure an untreated baseline.
4. Build one small behavior or run one controlled experiment.
5. Run focused tests and inspect the actual artifact or profile.
6. Change one case yourself: a shape, rank, example, threshold, or failure.
7. Write a five-minute lab note using `LEARNING_LOG_TEMPLATE.md`.
8. Commit and push a coherent branch. Merge a focused PR to `main` when that slice's gate passes.

If the slice takes three sessions, all three can have meaningful progress commits on the branch. Do not mark it done or merge early. GitHub documents that commit contribution attribution depends on an account-associated email and the commit reaching the default branch; check that before worrying about your graph ([GitHub profile contributions](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference)).

### Commit shape

Use a subject like `test(data): detect split leakage` or `feat(compiler): record graph recompiles`. Each commit should include a short body with the command run and observed result when that matters. A PR should link the lab note, config digest, report digest, and any accelerator passport. Never commit model weights, raw private data, access tokens, or enormous traces. Publish allowed artifacts separately and link them by digest.

### What you must explain at the end of every day

- What did this change let Forge do?
- Which test or measurement would have caught a broken version?
- What did the output actually show?
- What remains uncertain?

If you cannot answer, spend the next session on a smaller variation or explanation before building upward.

### Student-owned challenges on the starter

The new verifier, comparison, and auditor are already written, so do not reuse their implementation as a future day's personal accomplishment. Instead, use them as test subjects:

1. Run `forge verifier score configs/l0_factorial_task.json configs/l0_factorial_solution.py`. Predict the five case outcomes. Change a copy of the solution so it fails only one held-out case, then explain why the score changes.
2. Submit `while True: pass` and a forbidden import on copies of the solution. Confirm the distinct `TIMEOUT` and `TAMPER_ATTEMPT` outcomes. Add a new adversarial test of your own. The bounded interpreter is not a production security sandbox.
3. Run `forge verifier compare configs/l0_comparison.json`, then `forge verifier audit REPORT_REF` using its printed report reference. Trace each digest back to task and source blobs. Explain why a two-task improvement is still labelled `TOY_SAMPLE_ONLY`.
4. Run `forge run configs/l0_packing.json` followed by `forge runs audit`. Create a temporary test workspace, alter one passport field, and verify the auditor rejects the validly rehashed but inconsistent evidence. Do not tamper with your main `.forge` history just for the exercise.

Your Day 1 bootstrap commit should name these as AI-assisted starter features. Your later commits should contain your own hypotheses, tests, fixes, or measured runs.

## 2. The daily commit map

Each row maps one execution-plan slice to two planned build days. The first day exposes a failure or baseline; the second day builds or measures the capability and closes its gate. Hard accelerator work may take more sessions. Commit messages are suggestions, not text to paste without matching work.

| Slice | First build day: useful commit | Second build day: useful commit and gate |
| --- | --- | --- |
| S01 | **D001** Review the AI-assisted starter, choose identity/license/visibility, run tests; `docs(start): record baseline and limitations` | **D002** Make a personal CLI edge-case change, extend CPU CI if needed, self-review first PR; `test(cli): reject unknown commands` |
| S02 | **D003** Break config identity with a new invalid input; `test(identity): specify digest edge cases` | **D004** Harden canonicalization and artifact integrity; `feat(identity): verify stable manifests` |
| S03 | **D005** Inspect the local registry and specify PostgreSQL run-state transitions; `test(registry): reject invalid transitions` | **D006** Add Postgres migration and hardware passport probe; `feat(registry): persist complete passports` |
| S04 | **D007** Extend the starter verifier with your own adversarial task and explain its limits; `test(verifier): add student-owned attack case` | **D008** Attack the existing process worker, then build the containerized worker required for truly untrusted submissions; `feat(verifier): isolate untrusted submissions` |
| S05 | **D009** Audit and export the starter CPU passport, then corrupt a test bundle; `test(bundle): detect missing or altered evidence` | **D010** Extend the bounded bundle and reproduce from a clean checkout; `feat(run): prove portable L0 evidence` |
| S06 | **D011** Capture pinned raw source and malformed-record baseline; `test(data): reject unstable source records` | **D012** Normalize records with provenance and counts; `feat(data): ingest pinned sources` |
| S07 | **D013** Create exact and near-duplicate fixtures; `test(data): expose duplicate clusters` | **D014** Implement deterministic quality and MinHash/LSH filtering; `feat(data): filter near duplicates` |
| S08 | **D015** Inject evaluation leakage, including a grouped source; `test(data): detect contamination` | **D016** Freeze splits and emit removal evidence; `feat(data): publish clean splits` |
| S09 | **D017** Make a packing boundary and label-mask test fail; `test(packing): prevent cross-example loss` | **D018** Build tokenizer, masks, length histogram, and manifest; `feat(packing): emit token-safe records` |
| S10 | **D019** Record naive-padding baseline on the same examples; `exp(data): preregister layout controls` | **D020** Compare grouping and packing with real training timing; `exp(data): publish layout study` |
| S11 | **D021** Calculate L0 memory on paper and profile a mismatch; `test(memory): account for residual` | **D022** Emit analytical/measured memory autopsy; `feat(memory): explain peak allocation` |
| S12 | **D023** Train tiny full and LoRA baselines under matched controls; `exp(peft): record full and LoRA baseline` | **D024** Compare memory, speed, quality, and reload; `exp(peft): publish full-vs-LoRA` |
| S13 | **D025** Predict whether frozen weights dominate an A100 run; `exp(peft): preregister QLoRA hypothesis` | **D026** Run LoRA/QLoRA comparison and explain overhead; `exp(peft): publish quantized-adapter study` |
| S14 | **D027** Show activation memory growth and gradient reference; `test(memory): preserve checkpoint gradients` | **D028** Measure checkpointing and recompute cost; `exp(memory): publish checkpoint tradeoff` |
| S15 | **D029** Add rsLoRA rank and DoRA/PiSSA support probes; `test(peft): validate variant config` | **D030** Compare variants plus LoftQ/QLoRA on controlled workload; `exp(peft): publish adapter variants` |
| S16 | **D031** Give Doctor ambiguous memory cases; `test(doctor): refuse unsupported diagnosis` | **D032** Link weight/activation/KV recommendations to passports; `feat(doctor): diagnose memory` |
| S17 | **D033** Capture eager A100 cold and warm baselines; `exp(compiler): record eager baseline` | **D034** Measure compile path and graph breaks; `exp(compiler): compare A100 compile` |
| S18 | **D035** Run variable-shape Gaudi baseline, log recipe count; `exp(hpu): capture shape recompiles` | **D036** Explain dynamic-shape behavior from real metrics; `exp(hpu): publish compile pathology` |
| S19 | **D037** Test the current bucket optimizer against brute force and new histograms; `test(buckets): validate search objective` | **D038** Warm selected buckets and measure recipe reuse; `exp(buckets): validate recommended ladder` |
| S20 | **D039** Verify A100 BF16 and probe exact Gaudi SKU/FP8 support; `feat(precision): record capability matrix` | **D040** Run supported BF16/FP8 study with quality checks; `exp(precision): publish numeric tradeoff` |
| S21 | **D041** Rerun cold/warm compile cases from fresh caches; `test(compiler): reproduce timing protocol` | **D042** Accept or reject bucket and FP8 conclusions; `docs(compiler): publish reproducible report` |
| S22 | **D043** Make a deliberately wrong fast kernel fail the harness; `test(kernels): require correctness first` | **D044** Add gradients, timing, shape sweeps, and profiler context; `feat(kernels): build valid benchmark harness` |
| S23 | **D045** Write RMSNorm reference and student Triton forward; `test(rmsnorm): cover shapes and dtype` | **D046** Add backward and compare eager/compile/Liger/Triton; `exp(rmsnorm): publish A100 profile` |
| S24 | **D047** Write SwiGLU reference and numerical checks; `test(swiglu): verify gradients` | **D048** Compare four paths, including a losing shape; `exp(swiglu): publish kernel study` |
| S25 | **D049** Profile materialized logits and reference loss; `test(fused-ce): match reference gradients` | **D050** Add fused path comparison and OOM accounting; `exp(fused-ce): publish memory study` |
| S26 | **D051** Probe supported Gaudi fused/custom path; `test(hpu-op): document compatibility` | **D052** Run correctness and compile/runtime comparison; `exp(hpu-op): publish fused operation study` |
| S27 | **D053** Check masked/causal attention equivalence; `test(attention): verify backend outputs` | **D054** Measure A100 SDPA/FA2 and Gaudi fused SDPA; `exp(attention): publish context sweep` |
| S28 | **D055** Build rank-safe collective correctness fixtures; `test(collectives): detect mismatched calls` | **D056** Measure AllReduce/AllGather/ReduceScatter sweeps; `exp(collectives): publish bandwidth curves` |
| S29 | **D057** Prepare 2/4/8 HPU matrix and topology passports; `feat(hccl): record topology` | **D058** Run available HCCL topologies, explain missing ones; `exp(hccl): publish topology campaign` |
| S30 | **D059** Verify per-rank sampler and effective batch; `test(ddp): reject invalid scaling control` | **D060** Measure 1/2/4/8 HPU DDP where allocated; `exp(ddp): publish scaling curve` |
| S31 | **D061** Inspect FSDP2 parameter shards and ZeRO support; `test(sharding): verify state lifecycle` | **D062** Compare DDP/FSDP2/ZeRO under matched work; `exp(sharding): publish tradeoff` |
| S32 | **D063** Preregister compression-versus-distribution controls; `exp(fit): plan QLoRA-vs-FSDP` | **D064** Run and interpret fit, speed, communication, and quality; `exp(fit): publish signature study` |
| S33 | **D065** Test ideal, noisy, and regressing knee curves; `test(scaling): validate knee annotation` | **D066** Link real scaling knee to collective traces; `feat(atlas): explain scaling limit` |
| S34 | **D067** Corrupt the starter L0 checkpoint and name missing state; `test(checkpoint): reject incomplete save` | **D068** Extend full-state saving to the selected training backend and verify atomicity; `feat(checkpoint): save reproducible state` |
| S35 | **D069** Challenge the starter same-host L0 recovery proof, then kill and resume a real short run; `exp(recovery): capture restart baseline` | **D070** Verify data-cursor continuity and supported topology change; `exp(recovery): publish distributed restart proof` |
| S36 | **D071** Slow a rank and trigger bounded timeout in owned job; `test(faults): classify straggler` | **D072** Exercise kill/OOM/corrupt batch/interrupted save safely; `exp(faults): publish failure matrix` |
| S37 | **D073** Write one failure case from raw logs; `docs(failures): explain rank hang` | **D074** Connect Doctor rules to reliability cases; `feat(failures): publish museum pack` |
| S38 | **D075** Overfit a tiny SFT batch and check labels/effective batch; `test(sft): validate training contract` | **D076** Smoke SFT on selected real backends; `feat(sft): select measured recipe` |
| S39 | **D077** Preregister final SFT budget and quality test; `exp(sft): freeze final recipe` | **D078** Run final SFT and publish passport/checkpoint; `exp(sft): publish measured checkpoint` |
| S40 | **D079** Reverse a preference pair and predict DPO direction; `test(dpo): validate pair semantics` | **D080** Build preference data lineage and tiny DPO fixture; `feat(dpo): train reference-aware policy` |
| S41 | **D081** Compare vanilla/fused DPO numerical outputs; `test(dpo): verify fused gradients` | **D082** Measure memory and throughput with Liger path; `exp(dpo): publish fused-loss study` |
| S42 | **D083** Audit base→SFT→DPO parents and eval splits; `test(lineage): reject wrong parent` | **D084** Run final DPO and clean reload; `exp(dpo): publish checkpoint chain` |
| S43 | **D085** Sample G completions and classify failures; `test(rollout): preserve group identity` | **D086** Measure Transformers prefill/decode baseline; `exp(rollout): publish generation profile` |
| S44 | **D087** Test colocated vLLM memory and failure threshold; `exp(vllm): capture single-A100 baseline` | **D088** Compare vLLM and prefix cache on/off; `exp(vllm): publish rollout economics` |
| S45 | **D089** Attack verifier with timeout, import, network, and spoofed output; `test(reward): reject tampering` | **D090** Implement negative tamper/neutral infrastructure semantics; `feat(reward): produce safe audit` |
| S46 | **D091** Create equal-reward groups and inspect zero advantage; `exp(reward): reproduce collapse` | **D092** Restore variance and add Doctor guardrail; `feat(reward): diagnose recovery` |
| S47 | **D093** Smoke GRPO, check KL/NaN/tamper stop rules; `test(grpo): enforce guardrails` | **D094** Run preregistered seeds and aggregate honestly; `exp(grpo): publish final RLVR result` |
| S48 | **D095** Evaluate BF16 and PTQ load/quality baseline; `test(ptq): validate export` | **D096** Compare memory, latency, and accuracy; `exp(ptq): publish quantized inference` |
| S49 | **D097** Check fake-quant prepare/convert transition; `test(qat): verify state change` | **D098** Run QAT and converted model versus PTQ; `exp(qat): publish tradeoff` |
| S50 | **D099** Serve A100 checkpoint and test response/health; `test(serve): validate endpoint` | **D100** Sweep load and report TTFT/TPOT/p95/knee; `exp(serve): publish A100 load study` |
| S51 | **D101** Probe Gaudi plugin and compatible checkpoint; `test(hpu-serve): record support` | **D102** Measure real Gaudi load with supported topology; `exp(hpu-serve): publish HPU service report` |
| S52 | **D103** Compare selected training and serving recipes; `exp(decision): preregister cost-quality view` | **D104** Publish Pareto-style decision and Doctor saturation rule; `feat(decision): explain deployment choice` |
| S53 | **D105** Add ambiguous Doctor and mixed-context Campaign fixtures; `test(doctor): require comparable evidence` | **D106** Complete metric-linked rules and verified Pareto frontier; `feat(campaign): show measured tradeoffs` |
| S54 | **D107** Convert real failures into reusable structured cases; `feat(museum): generate evidence pages` | **D108** Write eleven measured when-to-use pages; `docs(playbook): publish empirical guide` |
| S55 | **D109** Build API from report schemas and test missing data; `test(atlas): keep chart provenance` | **D110** Build problem-first Atlas and critical UI paths; `feat(atlas): navigate measured runs` |
| S56 | **D111** Run the whole data→train→serve→Doctor path; `test(e2e): expose beta gaps` | **D112** Close feature gaps and publish beta audit; `feat(beta): demonstrate integrated Forge` |
| S57 | **D113** Recompute every final comparison from raw samples; `test(evaluation): refuse cherry-picking` | **D114** Publish paired CIs, negative results, and experiment index; `exp(evaluation): freeze claims` |
| S58 | **D115** Reproduce a representative A100 run from clean checkout; `test(reproduce): rebuild CUDA evidence` | **D116** Reproduce Gaudi path, checkpoint, recipe, and serving; `test(reproduce): rebuild HPU evidence` |
| S59 | **D117** Draft model/data cards and "what did not work"; `docs(release): publish limitations` | **D118** Produce evidence-backed README and continuous video; `docs(release): package public proof` |
| S60 | **D119** Run release verifier and fix named failures; `test(release): close evidence gaps` | **D120** Run clean final audit and tag only on PASS; `chore(release): ship Forge v1.0.0` |

### Real dates and missed days

Day numbers advance when you complete a focused build session. If you pause for exams, illness, queue wait, or a hard bug, resume the same day/slice. Do not backdate Git commits. If a planned experiment takes five days instead of two, commit distinct meaningful progress and write the actual duration in `FORGE_STATUS.md`. The eventual release date follows passed gates.

### Week endings

At the end of each five-session block, write a short weekly review as part of the fifth day's PR or lab note: what shipped, what failed, tests now required, compute spent, and what you can explain without notes. A review alone is not a substitute for that day's code or experiment.

## 3. What to learn, and how to practice it

Read **just ahead of the active slice**, not the entire stack before coding. These are primary sources. Recheck version compatibility when you reach each hardware stage, especially the Gaudi support matrix and TRL/vLLM APIs.

| Stage and days | Core learning | Read | Practice that proves understanding |
| --- | --- | --- | --- |
| 1, D001–D010 | Python packages, CLI, schemas, hashing, SQL, tests, uncertainty | [Python packaging guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/), [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/), [Typer tutorial](https://typer.tiangolo.com/tutorial/), [PostgreSQL tutorial](https://www.postgresql.org/docs/current/tutorial.html) | Change one config field, explain digest change; corrupt a stored blob; run a tiny verifier task and inspect the passport. |
| 2, D011–D020 | dataset provenance, leakage, tokenization, batching | [Hugging Face Datasets](https://huggingface.co/docs/datasets/), [Transformers data collators](https://huggingface.co/docs/transformers/main_classes/data_collator), [PyTorch data tutorial](https://docs.pytorch.org/tutorials/beginner/basics/data_tutorial.html) | Inject a near duplicate and an eval leak; compare naive/grouped/packed layouts on identical examples. |
| 3, D021–D032 | autograd memory, LoRA, QLoRA, checkpointing | [PyTorch profiler](https://docs.pytorch.org/tutorials/recipes/recipes/profiler_recipe.html), [PEFT LoRA](https://huggingface.co/docs/peft/main/conceptual_guides/lora), [PEFT quantization](https://huggingface.co/docs/peft/developer_guides/quantization) | Calculate memory by hand, then profile; double sequence length; decide whether weights or activations dominate. |
| 4, D033–D042 | graph capture, cold/warm timing, dynamic shapes, FP8 | [PyTorch compile tutorial](https://docs.pytorch.org/tutorials/intermediate/torch_compile_full_example.html), [Gaudi support matrix](https://docs.habana.ai/en/latest/PyTorch/Reference/PyTorch_Support_Matrix.html), [Gaudi dynamic shapes](https://docs.habana.ai/en/latest/PyTorch/Model_Optimization_PyTorch/Dynamic_Shapes.html) | Cause a graph break; predict recipe count; change bucket penalty and test the result on real HPU. |
| 5, D043–D054 | GPU memory hierarchy, reductions, fusion, gradients, attention | [Triton tutorials](https://triton-lang.org/main/getting-started/tutorials/), [Liger Kernel](https://github.com/linkedin/Liger-Kernel), [PyTorch SDPA](https://docs.pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html) | Write a correct reference first; make an intentionally fast wrong kernel fail; explain a slow shape from profiler data. |
| 6–7, D055–D074 | collectives, FSDP2, scaling, checkpoint semantics, distributed failures | [NCCL collectives](https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/usage/collectives.html), [FSDP2 tutorial](https://docs.pytorch.org/tutorials/intermediate/FSDP_tutorial.html), [PyTorch distributed overview](https://docs.pytorch.org/tutorials/beginner/dist_overview.html) | Draw AllGather/ReduceScatter; calculate speedup and efficiency; kill one rank and prove the restart did not skip data. |
| 8–9, D075–D094 | SFT, DPO, GRPO, verifier rewards, rollout economics | [TRL documentation](https://huggingface.co/docs/trl/index), [DPO Trainer](https://huggingface.co/docs/trl/dpo_trainer), [GRPO Trainer](https://huggingface.co/docs/trl/grpo_trainer), [vLLM integration](https://huggingface.co/docs/trl/vllm_integration) | Reverse a preference pair; produce a zero-variance reward group; explain whether rollout or optimizer dominates wall time. |
| 10, D095–D104 | PTQ, QAT, serving, latency distributions, saturation | [torchao QAT](https://docs.pytorch.org/ao/stable/workflows/qat.html), [torchao workflows](https://docs.pytorch.org/ao/stable/workflows/index.html), [vLLM docs](https://docs.vllm.ai/en/latest/) | Convert a QAT model; measure load at several concurrency levels; distinguish TTFT from TPOT. |
| 11–12, D105–D120 | diagnosis, product design, reproducibility, statistical honesty | [FastAPI tutorial](https://fastapi.tiangolo.com/tutorial/), [Playwright Python](https://playwright.dev/python/), [GitHub Actions](https://docs.github.com/en/actions), [GitHub releases](https://docs.github.com/en/repositories/releasing-projects-on-github) | Trace one Atlas chart to its raw report; reproduce a run from clean checkout; explain a negative result clearly. |

### Mathematics you should be able to derive

- **Throughput:** real, unpadded tokens divided by the measured steady-state interval.
- **Padding efficiency:** real tokens divided by processed token slots.
- **Speedup:** single-device time divided by N-device time for the same declared work.
- **Scaling efficiency:** speedup divided by N.
- **Adapter parameters:** for a linear weight of shape `out × in`, LoRA rank `r` adds approximately `r(in + out)` trainable values.
- **Attention cost:** explain why both memory traffic and attention work grow with sequence length, and where fused kernels change the memory behavior.
- **Paired quality delta:** solve-rate difference on the *same* held-out tasks, with paired resampling.
- **MFU:** achieved model FLOPs/sec divided by a declared dense hardware peak; print the FLOP convention and LoRA caveat.
- **Bucket objective:** expected padding waste plus a measured or declared penalty for each compiled shape.

Do each derivation on a tiny concrete example before using a library function. Keep the handwritten or Markdown calculation in the relevant lab note.

## 4. The centerpiece performance hypothesis

The proposed résumé target is a **preregistered experiment**, not a promised outcome or release condition:

> On a pinned 1.5B–3B SFT workload at 2,048 tokens on one A100, seek at least 15% higher real-token throughput and at least 25% lower peak device memory than a matched backend-native BF16 LoRA baseline, while keeping held-out solve rate within one percentage point.

Before spending A100 time, freeze the model revision, dataset digest, token budget, effective batch, sequence policy, optimizer, seeds, precision, warm-up, repetitions, and evaluation set. Record the baseline before tuning. Use a paired confidence interval for quality; assess the throughput and memory targets with repeated paired workloads. A point estimate alone does not prove the target. `forge.stats.judge_centerpiece_target` encodes the conservative lower-bound rule as a starting point; later slices must connect it to real run passports and preregistered reports.

If the target fails, publish the result and bottleneck diagnosis. The frozen V1 release requires the experiment and honest evidence, not a particular percentage.

## 5. Future reading after V1

Use one month per theme. Keep this as an extension track, outside the frozen V1 release gate.

| Month | Reading and code study | Small follow-up experiment |
| --- | --- | --- |
| 1 | Revisit [PyTorch profiler](https://docs.pytorch.org/tutorials/recipes/recipes/profiler_recipe.html), [FSDP2](https://docs.pytorch.org/tutorials/intermediate/FSDP_tutorial.html), and your own failure reports. | Reproduce one scaling knee with a second batch/sequence regime and explain the shift. |
| 2 | Work through the [Triton tutorial sequence](https://triton-lang.org/main/getting-started/tutorials/) and read [Liger's implementation](https://github.com/linkedin/Liger-Kernel). | Optimize one deliberately poor kernel shape while keeping correctness checks fixed. |
| 3 | Study [Gaudi dynamic shapes](https://docs.habana.ai/en/latest/PyTorch/Model_Optimization_PyTorch/Dynamic_Shapes.html) and current support matrix. | Test whether a learned compile penalty changes the bucket optimizer's chosen ladder. |
| 4 | Read current [TRL trainer docs](https://huggingface.co/docs/trl/index) and your reward-collapse traces. | Compare two valid reward shaping choices under the same task corpus and tamper checks. |
| 5 | Study [torchao QAT](https://docs.pytorch.org/ao/stable/workflows/qat.html) and [vLLM documentation](https://docs.vllm.ai/en/latest/). | Move a serving bottleneck with a second context-length/concurrency distribution. |
| 6 | Revisit your model card, Atlas, and every negative result. | Have another engineer reproduce one A100 and one Gaudi report; document every ambiguity they encounter. |

After that, choose one research direction only if the V1 evidence shows it matters: topology-aware cost optimization, better bucket search with measured compile costs, rollout scheduling, or deeper kernel fusion. A new feature is impressive when it answers a problem your measurements revealed.

## 6. Interview and self-examination plan

At the end of each stage, record a five-minute screen capture or written explanation. Use the actual run passport and raw profile, not slides alone. Answer:

1. What was the bottleneck?
2. How did you rule out the nearest alternative explanation?
3. Which optimization targeted it?
4. What did the optimization cost?
5. Did quality change beyond noise?
6. Which hardware and software versions bound the claim?
7. Can someone else reproduce it?

At final release, you should be able to open any Atlas recommendation, follow it to a passport and artifact digest, run the reproducer, and explain a counterexample where that recommendation should *not* be used. That is the learning standard behind the full Forge product.
