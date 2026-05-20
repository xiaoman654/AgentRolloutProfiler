#!/usr/bin/env python3
"""Analyze existing verl-agent logs and write a baseline profiling report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from profiler.log_parser import iter_existing_logs, parse_response_cases, parse_step_metrics
from profiler.report import build_markdown_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logs", nargs="+", required=True, help="Log paths or glob patterns.")
    parser.add_argument("--out", default="reports/baseline_profile.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logs = iter_existing_logs(args.logs)
    if not logs:
        raise SystemExit(f"No logs matched: {args.logs}")

    step_rows = []
    cases = []
    for log in logs:
        step_rows.extend(parse_step_metrics(log))
        cases.extend(parse_response_cases(log))

    report = build_markdown_report(step_rows, cases)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")

    print(f"logs={len(logs)} step_rows={len(step_rows)} cases={len(cases)} wrote={out_path}")


if __name__ == "__main__":
    main()

