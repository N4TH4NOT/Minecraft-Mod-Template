#!/usr/bin/env python3
"""Run scaffold fixtures and keep readable status summaries and failure evidence."""

import argparse
import html
import json
from pathlib import Path
import sys
import traceback
import unittest


STATUS_LABELS = {
    "passed": "✅ Passed",
    "failed": "❌ Failed",
    "error": "❌ Error",
    "skipped": "⚠️ Skipped",
    "expected_failure": "⚠️ Expected failure",
    "unexpected_success": "❌ Unexpected success",
}


class ScaffoldResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.outcomes = []

    def record(self, test, status, detail="", trace=""):
        self.outcomes.append({"test": test.id(), "status": status, "detail": detail, "traceback": trace})

    def addSuccess(self, test):
        super().addSuccess(test)
        self.record(test, "passed")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.record(test, "failed", str(err[1]), self.failures[-1][1])

    def addError(self, test, err):
        super().addError(test, err)
        self.record(test, "error", str(err[1]), self.errors[-1][1])

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.record(test, "skipped", reason)

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            failed = issubclass(err[0], test.failureException)
            trace = (self.failures if failed else self.errors)[-1][1]
            self.record(subtest, "failed" if failed else "error", str(err[1]), trace)

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.record(test, "expected_failure", str(err[1]), self.expectedFailures[-1][1])

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.record(test, "unexpected_success", "A test marked as an expected failure passed.")


def run_suite(suite, stream=None):
    if not suite.countTestCases():
        return {"result": "failed", "tests_run": 0, "tests": [],
                "error": "No scaffold integration tests were discovered."}
    result = unittest.TextTestRunner(verbosity=2, resultclass=ScaffoldResult, stream=stream).run(suite)
    executed = any(item["status"] != "skipped" for item in result.outcomes)
    report = {"result": "passed" if result.wasSuccessful() and executed else "failed",
              "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
              "skipped": len(result.skipped), "tests": result.outcomes}
    if not executed:
        report["error"] = "All scaffold integration tests were skipped; no fixture was validated."
    return report


def markdown_summary(report):
    def cell(value):
        value = " ".join(str(value).splitlines())
        if len(value) > 240:
            value = value[:237] + "..."
        return html.escape(value, quote=False).replace("|", "\\|")

    overall = "✅ Passed" if report["result"] == "passed" else "❌ Failed"
    lines = ["### Scaffold integration tests", "", f"Result: **{overall}**", "",
             "| Fixture | Status | Details |", "| --- | --- | --- |"]
    for item in report["tests"]:
        name = item["test"].rsplit(".", 1)[-1].removeprefix("test_").replace("_", " ")
        lines.append(f"| {cell(name)} | {STATUS_LABELS[item['status']]} | {cell(item['detail'])} |")
    if report.get("error"):
        lines.append(f"| Test suite | ❌ Failed | {cell(report['error'])} |")
    lines.extend(["", f"Test cases run: {report['tests_run']}.", "",
                  "Full logs, test identifiers and exception tracebacks are retained in the "
                  "`scaffold-integration` artifact (`scaffold-tests.log` and `scaffold-tests.json`).", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run_suite(unittest.defaultTestLoader.discover("scripts/ci/integration"))
    except Exception:
        report = {"result": "failed", "tests_run": 0, "tests": [], "error": traceback.format_exc()}
        print(report["error"], file=sys.stderr)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    rendered = markdown_summary(report)
    with args.summary.open("a", encoding="utf-8") as summary:
        summary.write(rendered)
    print(rendered)
    raise SystemExit(0 if report["result"] == "passed" else 1)


if __name__ == "__main__":
    main()
