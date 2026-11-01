"""Check reporting outcomes with in-memory fixtures, without invoking Gradle."""

import io
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from run_scaffold_tests import markdown_summary, run_suite


class ScaffoldReportingTest(unittest.TestCase):
    def run_fixture(self, callback):
        case = type("Fixture", (unittest.TestCase,), {"test_fixture": callback})
        return run_suite(unittest.TestSuite([case("test_fixture")]), stream=io.StringIO())

    def test_success_is_reported_with_readable_status(self):
        report = self.run_fixture(lambda test: test.assertTrue(True))
        self.assertEqual("passed", report["result"])
        self.assertEqual("passed", report["tests"][0]["status"])
        self.assertIn("✅ Passed", markdown_summary(report))

    def test_assertion_failure_keeps_its_traceback_and_fails_the_run(self):
        report = self.run_fixture(lambda test: test.fail("Fixture assertion failed"))
        self.assertEqual("failed", report["result"])
        self.assertEqual("failed", report["tests"][0]["status"])
        self.assertIn("AssertionError: Fixture assertion failed", report["tests"][0]["traceback"])
        self.assertIn("❌ Failed", markdown_summary(report))

    def test_unexpected_exception_keeps_its_traceback(self):
        def broken(test):
            raise RuntimeError("Gradle process did not finish")

        report = self.run_fixture(broken)
        self.assertEqual("failed", report["result"])
        self.assertEqual("error", report["tests"][0]["status"])
        self.assertIn("RuntimeError: Gradle process did not finish", report["tests"][0]["traceback"])
        self.assertIn("❌ Error", markdown_summary(report))

    def test_skip_reason_is_retained_and_an_entirely_skipped_suite_cannot_pass(self):
        report = self.run_fixture(lambda test: test.skipTest("Minestom is absent"))
        self.assertEqual("failed", report["result"])
        self.assertEqual("skipped", report["tests"][0]["status"])
        self.assertEqual("Minestom is absent", report["tests"][0]["detail"])
        self.assertIn("⏩ Skipped", markdown_summary(report))

    def test_empty_suite_cannot_report_a_validation(self):
        report = run_suite(unittest.TestSuite(), stream=io.StringIO())
        self.assertEqual("failed", report["result"])
        self.assertEqual(0, report["tests_run"])
        self.assertIn("No scaffold integration tests", report["error"])
        self.assertIn("❌ Failed", markdown_summary(report))

    def test_failing_subtest_is_not_lost_from_the_summary(self):
        def cache_check(test):
            with test.subTest(attempt=1):
                test.fail("Cache was not reused")

        report = self.run_fixture(cache_check)
        self.assertEqual("failed", report["result"])
        self.assertIn("attempt=1", report["tests"][0]["test"])
        self.assertIn("Cache was not reused", report["tests"][0]["traceback"])

    def test_skipped_optional_fixture_does_not_hide_a_passing_required_fixture(self):
        passing = type("Required", (unittest.TestCase,), {"test_required": lambda test: None})
        skipped = type("Optional", (unittest.TestCase,),
                       {"test_optional": lambda test: test.skipTest("Target is absent")})
        report = run_suite(unittest.TestSuite([passing("test_required"), skipped("test_optional")]),
                           stream=io.StringIO())
        self.assertEqual("passed", report["result"])
        self.assertEqual(1, report["skipped"])
        self.assertEqual(["passed", "skipped"], [item["status"] for item in report["tests"]])

    def test_summary_escapes_exception_text_without_changing_the_json_evidence(self):
        report = self.run_fixture(lambda test: test.fail("Missing <module> | saved\nSecond line"))
        summary = markdown_summary(report)
        self.assertIn("&lt;module&gt; \\| saved Second line", summary)
        self.assertEqual("Missing <module> | saved\nSecond line", report["tests"][0]["detail"])


if __name__ == "__main__":
    unittest.main()
