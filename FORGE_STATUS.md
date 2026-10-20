# FORGE - Project Status

Last updated: **2026-10-20**  
Plan version: **2.0.0**  
Overall state: **LOCAL CPU FOUNDATION IMPLEMENTED; V1 RELEASE GATE FAILS**

Plan lock: the complete sixty-slice evidence-gated plan is the only active plan. The earlier forty-day reduced plan has been superseded and is not implementation authority.

Publication decision, October 20: the owner authorized a public repository under `usmanmohammed2306/FORGE` and direct publication to `main`. This publishes the current implementation and roadmap; it does not assert completion of the frozen V1 product. The independent learning track continues separately. Test and measurement dates below remain the dates on which they were actually observed.

Publication verified: [public repository](https://github.com/usmanmohammed2306/FORGE), branch `main`, initial commit `e1e4750a96e4511ca05c6e9898faaedc7dd7bd99`. The remote SHA and 69-file tree matched the reviewed baseline. [Hosted CPU checks passed](https://github.com/usmanmohammed2306/FORGE/actions/runs/39466548399) for that commit on October 20. Private guidance, career records, and runtime artifacts were excluded.

## Current milestone

- Stage: 1 - Make one measured run real
- Active slice: `S01 - Project pulse`
- Slice state: `ACTIVE` - public bootstrap and CPU CI exist; independent student variation, teach-back, and focused learning PR remain
- Stage 1 gate: `OPEN` - complete the isolated L0 verifier and clean-checkout reproduction; the tiny CPU model is implemented

## Current implementation evidence

- installable Python package, Typer CLI, Pydantic experiment contract, domain-separated configuration digest;
- content-addressed artifact store with verified read and corruption tests;
- local SQLite development registry and run passport; PostgreSQL migration remains to be built;
- analytical CPU length-layout comparison for naive padding, grouping, and first-fit packing;
- tiny real CPU causal-transformer optimization with a content-addressed checkpoint and loss trace;
- full-state L0 optimizer/RNG checkpoints and a same-host interrupted/resumed proof with byte-identical final weights and loss trace;
- run-evidence graph auditor that checks config/report/passport/checkpoint links and detects tampering even when a replacement artifact has a valid digest;
- bounded L0 function-repair AST interpreter executed in a short-lived process, with wall-clock and CPU limits and distinct malformed, tamper, wrong-answer, timeout, and infrastructure outcomes;
- paired two-task verifier campaign with evidence-linked reports, a `TOY_SAMPLE_ONLY` statistical verdict, and a replay auditor that rejects fabricated scores or aggregate results;
- deterministic, bounded CPU evidence bundles with safe archive verification and idempotent clean-workspace import;
- small deterministic data-lineage fixture with exact/near duplicate and evaluation-overlap checks;
- indexed exact-pair/shared-shingle candidate search for the CPU data-lineage fixture, with randomized equivalence tests against pairwise Jaccard and a three-distribution paired synthetic microbenchmark;
- exact bounded bucket optimizer and an evidence-limited Doctor padding rule;
- paired bootstrap statistics and conservative centerpiece target checker;
- tested Pareto-frontier core for comparable throughput/memory/quality campaign points; real run integration remains;
- truthful local hardware probe, source-digest-checked CLI reproduction, CPU CI workflow, and tests;
- content-addressed CUDA/HPU preflight reports with observed device identity and small FP32/BF16 matmul smoke when devices are present;
- preregistered A100 BF16 SFT comparison schema and an evidence-linked paired analyzer that rejects mixed controls, unmatched hardware/software, incomplete pairs, and verifier infrastructure failures; all results remain explicitly `PRELIMINARY_UNAUTHENTICATED`;
- fail-closed release inventory that names missing evidence and does not claim V1 completion.

These are starter components. No accelerator training or held-out model-quality gain has been measured. The local layout run used synthetic sequence lengths and reported token-count utilization only. The tiny CPU training run demonstrated a falling loss on a toy corpus and saved a checkpoint; it does not establish language-model capability. Verifier fixture cases are public in the repository, and the bounded interpreter is not a sandbox for arbitrary Python.

## Completed planning evidence

- complete flagship V1 charter frozen;
- all forty-six source sections mapped in scope traceability;
- sixty feature-first slices defined;
- student learning pyramid defined;
- GitHub workflow begins with the first implementation session;
- 120-build-day learning and daily commit guide with primary resources;
- systems-alpha, training-alpha, beta, and release gates defined.

## Existing authority files

- `FORGE_V1_PLAN.md`
- `FORGE_EXECUTION_PLAN.md`
- `FORGE_SCOPE_TRACEABILITY.md`
- `FORGE_LEARNING_PATH.md`
- `FORGE_GITHUB_WORKFLOW.md`
- `LEARNING_LOG_TEMPLATE.md`
- `FORGE_DAILY_LEARNING_AND_GITHUB.md`
- `README.md`

## Required next work

Complete `S01 - Project pulse`:

1. publish the reviewed implementation to public `main` as authorized, excluding private guidance, career records, and local artifacts;
2. associate the initial commit with the verified owner using GitHub's privacy-preserving noreply email;
3. review the AI-assisted starter code and its recorded checks; the public baseline does not establish an independent student implementation;
4. create `learn/s01-project-pulse`;
5. make one small student-owned variation or new edge-case test;
6. run `make test`, `forge version`, `forge hardware-probe`, and the config smoke test;
7. inspect the existing CPU run passport and explain its claim limit;
8. verify an unknown command fails usefully;
9. complete the lab note and teach-back;
10. self-review the local diff; the independent learning exercise and its focused PR remain pending after the bootstrap publication;
11. confirm contribution attribution on remote `main` after that publication.

## Test status

The last local suite passed 77 tests plus lint and format checks on October 10; it has not been rerun for the October 20 documentation/publication work. The tiny CPU trainer and `forge reproduce` produced an exact report and checkpoint match on this host. The L0 save/resume proof produced byte-identical final checkpoints and loss traces. A CPU run bundle round-tripped into a clean test workspace and reproduced there. Local CUDA and HPU preflights both reported `UNAVAILABLE`, consistent with the Mac host; no remote hardware test has run. The A100 comparison tests use synthetic test-only fixtures and establish analyzer rejection behavior, not performance. The October 10 CPU data-lineage microbenchmark used three synthetic 6,000-row distributions and five paired timings each: indexed/pairwise median paired speedups were 52.85× for disjoint prompts, 1.08× for shared-shingle prompts, and 4.85× for duplicate-heavy prompts. This is not SFT or accelerator performance; see `benchmarks/results/data_lineage_cpu_2026-10-10.json` for raw timings and limits. The publication snapshot is prepared for `main`; remote publication and hosted CI are recorded separately after verification. Accelerator tests have not run. `forge release verify` last failed closed on 25 missing evidence categories.

## Blockers

No blocker for local S01 review. Forge-specific accelerator allocation, connection method, exact SKUs/counts, and job-time budget are still needed before executing hardware runs. Full release also requires model/dataset licenses and the remaining feature slices.

## Decisions required during S01

- GitHub destination authorized on October 20: public `usmanmohammed2306/FORGE`, default branch `main`;
- project license remains undecided; the public source currently grants no separate open-source license;
- Git author identity is associated with the verified GitHub owner through its noreply address;
- accelerator environment versions after the actual hardware inventory is known; CPU development constraints are pinned in `constraints/dev.txt`.

The owner authorized direct publication of the bootstrap to `main`. The independent S01 variation, explain-back, and focused learning PR remain separate acceptance evidence; publication alone does not mark the slice `DONE`.

## Schedule confidence

- Calendar deadline: none
- Initial part-time range: at least 24 focused weeks for the 120-day guide, plus hardware waits and remediation
- Aggressive range: about 15-20 focused weeks at 6-8 substantial sessions/week with timely hardware
- First evidence-based reforecast: after Stage 2
- Systems alpha: after accepted S27 and Stage 5 gate
- Training alpha: after accepted S42 and Stage 8 gate
- Feature-complete beta: after accepted S56 and Stage 11 gate
- Complete V1: after accepted S60 and all release gates

Ranges are forecasts, not reasons to cut scope or skip evidence.

## Pace evidence

- Focused student implementation sessions completed: 0
- Accepted slices: 0 / 60
- Rolling median sessions per accepted slice: unavailable
- A100 hours used: 0
- Gaudi HPU-hours used: 0
- Current forecast confidence: low until Stage 2
- Local host inventory: macOS arm64, Python 3.12.14, PyTorch installed for optional L0 smoke, no detected CUDA/HPU; remote A100/Gaudi access reported but not yet connected

## Locked decision

- Complete V1 contains all forty-six source sections except explicit charter non-goals.
- Hardware-contingent claims require real availability evidence, not simulation.
- The sixty slices define order and acceptance, not elapsed days.
- Only one slice is active at a time.
- Failed gates create remediation work; they do not shrink the charter.
- The only current slice is S01.
