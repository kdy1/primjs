# PrimJS Gungraun CI

## Permanent fork workflow

The repository contains `.github/workflows/gungraun.yml` and a standalone
`tools/gungraun/` Cargo package. Gungraun and its runner are pinned to 0.20.0.
The job runs only when `github.repository == 'kdy1/primjs'` and uses read-only
repository permissions. It never creates or comments on PRs.

The workflow has two triggers:

- `workflow_dispatch` compares full `base_ref` and `head_ref` commit SHAs.
  `filter` selects case IDs by literal substring; empty selects all cases.
  `workloads` accepts a JSON array of repository-relative JS paths from the
  workflow checkout. Empty uses every `tools/gungraun/fixtures/*.js` file.
  Both revisions execute these same files. Files must run directly under `qjs`
  without extra command-line arguments. Relative imports must resolve from the
  selected source file. Use deterministic inputs and assertions in each file.
  IDs are file stems with non-ASCII-alphanumeric characters replaced by `_`;
  IDs must be unique, and `filter` matches these normalized IDs.
- A push changing the harness or workflow on `kdy1/gungraun-optimize-skill` or
  `t3/gungraun/**` runs a same-SHA bootstrap check. It does not establish an
  optimization benefit. This lets the initial CI run before the workflow lands.

Manual dispatch requires the workflow on the fork's default branch. If it has
not landed, report that prerequisite. Do not create an upstream optimization PR
just to trigger benchmarks, directly push the default branch, or silently merge
infrastructure. The fork infrastructure PR is separate from optimization PRs.
See [GitHub's manual dispatch documentation](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).

## Measurement boundary

The harness launches the GN-built native `qjs` through Gungraun binary benchmarks.
Rust is only the driver. Inputs have fixed iteration counts and assert their
results. The entire process is measured, including startup, parsing and teardown.
Do not describe this as an isolated interpreter loop or a wall-clock benchmark.
See [Gungraun binary benchmarks](https://gungraun.github.io/gungraun/latest/html/benchmarks/binary_benchmarks/quickstart.html).

Both revisions use the same harness checkout, fixtures, Rust toolchain, runner,
Valgrind installation, executable path and GN arguments. The workflow builds
from each revision's own source and pinned `DEPS`. Inspect any dependency or
build configuration differences before attributing a change to production code.
The build uses release mode with symbols, Linux x64, snapshot disabled,
compatible memory management disabled, and tracing GC disabled. Do not use these
results for paths that require those features or ARM64 assembly.

The measured binary is `out/gungraun/exe.unstripped/qjs`, with DWARF debug
information verified before execution. The normal `out/gungraun/qjs` is stripped
by the Linux toolchain even when `symbol_level=2`. Profiles include all executed
engine functions, startup, and teardown; they cannot cover code the selected
workloads do not execute. Inlined functions may be attributed to their callers.
The runner uses Ubuntu 24.04: Ubuntu 22.04's Valgrind 3.18.1 cannot read the
pinned Clang toolchain's DWARF 5 information. Do not compare historical counts
from a different runner or Valgrind installation as an optimization result.

The three starter cases exercise arithmetic, object construction/property access,
and string construction/slicing. Extend them with representative cases before
optimizing another path. Freeze the new harness and run it against both unchanged
base and candidate; do not compare different workloads under one case ID.
For region-only measurements, add explicit native instrumentation in separate
benchmark plumbing and document its boundary before making such claims.

## Dispatch and identify a comparison

Resolve the workflow branch to a SHA and keep it unchanged during the experiment.
Ensure the full comparison SHAs are fetchable in the fork. Substitute actual
values in these commands; the workflow input names are part of its contract.

```sh
gh workflow run gungraun.yml --repo kdy1/primjs --ref <workflow-branch> \
  -f base_ref=<full-base-sha> -f head_ref=<full-head-sha> -f filter='<substring>'
gh run list --repo kdy1/primjs --workflow gungraun.yml \
  --event workflow_dispatch --branch <workflow-branch> \
  --json databaseId,headSha,createdAt,status,url
gh run view <run-id> --repo kdy1/primjs
gh run download <run-id> --repo kdy1/primjs --dir <evidence-directory>
```

To select custom workloads, also pass, for example:
`-f workloads='["testing/quickjs/compiler/unit_test/json_parse.js"]'`.
The paths refer to the fixed workflow checkout, not either engine checkout.

Record dispatch time, workflow SHA and run ID. Never select the latest run
without checking identity. Use bounded waits for that run. Each run has independent
concurrency so incremental and cumulative runs cannot cancel one another.

Artifacts are named `gungraun-<run-id>-<attempt>` and retained for 30 days. Save
needed evidence before expiration. Inspect:

- `metadata.json`: exact comparison SHAs, workflow SHA, tool versions, workload
  hashes, selected cases, binary hashes and `status: complete`.
- `comparison.json` and `summary.md`: exact Ir counts, percentage changes,
  equal-frequency portfolio result and standard gate verdict.
- `base-profiles/` and `head-profiles/`: Gungraun summaries and raw Callgrind
  profiles for annotation; `<revision>-<case>.log` contains runner output.
  Each current profile also has `.inclusive-no.txt` (self costs) and
  `.inclusive-yes.txt` (inclusive costs) reports covering all functions.
- `base-qjs` and `head-qjs`: exact unstripped executables for offline inspection.
  `metadata.json` records selected workload paths and SHA-256 hashes.
- `base-args.gn` and `head-args.gn`: identical release configuration.

The parser expects summary schema `7` from the pinned release. It rejects missing
baselines, zero counts, duplicate or unexpected cases, missing cases and unknown
schemas. Update and validate the parser when changing Gungraun versions. A valid
run with `gate: not_passed` remains green: this CI reports performance; the skill
controls publication. Build, fixture, harness or malformed-result errors fail CI.
Artifacts upload even after failure; incomplete evidence cannot pass the gate.

For harness changes run `cargo bench --locked --manifest-path
tools/gungraun/Cargo.toml --no-run`, the report unit tests, workflow lint, and a
fork Actions bootstrap run. Local compilation does not validate Linux Valgrind
execution. Investigate deterministic failures; retry a transient Actions failure
once and then report the blocker. Never use `pull_request_target` to execute
candidate code or add write permissions to bypass fork restrictions.
