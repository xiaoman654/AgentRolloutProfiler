"""Generate markdown summaries from parsed profiling data."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean

from .schema import ResponseCase, StepMetrics


TIMING_KEYS = [
    "timing_s/gen",
    "timing_s/reward",
    "timing_s/old_log_prob",
    "timing_s/ref",
    "timing_s/adv",
    "timing_s/update_actor",
    "timing_s/testing",
    "timing_s/step",
]

LENGTH_KEYS = [
    "prompt_length/mean",
    "prompt_length/max",
    "prompt_length/clip_ratio",
    "response_length/mean",
    "response_length/max",
    "response_length/clip_ratio",
]


def _fmt(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.3f}"


def _average(rows: list[StepMetrics], key: str) -> float | None:
    values = [row.metrics[key] for row in rows if key in row.metrics]
    return mean(values) if values else None


def _sum(rows: list[StepMetrics], key: str) -> float:
    return sum(row.metrics[key] for row in rows if key in row.metrics)


def _group_by_log(rows: list[StepMetrics]) -> dict[str, list[StepMetrics]]:
    grouped: dict[str, list[StepMetrics]] = defaultdict(list)
    for row in rows:
        grouped[row.source_log].append(row)
    return dict(grouped)


def search_query_stats(cases: list[ResponseCase]) -> tuple[int, int, float]:
    queries = []
    for case in cases:
        action = case.action.strip()
        if action.lower().startswith("search[") and action.endswith("]"):
            queries.append(action[len("search[") : -1].strip().lower())
    total = len(queries)
    unique = len(set(queries))
    repeat_rate = 0.0 if total == 0 else 1.0 - unique / total
    return total, unique, repeat_rate


def build_markdown_report(rows: list[StepMetrics], cases: list[ResponseCase]) -> str:
    lines: list[str] = []
    lines.append("# Baseline Rollout Profile")
    lines.append("")
    lines.append("Generated from verl-agent console logs.")
    lines.append("")

    grouped = _group_by_log(rows)
    lines.append("## Log Summary")
    lines.append("")
    lines.append("| Log | parsed step lines | normal rows | validation rows | avg normal step_s | avg validation step_s | validation testing share |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for log, log_rows in grouped.items():
        validation_rows = [row for row in log_rows if "timing_s/testing" in row.metrics]
        normal_rows = [row for row in log_rows if "timing_s/testing" not in row.metrics and "timing_s/step" in row.metrics]
        avg_normal_step = _average(normal_rows, "timing_s/step")
        avg_validation_step = _average(validation_rows, "timing_s/step")
        testing_share = None
        validation_step_sum = _sum(validation_rows, "timing_s/step")
        if validation_step_sum:
            testing_share = _sum(validation_rows, "timing_s/testing") / validation_step_sum
        lines.append(
            f"| `{log}` | {len(log_rows)} | {len(normal_rows)} | {len(validation_rows)} | "
            f"{_fmt(avg_normal_step)} | {_fmt(avg_validation_step)} | {_fmt(testing_share)} |"
        )
    lines.append("")

    lines.append("## Timing Averages")
    lines.append("")
    lines.append("| Metric | Average |")
    lines.append("|---|---:|")
    for key in TIMING_KEYS:
        lines.append(f"| `{key}` | {_fmt(_average(rows, key))} |")
    lines.append("")

    lines.append("## Length Averages")
    lines.append("")
    lines.append("| Metric | Average |")
    lines.append("|---|---:|")
    for key in LENGTH_KEYS:
        lines.append(f"| `{key}` | {_fmt(_average(rows, key))} |")
    lines.append("")

    action_counts = Counter(case.action_type or "unknown" for case in cases if case.action or case.response)
    lines.append("## Action Type Distribution")
    lines.append("")
    lines.append("| Action type | Count |")
    lines.append("|---|---:|")
    for action_type, count in action_counts.most_common():
        lines.append(f"| `{action_type}` | {count} |")
    lines.append("")

    total_search, unique_search, repeat_rate = search_query_stats(cases)
    lines.append("## Search Query Repetition")
    lines.append("")
    lines.append(f"- total search actions: {total_search}")
    lines.append(f"- unique search queries: {unique_search}")
    lines.append(f"- observed repeat rate: {_fmt(repeat_rate)}")
    lines.append("")

    scored = [case for case in cases if case.score is not None]
    nonzero = [case for case in scored if case.score and case.score > 0]
    success = [case for case in scored if case.score == 10.0]
    lines.append("## Parsed Case Scores")
    lines.append("")
    lines.append(f"- parsed cases: {len(cases)}")
    lines.append(f"- scored cases: {len(scored)}")
    lines.append(f"- nonzero-score cases: {len(nonzero)}")
    lines.append(f"- success-score-10 cases: {len(success)}")
    lines.append("")

    lines.append("## Phase 1 Decision Notes")
    lines.append("")
    lines.append("- Use this report to decide whether observation compression, search cache, or parser optimization is worth testing.")
    lines.append("- Do not treat speed improvements as valid unless task score drift is measured in a later controlled run.")
    lines.append("")
    return "\n".join(lines)
