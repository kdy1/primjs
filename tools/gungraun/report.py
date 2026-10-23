"""Read the pinned Gungraun 0.20 summary schema. Reject incomplete comparisons."""
import json
import math


def summarize(root, expected):
    rows = {}
    for path in root.rglob('summary.json'):
        summary = json.loads(path.read_text())
        if summary['version'] != '7':
            raise ValueError(f'Unsupported summary version in {path}')
        case = summary['id']
        if case not in expected or case in rows:
            raise ValueError(f'Unexpected or duplicate case: {case}')
        profiles = [p for p in summary['profiles'] if p['tool'].lower() == 'callgrind']
        if len(profiles) != 1:
            raise ValueError(f'Expected one Callgrind profile for {case}')
        values = profiles[0]['data']['total']['metrics']['Ir']['values']
        base, head = values['old'], values['new']
        if any(type(v) is not int or v <= 0 for v in (base, head)):
            raise ValueError(f'Invalid instruction counts for {case}')
        rows[case] = {'case': case, 'base': base, 'head': head,
                      'change_percent': 100 * (head - base) / base}
    if set(rows) != set(expected):
        raise ValueError(f'Missing benchmark cases: {set(expected) - set(rows)}')
    cases = [rows[c] for c in sorted(rows)]
    base_sum = sum(r['base'] for r in cases)
    head_sum = sum(r['head'] for r in cases)
    # Integer comparisons keep the exact 1% boundary stable.
    passed = head_sum * 100 <= base_sum * 99 and all(
        r['head'] * 100 < r['base'] * 101 for r in cases)
    return {'schema_version': 1, 'metric': 'Ir', 'cases': cases,
            'improvement_percent': 100 * (base_sum - head_sum) / base_sum,
            'absolute_delta': head_sum - base_sum,
            'geometric_mean_ratio': math.exp(sum(math.log(r['head'] / r['base']) for r in cases) / len(cases)),
            'gate': 'pass' if passed else 'not_passed'}
