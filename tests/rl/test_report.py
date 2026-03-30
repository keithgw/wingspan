import json
import os
import tempfile
import unittest

from src.rl.linear_policy import LinearPolicy
from src.rl.report import generate_report


class TestGenerateReport(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.policy_path = os.path.join(self.tmpdir, "test_policy.npz")
        policy = LinearPolicy()
        policy.save(self.policy_path)

    def test_generates_valid_notebook(self):
        output = os.path.join(self.tmpdir, "report.ipynb")
        result = generate_report(self.policy_path, output_path=output, models_dir=self.tmpdir)
        self.assertEqual(result, output)
        self.assertTrue(os.path.isfile(output))

        with open(output, encoding="utf-8") as f:
            nb = json.load(f)

        self.assertEqual(nb["nbformat"], 4)
        self.assertIn("cells", nb)
        self.assertIn("metadata", nb)
        self.assertEqual(len(nb["cells"]), 16)

    def test_cell_types(self):
        output = os.path.join(self.tmpdir, "report.ipynb")
        generate_report(self.policy_path, output_path=output, models_dir=self.tmpdir)

        with open(output, encoding="utf-8") as f:
            nb = json.load(f)

        types = [c["cell_type"] for c in nb["cells"]]
        self.assertIn("markdown", types)
        self.assertIn("code", types)
        for cell in nb["cells"]:
            self.assertIn(cell["cell_type"], ("markdown", "code"))

    def test_missing_policy_raises(self):
        with self.assertRaises(FileNotFoundError):
            generate_report("/nonexistent/policy.npz")

    def test_creates_output_directory(self):
        output = os.path.join(self.tmpdir, "subdir", "report.ipynb")
        generate_report(self.policy_path, output_path=output, models_dir=self.tmpdir)
        self.assertTrue(os.path.isfile(output))

    def test_paths_safely_escaped(self):
        output = os.path.join(self.tmpdir, "report.ipynb")
        generate_report(self.policy_path, output_path=output, models_dir=self.tmpdir)

        with open(output, encoding="utf-8") as f:
            content = f.read()

        # Policy path should appear as a repr'd string, not raw interpolation
        self.assertIn(repr(self.policy_path), content)


if __name__ == "__main__":
    unittest.main()
