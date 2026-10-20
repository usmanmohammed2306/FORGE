# FORGE - Complete Scope Traceability

Status: **BINDING SCOPE CROSS-CHECK**  
Source: complete forty-six-section Forge specification supplied on 2026-09-20  
Implementation authority: `FORGE_V1_PLAN.md` and `FORGE_EXECUTION_PLAN.md`

This matrix prevents the complete product from quietly shrinking into the earlier forty-day core. Every source section maps to executable slices and primary acceptance evidence. A source requirement may not be deferred by renaming it optional, polish, or V2 work unless the frozen charter explicitly classifies it as a non-goal or hardware-contingent clause.

| Source section | Planned implementation | Primary release evidence |
| --- | --- | --- |
| 1. What Forge proves | Charter Sections 1-3; S57-S60 | complete release report covering all declared systems layers |
| 2. Hardware contract | S03, S05, S18, S20, S26, S28-S33, S50-S51 | GPU/HPU passports, compatibility report, real topology evidence |
| 3. Atlas, not one benchmark | all stages; S53-S56 | lab reports with problem-hypothesis-intervention conclusions |
| 4. Model ladder | S04-S05 and promotion gates in every accelerator stage | L0/L1/L2/L3 promotion records and budget approvals |
| 5. Data Plane | S06-S09 | immutable dataset manifest and lineage report |
| 6. Data Efficiency Lab | S10 | padding/grouping/packing comparison |
| 7. Memory Autopsy | S11 and S16 | analytical versus measured memory report and attribution limits |
| 8. Adapter Lab | S12-S15 | full/LoRA/QLoRA/rsLoRA/DoRA-or-PiSSA/LoftQ matrix |
| 9. QLoRA versus FSDP | S31-S32 | compression-versus-distribution report |
| 10. Activation Memory Lab | S14 | checkpointing memory/throughput/recompute report |
| 11. Precision Lab | S20-S21 | A100 BF16 baseline and supported Gaudi BF16/FP8 report |
| 12. Quantization Lab | S13 and S48-S49 | QLoRA, PTQ, and QAT comparison with quality and serving metrics |
| 13. Compiler Lab | S17-S18 and S21 | eager/compile graph-break and steady-state report on both backends |
| 14. Bucket Optimizer | S19 | tested optimizer, selected ladder, predicted/observed waste and graph count |
| 15. Kernel Lab | S22-S25 | correctness and benchmark report for all three mandatory kernels |
| 16. Gaudi Kernel Path | S26 | supported compiled/fused/custom-operation comparison and compatibility limits |
| 17. Attention Lab | S27 | A100 SDPA/FA2 and Gaudi ordinary/fused-SDPA report |
| 18. Collective Communication | S28-S29 | HCCL AllReduce/AllGather/ReduceScatter bandwidth curves; NCCL if available |
| 19. Distributed Training | S30-S32 | single/DDP/FSDP2/ZeRO comparison |
| 20. Scaling Atlas | S29-S33 | 1/2/4/8 availability matrix, speedup, efficiency, and knee annotation |
| 21. Straggler and Failure Lab | S36-S37 | controlled failure matrix, logs, detection and recovery behavior |
| 22. Distributed Checkpoint Lab | S34-S35 | full-state kill/restart continuity and supported topology-change report |
| 23. SFT Stage | S38-S39 | selected recipe, final checkpoint, performance and evaluation report |
| 24. Preference Optimization | S40-S42 | DPO correctness, vanilla/fused comparison, final DPO checkpoint and eval |
| 25. GRPO/RLVR | S43-S47 | Transformers/vLLM rollout evidence and multi-seed GRPO report |
| 26. GRPO Reward Lab | S45-S46 | verifier security, reward-collapse reproduction and recovery |
| 27. Rollout Efficiency Lab | S43-S44 | generation baseline and prefix-cache off/on report |
| 28. Serving Lab | S50-S52 | A100 and supported Gaudi serving reports, BF16/quantized comparison |
| 29. Forge Doctor | S16, S33, S46, S52-S53 | deterministic diagnoses with linked measurements and tests |
| 30. Failure Museum | S37 and S54 | public, reproducible failure entries with symptom/cause/fix/evidence |
| 31. Forge Atlas web product | S55-S56 | working navigation and evidence-backed product pages |
| 32. Problem-first interface | S55-S56 | all eight required problem entry points linked to real runs |
| 33. When should I use X? pages | S54-S56 | eleven required playbook pages backed by comparisons |
| 34. Run Passport | S02-S03, expanded by every stage | schema validation and complete final-run passports |
| 35. Experiment registry | S02 and S57 | declarative configs, stable digests, comparable run queries |
| 36. Database and artifact model | S02-S03 | PostgreSQL migrations, content-addressed storage, digest integrity tests |
| 37. Evaluation discipline | S04, S10, S12 onward, S57 | paired deltas, bootstrap intervals, negative-result label tests |
| 38. Performance metrics | S03 and every experiment slice | machine-readable metrics with full context and validity checks |
| 39. Repository structure | created just in time by S01-S05 and owning slices | runnable packages without speculative empty directories |
| 40. Development timeline | sixty evidence-gated slices; status forecasts only | accepted-slice history and stage reports |
| 41. Mandatory final experiments | S10, S12-S14, S17-S21, S23-S35, S38-S56 | automated mandatory-experiment matrix from `forge release verify` |
| 42. Deliberate non-requirements | Charter Section 13 | limitations and non-goals report; no accidental scope expansion |
| 43. Demo | S56 and S59-S60 | continuous executable 90-second proof path |
| 44. Hiring value | S59 | public evidence package and measured resume bullets |
| 45. Intended reviewer reaction | S55-S60 | coherent README, Atlas, Failure Museum, kernels, and evidence path |
| 46. Ultimate learning objective | every lab note and stage teach-back | recorded explanations grounded in personally executed experiments |

### Approved extension beyond the source specification

| Extension | Planned implementation | Primary release evidence |
| --- | --- | --- |
| E1. Forge Campaigns multi-objective frontier | S53 and S55 | verified comparable runs, nondominated frontier, uncertainty, and source links |

## Mandatory experiment cross-check

| Required experiment | Owning slice | Release state before evidence exists |
| --- | --- | --- |
| LoRA versus QLoRA | S12-S13 | BLOCKED |
| activation checkpointing | S14 | BLOCKED |
| packing efficiency | S10 | BLOCKED |
| `torch.compile` | S17-S18 | BLOCKED |
| Gaudi bucketing | S18-S19 | BLOCKED |
| A100 Triton/Liger kernels | S22-S25 | BLOCKED |
| Gaudi fused/custom operation | S26 | BLOCKED |
| attention comparison | S27 | BLOCKED |
| Gaudi 1/2/4/8 scaling | S29-S33 | BLOCKED or HARDWARE-UNAVAILABLE with proof |
| HCCL collectives | S28-S29 | BLOCKED until real multi-HPU evidence |
| DDP versus FSDP2/ZeRO | S30-S31 | BLOCKED |
| distributed checkpoint recovery | S34-S35 | BLOCKED |
| SFT | S38-S39 | BLOCKED |
| DPO | S40-S42 | BLOCKED |
| GRPO | S43-S47 | BLOCKED |
| reward-variance failure | S46 | BLOCKED |
| vLLM rollout | S44 | BLOCKED |
| serving | S50-S52 | BLOCKED |
| PTQ/QAT | S48-S49 | BLOCKED |
| Forge Doctor | S53 | BLOCKED |
| Forge Atlas | S55-S56 | BLOCKED |
| checkpoint and recipe | S58-S60 | BLOCKED |

## Complete-project interpretation

Complete means:

- every non-contingent traceability row has executable behavior and direct evidence;
- every hardware-contingent row has either measured evidence or a truthful machine-generated availability record;
- the base-to-SFT-to-DPO-to-GRPO-to-quantize-to-serve path is reproducible;
- all required laboratories use real outputs rather than illustrative numbers;
- the Doctor and Atlas consume the same reports produced by the runners;
- the user can explain, modify, test, and defend each layer;
- the final release gate passes from a clean checkout.

It does not mean implementing the explicit non-goals in the frozen charter.

## Original PDF reconciliation

The earlier `Project5_Forge_MultiAccelerator_PostTraining.pdf` was also audited. Compatible requirements are retained; direct conflicts are resolved in favor of the newer forty-six-section Atlas specification and the user's actual hardware contract.

| Original PDF item | Frozen V1 resolution |
| --- | --- |
| Data ingest, MinHash LSH, two-signal decontamination, packing, content hash | retained in S06-S10 |
| Five removed examples shown verbatim | retained as five license-safe redacted examples or keyed fingerprints; restricted source text is not republished blindly |
| Shape buckets, warm every bucket, graph count flat after warmup | retained and strengthened in S18-S21 |
| Distributed SFT/DPO on Gaudi; GRPO on one A100 | retained in S38-S47 |
| Prefix caching, reward-variance, KL, and tamper guardrails | retained in S44-S47 |
| MFU with numerator, denominator, and LoRA caveat | retained in the measurement contract and run reports |
| Three-seed evaluation, paired bootstrap interval, tamper rate | retained in S47 and S57 |
| Published checkpoint and ten-section recipe/model card | retained in S39 and S58-S60 |
| Training dashboards, inference endpoint, run/eval/scaling viewer | expanded into the Atlas and API in S55-S56 |
| “What did not work” and honest constraints | retained in the model card, Failure Museum, and release package |
| 8/16/32/64 HPU multi-node scaling | superseded by the newer real hardware contract: 1/2/4/8 HPU when allocated; no false multi-node claim |
| No clickable UI | superseded by the newer required problem-first Atlas web product |
| Ten-day core plus optional advanced phase | superseded by sixty evidence-gated slices; the newer mandatory labs are not optional |
| Hard-coded legacy Gaudi lazy/ZeRO flags | replaced by runtime capability detection and current backend locks; historical flags are not copied without validation |
| Mandatory reuse of a separate Obligation project | the deterministic verifier contract is retained without making V1 depend on another repository; a compatible adapter may reuse prior verified code |

The superseded PDF clauses are not missing scope. They are older assumptions contradicted by the later product definition or real hardware availability.

## Release rule

Forge cannot be called V1 complete while any applicable row lacks its primary evidence. A successful one-off run, polished interface, green contribution graph, or demo video cannot substitute for a failed traceability row. Remediation slices are added until the row passes; the frozen scope is not reduced.
