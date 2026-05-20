#!/usr/bin/env python3
"""Analyze existing verl-agent logs and write a baseline profiling report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from profiler.log_parser import iter_existing_logs, parse_profile_events, parse_response_cases, parse_step_metrics
from profiler.report import build_env_event_summary, build_markdown_report, build_profile_summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logs", nargs="+", required=True, help="Log paths or glob patterns.")
    parser.add_argument("--out", default="reports/baseline_profile.md")
    parser.add_argument("--json-out", default=None, help="Optional machine-readable JSON summary path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logs = iter_existing_logs(args.logs)
    if not logs:
        raise SystemExit(f"No logs matched: {args.logs}")

    step_rows = []
    cases = []
    env_events = []
    for log in logs:
        step_rows.extend(parse_step_metrics(log))
        cases.extend(parse_response_cases(log))
        env_events.extend(parse_profile_events(log))

    report = build_markdown_report(step_rows, cases, env_events)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report, encoding="utf-8")

    json_out = Path(args.json_out) if args.json_out else out_path.with_suffix(".json")
    json_out.parent.mkdir(parents=True, exist_ok=True)
    summary = build_profile_summary(step_rows, cases)
    summary["env_profile_events"] = build_env_event_summary(env_events)
    json_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(
        f"logs={len(logs)} step_rows={len(step_rows)} cases={len(cases)} env_events={len(env_events)} "
        f"wrote={out_path} json={json_out}"
    )


if __name__ == "__main__":
    main()
