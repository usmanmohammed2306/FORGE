# FORGE - GitHub Learning and Contribution Workflow

Status: **BINDING SESSION-BASED WORKFLOW**  
Updated: **2026-10-20**

Local Git history begins in the first implementation session; GitHub publication begins only when the user authorizes it. The uncommitted, AI-assisted planning and CPU starter code now present in this folder form the reviewed bootstrap baseline; the first student-owned code PR is part of S01. Every later green square should be the side effect of a tested, understandable product brick. Do not spread the existing starter across later dates to imply you authored it then.

Publication decision, October 20: publish the reviewed bootstrap to public `usmanmohammed2306/FORGE` directly on `main`. The owner will pursue incremental learning separately on the laptop. A single truthful bootstrap commit preserves the existing implementation's provenance; S01's independent variation, teach-back, and focused PR gate stay open. Private career records, local guidance, caches, and runtime artifacts are excluded from the public tree.

## 1. First implementation session

Before the first remote push:

1. create Forge as a standalone repository rather than a fork;
2. use `main` as the default branch;
3. confirm the local author name;
4. confirm the commit email is associated with the intended GitHub account or use the correct GitHub `noreply` address;
5. choose repository visibility and license deliberately;
6. review the existing starter, run `make test`, and commit the planning plus CPU baseline to `main` with an honest AI-assistance note as the only bootstrap exception;
7. add `origin` and push the baseline;
8. create a short-lived `learn/s01-project-pulse` branch;
9. add a new failing CLI edge case or personal variation, then make the small change yourself; `forge version` already exists in the starter;
10. open, review, and merge its PR after CI passes;
11. verify both commits appear under the correct GitHub identity.

Public visibility is preferred once the repository contains no secrets, private data, restricted artifacts, or unclear license material. Starting private is acceptable. Visibility changes remain a user decision.

## 2. Contribution cycle

For each slice:

```text
read FORGE_STATUS and previous lab note
  -> rerun previous visible proof
  -> create short-lived branch
  -> make prediction
  -> observe failure or baseline
  -> implement smallest behavior
  -> run focused and regression tests
  -> inspect real artifact or measurement
  -> complete student variation and teach-back
  -> update lab note and FORGE_STATUS
  -> commit coherent changes
  -> push branch and open focused PR
  -> CI and accelerator evidence pass
  -> self-review actual diff
  -> merge into main
  -> verify remote main and attribution
```

A branch push is useful backup but is not a published contribution until it reaches the default branch.

## 3. Branch naming

Use the stable slice ID and one purpose:

```text
learn/s01-project-pulse
feat/s09-boundary-safe-packing
exp/s19-bucket-optimizer
kernel/s23-triton-rmsnorm
dist/s35-checkpoint-recovery
fix/s45-verifier-timeout
docs/s54-qlora-playbook
```

Branches are short lived. A difficult slice may span several sessions; coherent progress commits may be pushed without pretending the slice is complete.

## 4. Commit standard

Prefer one to three meaningful commits per completed brick. Examples:

```text
test(registry): specify stable experiment digests
feat(registry): persist versioned run manifests
docs(learning): record S02 identity experiment
```

Each commit should:

- represent one coherent change;
- keep the branch runnable or clearly identify a temporary failing-test commit;
- avoid unrelated formatting churn;
- preserve correct authorship;
- exclude secrets, credentials, raw private data, `.env` files, downloaded models, datasets, checkpoints, evidence bundles, traces, provider logs, and generated dependency trees;
- use Git LFS or an external artifact release only when the publishing and license plan explicitly permits it.

Do not create:

- empty commits for a green square;
- retroactively dated commits;
- many tiny commits that artificially split one idea;
- commits containing only generated benchmark noise;
- false result files or manually edited metrics;
- code that bypasses a failing test merely to merge.

A quiet day is better than dishonest activity.

## 5. Pull request standard

Every slice PR contains:

```text
Slice ID:
Problem:
Concept learned:
Invariant or hypothesis:
Prediction:
Failure or baseline observed:
Implementation:
Tests and exact commands:
Artifact/report inspected:
Measured result:
Student variation:
Limitations and unsupported cases:
Compute used:
Lab note:
Traceability rows:
Next slice:
```

Keep the diff reviewable in one sitting. Large generated reports should be linked by digest and summarized, not dumped into the source diff.

## 6. Merge strategy

Default: **squash merge one accepted slice into `main`**.

A normal merge is allowed for a multi-session slice when preserving several coherent, passing commits materially improves the educational history. Do not force-push `main` or rewrite published release history.

An accelerator experiment PR may contain:

- code and config changes;
- a small machine-readable summary;
- links/digests to raw artifacts;
- the lab note and conclusion.

It should not contain huge checkpoints, full profiler traces, or copied model caches.

## 7. CI and hardware evidence

CPU CI covers the checks available without accelerators. Accelerator claims require separate evidence containing:

- exact commit and config digest;
- hardware passport and topology;
- backend environment lock/container digest;
- command and exit state;
- raw report/artifact digests;
- test and numerical-validity result;
- run cost/time where available.

A manual accelerator run may satisfy a slice when it is reproducible and its evidence is attached. A generic `tests passed` comment cannot.

## 8. Contribution visibility checks

If a merged commit does not appear on the contribution graph:

1. inspect its author email with `git log`;
2. confirm the email belongs to the GitHub account;
3. confirm the commit reached the default branch;
4. confirm the repository is standalone rather than a fork;
5. confirm private-contribution visibility if the repository is private;
6. allow normal GitHub processing time before treating it as broken.

Do not change author history or repository visibility without the user's explicit choice.

## 9. Sustainable rhythm

- Four to five meaningful sessions per week is a healthy part-time baseline, not a quota.
- Merge only completed bricks; push safe progress to the active branch when a slice spans sessions.
- Use one milestone per stage and one issue per slice or substantial remediation brick.
- Tag only meaningful evidence gates: `systems-alpha`, `training-alpha`, `v1.0.0-beta`, and `v1.0.0` after their gates pass.
- Reforecast at stage gates from accepted-slice throughput and hardware access.
- Never start a second slice merely to manufacture a contribution day.

## 10. GitHub planning artifacts

Recommended labels:

```text
learning, data, memory, adapter, compiler, kernel, attention,
distributed, reliability, sft, dpo, grpo, quantization,
serving, doctor, atlas, benchmark, security, release
```

Use GitHub issues, milestones, PRs, and releases only when they improve traceability. Do not create sixty empty issues before S01 unless the user finds that board useful; create or refine them stage by stage.

## 11. Portfolio quality standard

A reviewer should see:

- steady growth through small, understandable PRs;
- tests and numerical checks evolving with features;
- experiment controls and hypotheses written before expensive runs;
- real negative results and failures retained;
- raw evidence behind every chart;
- honest backend and hardware limitations;
- a clean default branch at every accepted stage gate;
- a final release produced by an automated evidence audit.

The contribution graph is a useful side effect. The reviewable engineering history is the stronger signal.
