#!/usr/bin/env python3
"""Compare exact PrimJS revisions with one fixed Gungraun binary harness."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from report import summarize


def run(args, **kwargs):
    subprocess.run(args, check=True, **kwargs)


def main():
    engine, output = (Path(p).resolve() for p in sys.argv[1:])
    harness = Path(__file__).resolve().parent
    base, head = os.environ['BASE_SHA'], os.environ['HEAD_SHA']
    case_filter = os.environ.get('CASE_FILTER', '')
    if not all(re.fullmatch('[0-9a-f]{40}', sha) for sha in (base, head)):
        raise ValueError('Both revisions must be full commit SHAs')
    cases = sorted(p.stem for p in (harness / 'fixtures').glob('*.js')
                   if case_filter in p.stem)
    if not cases:
        raise ValueError('Filter selected no cases')
    output.mkdir(parents=True, exist_ok=False)
    home = output / 'profiles'
    binary = output / 'qjs'
    metadata = {
        'schema_version': 1, 'repository': 'kdy1/primjs',
        'base_sha': base, 'head_sha': head, 'filter': case_filter,
        'cases': cases, 'metric': 'Ir', 'frequencies': {c: 1 for c in cases},
        'workflow_sha': os.environ['GITHUB_SHA'],
        'run_url': f"https://github.com/kdy1/primjs/actions/runs/{os.environ['GITHUB_RUN_ID']}",
        'runner': dict(zip(('sysname', 'nodename', 'release', 'version', 'machine'), os.uname())),
        'rust': subprocess.check_output(['rustc', '--version'], text=True).strip(),
        'valgrind': subprocess.check_output(['valgrind', '--version'], text=True).strip(),
        'gungraun': '0.20.0',
        'measurement': 'Whole qjs process, including startup, parsing and teardown',
        'harness_sha256': {
            str(p.relative_to(harness)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(harness.rglob('*'))
            if p.is_file() and not {'target', '__pycache__'} & set(p.relative_to(harness).parts)
        },
        'status': 'incomplete',
    }
    metadata_path = output / 'metadata.json'
    metadata_path.write_text(json.dumps(metadata, indent=2) + '\n')
    for label, sha in [('base', base), ('head', head)]:
        run(['git', '-C', str(engine), 'fetch', 'origin', sha])
        run(['git', '-C', str(engine), 'checkout', '--detach', sha])
        actual = subprocess.check_output(['git', '-C', str(engine), 'rev-parse', 'HEAD'], text=True).strip()
        if actual != sha:
            raise ValueError('Checkout did not resolve to requested SHA')
        shutil.rmtree(engine / 'out/gungraun', ignore_errors=True)
        run(['bash', str(harness / 'build.sh'), str(engine), str(binary)])
        shutil.copyfile(engine / 'out/gungraun/args.gn', output / f'{label}-args.gn')
        if label == 'head' and (output / 'base-args.gn').read_bytes() != (output / 'head-args.gn').read_bytes():
            raise ValueError('Build arguments differ')
        metadata[f'{label}_binary_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
        env = dict(os.environ, PRIMJS_QJS=str(binary))
        # Validate every selected workload outside Valgrind before measurement.
        for case in cases:
            run([str(binary), str(harness / 'fixtures' / f'{case}.js')], env=env)
            args = ['cargo', 'bench', '--locked', '--manifest-path', str(harness / 'Cargo.toml'),
                    '--bench', 'qjs', '--', f'--home={home}', '--save-summary=json',
                    '--save-baseline=base' if label == 'base' else '--baseline=base',
                    f'*{case}*']
            with (output / f'{label}-{case}.log').open('w') as log:
                run(args, env=env, stdout=log, stderr=subprocess.STDOUT)
        shutil.copytree(home, output / f'{label}-profiles')
    result = summarize(output / 'head-profiles', cases)
    (output / 'comparison.json').write_text(json.dumps(result, indent=2) + '\n')
    metadata['status'] = 'complete'
    metadata_path.write_text(json.dumps(metadata, indent=2) + '\n')
    lines = ['## Gungraun: executed instructions (Ir)', '',
             f'Base: `{base}`; head: `{head}`', '',
             '| Case | Base | Head | Change |', '| --- | ---: | ---: | ---: |']
    lines += [f"| {r['case']} | {r['base']} | {r['head']} | {r['change_percent']:+.3f}% |"
              for r in result['cases']]
    lines += ['', f"Portfolio improvement: {result['improvement_percent']:.3f}%.",
              f"Standard performance gate: **{result['gate']}**.",
              'Equal case frequencies. Whole-process counts are not wall-clock timings.',
              'Publication also requires relevant correctness checks and profile review.', '']
    report = '\n'.join(lines)
    (output / 'summary.md').write_text(report)
    with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary:
        summary.write(report)
    # A valid measurement succeeds even when the publication gate does not pass.
    print(report)


if __name__ == '__main__':
    main()
