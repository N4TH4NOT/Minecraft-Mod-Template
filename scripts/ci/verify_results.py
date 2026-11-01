#!/usr/bin/env python3
"""Reject missing, empty or entirely skipped JUnit reports where tests exist."""

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

def verify(directory):
    reports = sorted((directory / "build/test-results").rglob("TEST-*.xml"))
    if not reports:
        raise ValueError(f"{directory}: JUnit reports are missing; application validation requires tests")
    executed = 0
    skipped = 0
    for path in reports:
        report = ET.parse(path).getroot()
        suites = [report] if report.tag == "testsuite" else list(report.iter("testsuite"))
        for suite in suites:
            failures = int(suite.get("failures", "0")) + int(suite.get("errors", "0"))
            if failures:
                raise ValueError(f"{path}: {failures} test failures or errors")
            ignored = int(suite.get("skipped", suite.get("disabled", "0")))
            tests = int(suite.get("tests", "0"))
            executed += tests - ignored
            skipped += ignored
    if executed <= 0:
        raise ValueError(f"{directory}: no tests ran (empty or entirely skipped suites)")
    return {"executed": executed, "skipped": skipped, "reports": len(reports)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--modules", nargs="+", required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = {"result": "passed", "modules": {}}
    try:
        for module in args.modules:
            directory = args.root / module
            report["modules"][module] = verify(directory)
    except (ValueError, OSError, ET.ParseError) as error:
        report.update(result="failed", error=str(error))
    text = json.dumps(report, indent=2)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text + "\n", encoding="utf-8")
    if report["result"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
