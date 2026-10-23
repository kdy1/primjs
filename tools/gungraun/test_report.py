import json
from pathlib import Path
import tempfile
import unittest

from report import summarize


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def case(self, name, base, head):
        path = self.root / name / 'summary.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'version': '7', 'id': name, 'profiles': [
            {'tool': 'Callgrind', 'data': {'total': {'metrics': {
                'Ir': {'values': {'old': base, 'new': head}}}}}}]}))
        return path

    def test_exact_thresholds(self):
        self.case('a', 10000, 9900)
        self.assertEqual(summarize(self.root, ['a'])['gate'], 'pass')
        self.case('a', 10000, 9901)
        self.assertEqual(summarize(self.root, ['a'])['gate'], 'not_passed')

    def test_large_gain_does_not_hide_one_percent_regression(self):
        self.case('a', 10000, 5000)
        self.case('b', 100, 101)
        self.assertEqual(summarize(self.root, ['a', 'b'])['gate'], 'not_passed')

    def test_same_sha_is_not_an_optimization(self):
        self.case('a', 100, 100)
        self.assertEqual(summarize(self.root, ['a'])['gate'], 'not_passed')

    def test_incomplete_or_duplicate_results_fail(self):
        path = self.case('a', 100, 99)
        with self.assertRaises(ValueError):
            summarize(self.root, ['a', 'b'])
        self.case('duplicate', 100, 99).write_text(path.read_text())
        with self.assertRaises(ValueError):
            summarize(self.root, ['a'])

    def test_missing_baseline_and_unknown_schema_fail(self):
        path = self.case('a', 100, 99)
        data = json.loads(path.read_text())
        del data['profiles'][0]['data']['total']['metrics']['Ir']['values']['old']
        path.write_text(json.dumps(data))
        with self.assertRaises(KeyError):
            summarize(self.root, ['a'])
        data['version'] = '8'
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            summarize(self.root, ['a'])


if __name__ == '__main__':
    unittest.main()
