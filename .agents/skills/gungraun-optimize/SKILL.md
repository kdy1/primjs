---
name: gungraun-optimize
description: Profile and optimize PrimJS C/C++ code with Gungraun comparisons in kdy1/primjs GitHub Actions, then obtain human approval for each accepted optimization before publishing its draft PR to lynx-family/primjs. Use for measured PrimJS performance work or Gungraun regression investigation.
---

# Gungraun Optimize

Use profiles to select one focused optimization, measure it without an experiment
PR, and publish it only after the performance gate and correctness checks pass
and a human explicitly approves that individual upstream PR.
Creating or editing this skill does not start an optimization run.

Adapted from [swc-next's gungraun-optimize skill](https://github.com/swc-project/swc-next/tree/5e09b3300c62a8f1c120e5016b787cddbb6de423/.agents/skills/gungraun-optimize).
The PrimJS workflow uses a Rust binary benchmark harness around the native `qjs`
executable. It does not treat PrimJS as a Rust library or apply SWC AST rules.

## Keep measurement and publication separate

- Run every Gungraun Actions job in **kdy1/primjs**. Pass `--repo kdy1/primjs`
  explicitly to workflow, run, and artifact commands.
- Push task-owned experiment and publication branches only to the verified
  `kdy1/primjs` remote. Never push either repository's default branch.
- Create accepted optimization PRs in **lynx-family/primjs**, targeting its
  verified default branch (currently `develop`), with a head branch in
  **kdy1/primjs** and `draft: true`.
- Keep this repository skill and fork CI plumbing out of upstream optimization
  PRs. Start publication branches from upstream, not the fork's default branch.
- Keep one focused optimization commit, with its correctness tests, per PR.
  Do not create experiment PRs or include rejected changes.
- Obtain explicit human approval for each upstream PR, including draft PRs.
  Passing the performance gate or authorizing an optimization run does not
  authorize upstream publication. Approval for one PR does not cover another.
- After that approval, invoke the installed `$create-pr` skill for publication.
  Supply explicit repositories and draft state; never let it infer the target from `origin`.
  If that skill is unavailable, retain the measured branch and report the
  missing publication dependency.

## Inspect and establish evidence

1. Read repository instructions, the affected implementation and its callers.
   Preserve user changes. Confirm GitHub authentication, fork push access, and
   the upstream relationship with `gh repo view kdy1/primjs --json parent`.
2. Identify the requested workload and metric. Default to Callgrind `Ir`.
   For cache or allocation work, extend the harness with the appropriate
   Gungraun tool and update the report parser before interpreting those metrics.
3. Read [the CI reference](references/gungraun-ci.md). Reuse the permanent
   `.github/workflows/gungraun.yml` and `tools/gungraun/` harness. Verify that the
   chosen cases exercise the target code. The starter suite does not cover all
   engine paths, GC modes, N-API, WebAssembly, or snapshot execution.
4. Freeze the upstream starting SHA, harness SHA, selected target and related
   cases, protected cases, features, and case frequencies before editing code.
   Use documented production frequencies when available; otherwise use one per
   case and disclose it. Do not change the portfolio after seeing results to
   make a failed hypothesis pass.
5. Obtain a same-SHA CI comparison to validate the harness and collect initial
   profiles. Inspect Callgrind self and inclusive costs before choosing a
   hypothesis. Local runs can validate correctness or harness startup; only
   fork Actions results support comparative performance claims.

## Implement and measure one hypothesis

- Prefer changes to an existing shared implementation. Preserve JavaScript
  semantics, exception behavior, ownership, GC rooting, and public compatibility.
  Do not duplicate a helper solely to optimize one caller.
- Default to portable production changes. An x64 measurement is not permission
  to add intrinsics, assembly, CPU-specific flags, or architecture-gated paths.
  For an explicitly requested architecture, require a compatible Linux runner
  and a comparison that actually executes that path. Report untested targets.
- Run narrow correctness checks and the applicable repository checks before
  publication. Inspect `tools/ci/check_test_build.py` and
  `tools/ci/check_test_run.py` for the relevant modes and targets. A fixture's
  result assertion is a smoke check, not the complete engine test suite.
- Commit only the candidate and its tests on a task-owned branch. Keep temporary
  benchmark changes on a separate measurement branch or fixed harness checkout.
- Push to the fork and dispatch exact base/head SHAs. For dependent accepted
  changes, compare both against the previous accepted revision and the frozen
  starting revision. Both comparisons must pass; earlier wins cannot hide a
  harmful new change. One comparison suffices when the bases are identical.
- Match the workflow revision, run ID, artifact SHA metadata, cases and filter.
  Inspect saved summaries and raw profiles. Missing, renamed, failed or newly
  added cases are non-comparable until both sides use identical workloads.

## Apply the performance gate

For each comparison compute `score = sum(frequency * head) /
sum(frequency * base)`. Improvement is `1 - score`. Inspect every target and
related case, the weighted absolute delta, and the geometric mean as a secondary
statistic. Counts must be positive and complete.

- The standard gate requires at least **1% portfolio improvement**, with every
  individual target and related regression **below 1%**, for both incremental
  and cumulative comparisons. Correctness checks must pass.
- The bundled `comparison.json` reports this standard gate with equal case
  frequencies. A successful Actions run alone is not a passing gate.
- The reference workflow's tradeoff exception permits an isolated non-protected
  regression from 1% to below 3% only when both portfolios improve at least 5%,
  the regression is not repeated across a workload family, and profiles explain
  it. Report this as a reviewed exception; do not relabel the JSON standard gate.
- A sub-1% improvement is acceptable only when both portfolios improve, the code
  is equally simple or simpler, and no individual regression reaches 1%.
- A protected regression of at least 1%, or any regression of at least 3%, needs
  a user decision before publication. Reject a worsening incremental portfolio
  or broadly harmful regressions. Do not change thresholds to accept a result.
- Repeat a matching comparison once when results are near a threshold or profile
  evidence conflicts with the aggregate. Inconsistent repeats are inconclusive.
  Keep infrastructure failure distinct from a performance regression.

## Prepare and approve each upstream PR

Transfer only the accepted production change and correctness tests to a clean
branch based on upstream. Inspect its full upstream diff and ancestry to exclude
fork skill, harness, workflow and unrelated fork commits. Verify the production
source matches the measured source. Record measured and published SHAs. If a
rebase, conflict resolution, or different base changes production contents,
remeasure the actual publication revision before claiming the gate passed.

Before asking for approval, complete the implementation, correctness checks,
performance comparisons, and publication branch preparation described above.
Prepare the exact proposed title and body. Show the human the target repository
and base, head branch and SHA, reviewable diff, title and body, CI evidence,
performance gate outcome, correctness results, and any limitations or tradeoffs.

Ask for explicit approval to create this individual draft PR in
`lynx-family/primjs`, then wait. Do not create an upstream PR or hand publication
to `$create-pr` while approval is pending. Keep the prepared branch and evidence
available. A performance-tradeoff decision alone is not publication approval
unless the human explicitly approves this prepared PR as well.

Record the approval with the proposed PR's repository, base, head SHA and content.
Reuse that approval for the same prepared PR; do not ask again without a change.
If the implementation, target, or material PR content changes after approval,
complete any required validation and obtain approval for the revised proposal
before publication. If approval is declined, do not publish that PR.

After approval, hand `$create-pr` the following facts:

- The explicit human approval for this individual PR and the approved revision
  and content.
- Target `repository: lynx-family/primjs`, `headRepository: kdy1/primjs`, verified
  `baseBranch`, exact publication branch/SHA, absolute checkout, and `draft: true`.
- One focused optimization and its effect on the measured hot path.
- Exact base/head metrics, individual regressions, portfolio scores, protected
  cases, both comparison URLs when needed, artifact names and SHA mappings.
- Actual correctness results, coverage gaps, and metric limitations. `Ir` is
  executed instructions, not elapsed time or proof of speed on another target.
- Verified issue references when applicable and required AI assistance disclosure.
  Follow current contribution guidance for commit labels and trailers.

Publish each approved independent optimization separately. Do not silently make
later PRs include earlier unmerged changes. If a dependent PR stack is needed,
resolve its cross-fork base strategy before publishing that layer; GitHub PR
bases belong to the target repository. Register published PRs with the thread
when the host provides linking tools. Do not merge or enable auto-merge.

Continue within the user's requested scope while profile-supported hypotheses
remain. Stop for missing measurement access, inconclusive comparisons, failed
correctness, or an unresolved user tradeoff. Delete only task-owned rejected or
temporary branches after preserving evidence. Retain accepted PR branches and
the permanent fork harness. Report accepted PRs, exact metrics, run links,
correctness coverage, rejected attempts, and remaining blockers.
