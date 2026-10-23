import json
from pathlib import Path
import tempfile
import unittest

from compare import select_workloads


class WorkloadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.harness = self.root / 'tools/gungraun'
        (self.harness / 'fixtures').mkdir(parents=True)
        self.fixture('tools/gungraun/fixtures/default.js')

    def fixture(self, name):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('print(1);\n')
        return path

    def test_default_and_custom_workloads(self):
        self.assertEqual(list(select_workloads(self.harness, '', '')), ['default'])
        path = self.fixture('testing/custom-case.js')
        self.assertEqual(select_workloads(self.harness, json.dumps([
            'testing/custom-case.js']), 'custom'), {'custom_case': path})

    def test_invalid_missing_and_duplicate_workloads(self):
        self.fixture('testing/default.js')
        for requested in [[], {}, ['missing.js'], ['../outside.js'],
                          [str(self.harness / 'fixtures/default.js')], [1],
                          ['testing/default.js', 'tools/gungraun/fixtures/default.js']]:
            with self.subTest(requested=requested), self.assertRaises(ValueError):
                select_workloads(self.harness, json.dumps(requested), '')

    def test_empty_filter_result_and_symlink_escape(self):
        with self.assertRaises(ValueError):
            select_workloads(self.harness, '', 'absent')
        (self.root / 'escape.js').symlink_to('/etc/passwd')
        with self.assertRaises(ValueError):
            select_workloads(self.harness, '["escape.js"]', '')


if __name__ == '__main__':
    unittest.main()
