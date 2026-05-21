#!/usr/bin/env python3
"""Build a Phase 2 report focused on rollout validation cost."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from profiler.log_parser import (
    iter_existing_logs,
    parse_profile_events,
    parse_response_cases,
    parse_step_metrics,
    parse_time_p_runtime,
)
from profiler.report import build_env_event_summary, search_query_stats
from profiler.schema import EnvProfileEvent, LogRuntime, ResponseCase, StepMetrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--logs", nargs="+", required=True, help="Log paths or glob patterns.")
    parser.add_argument("--out", default="reports/phase2_rollout_validation_profile.md")
    parser.add_argument("--json-out", default=None, help="Optional machine-readable JSON output path.")
    return parser.parse_args()


def avg(values: Iterable[float]) -> float | None:
    values = list(values)
    return mean(values) if values else None


def fmt(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.3f}"


def short_log_name(log: str) -> str:
    return Path(log).name


def split_rows(rows: list[StepMetrics]) -> tuple[list[StepMetrics], list[StepMetrics]]:
    validation_rows = [
        row
        for row in rows
        if "timing_s/testing" in row.metrics or any(key.startswith("val/") for key in row.metrics)
    ]
    normal_rows = [
        row
        for row in rows
        if row not in validation_rows and "timing_s/step" in row.metrics
    ]
    return normal_rows, validation_rows


def avg_metric(rows: list[StepMetrics], key: str) -> float | None:
    return avg(row.metrics[key] for row in rows if key in row.metrics)


def sum_metric(rows: list[StepMetrics], key: str) -> float:
    return sum(row.metrics[key] for row in rows if key in row.metrics)


def grouped_by_log(items):
    grouped = defaultdict(list)
    for item in items:
        grouped[item.source_log].append(item)
    return dict(grouped)


def score_summary(cases: list[ResponseCase]) -> dict[str, int | float | None]:
    scored = [case.score for case in cases if case.score is not None]
    successes = [score for score in scored if score == 10.0]
    nonzero = [score for score in scored if score and score > 0]
    return {
        "parsed_cases": len(cases),
        "scored_cases": len(scored),
        "nonzero_cases": len(nonzero),
        "success_score_10_cases": len(successes),
        "avg_score": avg(scored),
    }


def action_counts(cases: list[ResponseCase]) -> dict[str, int]:
    counter = Counter(case.action_type or "unknown" for case in cases if case.action or case.response)
    return dict(counter.most_common())


def summarize_log(
    log: str,
    rows: list[StepMetrics],
    cases: list[ResponseCase],
    events: list[EnvProfileEvent],
    runtime: LogRuntime | None,
) -> dict[str, object]:
    normal_rows, validation_rows = split_rows(rows)
    validation_step_s = avg_metric(validation_rows, "timing_s/step")
    testing_s = avg_metric(validation_rows, "timing_s/testing")
    runtime_real_s = runtime.real_s if runtime else None
    if validation_step_s is None:
        validation_step_s = runtime_real_s
    if testing_s is None:
        testing_s = runtime_real_s
    normal_step_s = avg_metric(normal_rows, "timing_s/step")
    validation_non_testing_s = None
    if validation_step_s is not None and testing_s is not None:
        validation_non_testing_s = validation_step_s - testing_s
    validation_testing_share = None
    validation_step_sum = sum_metric(validation_rows, "timing_s/step")
    if validation_step_sum:
        validation_testing_share = sum_metric(validation_rows, "timing_s/testing") / validation_step_sum

    total_search, unique_search, repeat_rate = search_query_stats(cases)
    env_summary = build_env_event_summary(events)
    manager_step = env_summary.get("manager_step", {})
    worker_step = env_summary.get("worker_step", {})

    return {
        "short_name": short_log_name(log),
        "step_rows": len(rows),
        "normal_rows": len(normal_rows),
        "validation_rows": len(validation_rows),
        "avg_normal_step_s": normal_step_s,
        "avg_validation_step_s": validation_step_s,
        "avg_validation_testing_s": testing_s,
        "avg_validation_non_testing_s": validation_non_testing_s,
        "validation_testing_share": validation_testing_share,
        "runtime_real_s": runtime_real_s,
        "runtime_user_s": runtime.user_s if runtime else None,
        "runtime_sys_s": runtime.sys_s if runtime else None,
        "avg_gen_s_normal": avg_metric(normal_rows, "timing_s/gen"),
        "avg_gen_s_validation": avg_metric(validation_rows, "timing_s/gen"),
        "avg_response_length": avg_metric(rows, "response_length/mean"),
        "avg_prompt_length": avg_metric(rows, "prompt_length/mean"),
        "cases": score_summary(cases),
        "action_counts": action_counts(cases),
        "search_query_total": total_search,
        "search_query_unique": unique_search,
        "search_query_repeat_rate": repeat_rate,
        "env_profile_events": env_summary,
        "avg_manager_step_s": manager_step.get("avg_total_s"),
        "avg_worker_step_s": worker_step.get("avg_total_s"),
    }


def build_summary(
    logs: list[Path],
    rows: list[StepMetrics],
    cases: list[ResponseCase],
    events: list[EnvProfileEvent],
    runtimes: list[LogRuntime],
) -> dict[str, object]:
    rows_by_log = grouped_by_log(rows)
    cases_by_log = grouped_by_log(cases)
    events_by_log = grouped_by_log(events)
    runtimes_by_log = {runtime.source_log: runtime for runtime in runtimes}
    per_log = {}
    for log in logs:
        key = str(log)
        per_log[key] = summarize_log(
            key,
            rows_by_log.get(key, []),
            cases_by_log.get(key, []),
            events_by_log.get(key, []),
            runtimes_by_log.get(key),
        )
    return {"logs": per_log}


def build_markdown(summary: dict[str, object]) -> str:
    lines: list[str] = []
    lines.append("# Phase 2 Rollout and Validation Profile")
    lines.append("")
    lines.append("This report focuses on validation/testing cost, after Phase 1 found that WebShop environment stepping is not the dominant bottleneck.")
    lines.append("")
    lines.append("## Validation Cost Summary")
    lines.append("")
    lines.append("| Log | normal step_s | validation step_s | validation testing_s | wall real_s | non-testing validation_s | testing share | validation rows |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for log_summary in summary["logs"].values():
        lines.append(
            f"| `{log_summary['short_name']}` | "
            f"{fmt(log_summary['avg_normal_step_s'])} | "
            f"{fmt(log_summary['avg_validation_step_s'])} | "
            f"{fmt(log_summary['avg_validation_testing_s'])} | "
            f"{fmt(log_summary['runtime_real_s'])} | "
            f"{fmt(log_summary['avg_validation_non_testing_s'])} | "
            f"{fmt(log_summary['validation_testing_share'])} | "
            f"{log_summary['validation_rows']} |"
        )
    lines.append("")

    lines.append("## Generation and Length Signals")
    lines.append("")
    lines.append("| Log | gen_s normal | gen_s validation | avg prompt length | avg response length |")
    lines.append("|---|---:|---:|---:|---:|")
    for log_summary in summary["logs"].values():
        lines.append(
            f"| `{log_summary['short_name']}` | "
            f"{fmt(log_summary['avg_gen_s_normal'])} | "
            f"{fmt(log_summary['avg_gen_s_validation'])} | "
            f"{fmt(log_summary['avg_prompt_length'])} | "
            f"{fmt(log_summary['avg_response_length'])} |"
        )
    lines.append("")

    lines.append("## Environment Timing Cross-Check")
    lines.append("")
    lines.append("| Log | manager_step_s | worker_step_s | search repeat rate | search total | unique search |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for log_summary in summary["logs"].values():
        lines.append(
            f"| `{log_summary['short_name']}` | "
            f"{fmt(log_summary['avg_manager_step_s'])} | "
            f"{fmt(log_summary['avg_worker_step_s'])} | "
            f"{fmt(log_summary['search_query_repeat_rate'])} | "
            f"{log_summary['search_query_total']} | "
            f"{log_summary['search_query_unique']} |"
        )
    lines.append("")

    lines.append("## Score and Case Counts")
    lines.append("")
    lines.append("| Log | parsed cases | scored cases | nonzero cases | success cases | avg score |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for log_summary in summary["logs"].values():
        case_summary = log_summary["cases"]
        lines.append(
            f"| `{log_summary['short_name']}` | "
            f"{case_summary['parsed_cases']} | "
            f"{case_summary['scored_cases']} | "
            f"{case_summary['nonzero_cases']} | "
            f"{case_summary['success_score_10_cases']} | "
            f"{fmt(case_summary['avg_score'])} |"
        )
    lines.append("")

    lines.append("## Phase 2 Reading Guide")
    lines.append("")
    lines.append("- If `testing share` stays near 1.0, optimization should target validation rollout volume, generation throughput, or evaluation frequency.")
    lines.append("- Eval-only logs may not contain `timing_s/testing`; in that case `wall real_s` from `/usr/bin/time -p` is the preferred latency signal.")
    lines.append("- If `manager_step_s` and `worker_step_s` remain below 0.1s, WebShop environment stepping is still not the priority.")
    lines.append("- If latency scales roughly linearly with eval size, validation batch size/frequency is a direct speed-quality tradeoff.")
    lines.append("- If score is unstable at small eval sizes, use small eval only for profiling and keep larger eval for final reporting.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    logs = iter_existing_logs(args.logs)
    if not logs:
        raise SystemExit(f"No logs matched: {args.logs}")

    rows: list[StepMetrics] = []
    cases: list[ResponseCase] = []
    events: list[EnvProfileEvent] = []
    runtimes: list[LogRuntime] = []
    for log in logs:
        rows.extend(parse_step_metrics(log))
        cases.extend(parse_response_cases(log))
        events.extend(parse_profile_events(log))
        runtimes.append(parse_time_p_runtime(log))

    summary = build_summary(logs, rows, cases, events, runtimes)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_markdown(summary), encoding="utf-8")

    json_out = Path(args.json_out) if args.json_out else out_path.with_suffix(".json")
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"logs={len(logs)} wrote={out_path} json={json_out}")


if __name__ == "__main__":
    main()
