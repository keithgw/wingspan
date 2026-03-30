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

    def test_generates_html_report(self):
        output = os.path.join(self.tmpdir, "report.html")
        result = generate_report(self.policy_path, output_path=output, models_dir=self.tmpdir)
        self.assertEqual(result, output)
        self.assertTrue(os.path.isfile(output))

        with open(output, encoding="utf-8") as f:
            content = f.read()

        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("Policy Analysis Report", content)
        self.assertIn("Action Weights", content)
        self.assertIn("Feature Importance", content)
        self.assertIn("Strategy Rules", content)
        self.assertIn("Decision Traces", content)

    def test_contains_embedded_images(self):
        output = os.path.join(self.tmpdir, "report.html")
        generate_report(self.policy_path, output_path=output, models_dir=self.tmpdir)

        with open(output, encoding="utf-8") as f:
            content = f.read()

        # Charts are embedded as base64 PNGs
        self.assertIn("data:image/png;base64,", content)

    def test_missing_policy_raises(self):
        with self.assertRaises(FileNotFoundError):
            generate_report("/nonexistent/policy.npz")

    def test_creates_output_directory(self):
        output = os.path.join(self.tmpdir, "subdir", "report.html")
        generate_report(self.policy_path, output_path=output, models_dir=self.tmpdir)
        self.assertTrue(os.path.isfile(output))

    def test_default_output_path(self):
        result = generate_report(self.policy_path, models_dir=self.tmpdir)
        expected = os.path.join(self.tmpdir, "policy_report.html")
        self.assertEqual(result, expected)
        self.assertTrue(os.path.isfile(expected))


if __name__ == "__main__":
    unittest.main()
