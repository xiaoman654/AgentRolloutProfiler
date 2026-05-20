"""Generate markdown and JSON summaries from parsed profiling data."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean

from .schema import EnvProfileEvent, ResponseCase, StepMetrics


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


def _short_log_name(log: str) -> str:
    return Path(log).name


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


def _action_counts(cases: list[ResponseCase]) -> dict[str, int]:
    counts = Counter(case.action_type or "unknown" for case in cases if case.action or case.response)
    return dict(counts.most_common())


def _score_summary(cases: list[ResponseCase]) -> dict[str, int]:
    scored = [case for case in cases if case.score is not None]
    nonzero = [case for case in scored if case.score and case.score > 0]
    success = [case for case in scored if case.score == 10.0]
    return {
        "parsed_cases": len(cases),
        "scored_cases": len(scored),
        "nonzero_score_cases": len(nonzero),
        "success_score_10_cases": len(success),
    }


def _metric_average_block(rows: list[StepMetrics], keys: list[str]) -> dict[str, float | None]:
    return {key: _average(rows, key) for key in keys}


def _split_rows(rows: list[StepMetrics]) -> tuple[list[StepMetrics], list[StepMetrics]]:
    validation_rows = [row for row in rows if "timing_s/testing" in row.metrics]
    normal_rows = [row for row in rows if "timing_s/testing" not in row.metrics and "timing_s/step" in row.metrics]
    return normal_rows, validation_rows


def build_profile_summary(rows: list[StepMetrics], cases: list[ResponseCase]) -> dict[str, object]:
    """Build a machine-readable summary for downstream plotting/comparison."""

    grouped_rows = _group_by_log(rows)
    cases_by_log: dict[str, list[ResponseCase]] = defaultdict(list)
    for case in cases:
        cases_by_log[case.source_log].append(case)

    per_log: dict[str, object] = {}
    for log, log_rows in grouped_rows.items():
        normal_rows, validation_rows = _split_rows(log_rows)
        testing_share = None
        validation_step_sum = _sum(validation_rows, "timing_s/step")
        if validation_step_sum:
            testing_share = _sum(validation_rows, "timing_s/testing") / validation_step_sum
        log_cases = cases_by_log.get(log, [])
        total_search, unique_search, repeat_rate = search_query_stats(log_cases)
        per_log[log] = {
            "short_name": _short_log_name(log),
            "step_rows": len(log_rows),
            "normal_rows": len(normal_rows),
            "validation_rows": len(validation_rows),
            "avg_normal_step_s": _average(normal_rows, "timing_s/step"),
            "avg_validation_step_s": _average(validation_rows, "timing_s/step"),
            "validation_testing_share": testing_share,
            "timing_avg_all_rows": _metric_average_block(log_rows, TIMING_KEYS),
            "timing_avg_normal_rows": _metric_average_block(normal_rows, TIMING_KEYS),
            "timing_avg_validation_rows": _metric_average_block(validation_rows, TIMING_KEYS),
            "length_avg_all_rows": _metric_average_block(log_rows, LENGTH_KEYS),
            "action_type_counts": _action_counts(log_cases),
            "search_query_total": total_search,
            "search_query_unique": unique_search,
            "search_query_repeat_rate": repeat_rate,
            "score_summary": _score_summary(log_cases),
        }

    total_search, unique_search, repeat_rate = search_query_stats(cases)
    normal_rows, validation_rows = _split_rows(rows)
    return {
        "logs": per_log,
        "overall": {
            "step_rows": len(rows),
            "normal_rows": len(normal_rows),
            "validation_rows": len(validation_rows),
            "timing_avg_all_rows": _metric_average_block(rows, TIMING_KEYS),
            "timing_avg_normal_rows": _metric_average_block(normal_rows, TIMING_KEYS),
            "timing_avg_validation_rows": _metric_average_block(validation_rows, TIMING_KEYS),
            "length_avg_all_rows": _metric_average_block(rows, LENGTH_KEYS),
            "action_type_counts": _action_counts(cases),
            "search_query_total": total_search,
            "search_query_unique": unique_search,
            "search_query_repeat_rate": repeat_rate,
            "score_summary": _score_summary(cases),
        },
    }


def _event_average(events: list[EnvProfileEvent], key: str) -> float | None:
    values = []
    for event in events:
        value = event.payload.get(key)
        if isinstance(value, (int, float)):
            values.append(float(value))
    return mean(values) if values else None


def build_env_event_summary(events: list[EnvProfileEvent]) -> dict[str, dict[str, float | int | None]]:
    grouped: dict[str, list[EnvProfileEvent]] = defaultdict(list)
    for event in events:
        grouped[event.event].append(event)

    summary: dict[str, dict[str, float | int | None]] = {}
    for event_name, event_rows in grouped.items():
        summary[event_name] = {
            "count": len(event_rows),
            "avg_total_s": _event_average(event_rows, "total_s"),
            "avg_projection_s": _event_average(event_rows, "projection_s"),
            "avg_env_step_s": _event_average(event_rows, "env_step_s"),
            "avg_format_obs_s": _event_average(event_rows, "format_obs_s"),
            "avg_build_text_obs_s": _event_average(event_rows, "build_text_obs_s"),
            "avg_worker_step_s": _event_average(event_rows, "worker_step_s"),
            "avg_available_actions_s": _event_average(event_rows, "available_actions_s"),
            "avg_reward_rewrite_s": _event_average(event_rows, "reward_rewrite_s"),
            "avg_obs_chars": _event_average(event_rows, "obs_chars"),
            "avg_text_obs_chars": _event_average(event_rows, "text_obs_chars"),
        }
    return summary


def build_markdown_report(
    rows: list[StepMetrics],
    cases: list[ResponseCase],
    env_events: list[EnvProfileEvent] | None = None,
) -> str:
    lines: list[str] = []
    lines.append("# Baseline Rollout Profile")
    lines.append("")
    lines.append("Generated from verl-agent console logs.")
    lines.append("")

    summary = build_profile_summary(rows, cases)
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

    normal_rows, validation_rows = _split_rows(rows)
    lines.append("## Overall Timing Averages")
    lines.append("")
    lines.append("| Metric | All rows | Normal rows | Validation rows |")
    lines.append("|---|---:|---:|---:|")
    for key in TIMING_KEYS:
        lines.append(
            f"| `{key}` | {_fmt(_average(rows, key))} | "
            f"{_fmt(_average(normal_rows, key))} | {_fmt(_average(validation_rows, key))} |"
        )
    lines.append("")

    lines.append("## Overall Length Averages")
    lines.append("")
    lines.append("| Metric | Average |")
    lines.append("|---|---:|")
    for key in LENGTH_KEYS:
        lines.append(f"| `{key}` | {_fmt(_average(rows, key))} |")
    lines.append("")

    lines.append("## Per-Log Timing and Length")
    lines.append("")
    for log, log_rows in grouped.items():
        log_normal_rows, log_validation_rows = _split_rows(log_rows)
        lines.append(f"### `{_short_log_name(log)}`")
        lines.append("")
        lines.append("| Metric | Normal rows | Validation rows |")
        lines.append("|---|---:|---:|")
        for key in TIMING_KEYS:
            lines.append(f"| `{key}` | {_fmt(_average(log_normal_rows, key))} | {_fmt(_average(log_validation_rows, key))} |")
        for key in LENGTH_KEYS:
            lines.append(f"| `{key}` | {_fmt(_average(log_normal_rows, key))} | {_fmt(_average(log_validation_rows, key))} |")
        lines.append("")

    action_counts = Counter(summary["overall"]["action_type_counts"])
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

    score_summary = summary["overall"]["score_summary"]
    lines.append("## Parsed Case Scores")
    lines.append("")
    lines.append(f"- parsed cases: {score_summary['parsed_cases']}")
    lines.append(f"- scored cases: {score_summary['scored_cases']}")
    lines.append(f"- nonzero-score cases: {score_summary['nonzero_score_cases']}")
    lines.append(f"- success-score-10 cases: {score_summary['success_score_10_cases']}")
    lines.append("")

    env_events = env_events or []
    if env_events:
        lines.append("## Environment-Level Profile Events")
        lines.append("")
        lines.append("| Event | Count | avg total_s | avg env_step_s | avg projection_s | avg format_obs_s | avg build_text_obs_s | avg obs chars |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
        for event_name, event_summary in build_env_event_summary(env_events).items():
            lines.append(
                f"| `{event_name}` | {event_summary['count']} | "
                f"{_fmt(event_summary.get('avg_total_s'))} | "
                f"{_fmt(event_summary.get('avg_env_step_s'))} | "
                f"{_fmt(event_summary.get('avg_projection_s'))} | "
                f"{_fmt(event_summary.get('avg_format_obs_s'))} | "
                f"{_fmt(event_summary.get('avg_build_text_obs_s'))} | "
                f"{_fmt(event_summary.get('avg_obs_chars'))} |"
            )
        lines.append("")

    lines.append("## Phase 1 Decision Notes")
    lines.append("")
    lines.append("- Use this report to decide whether observation compression, search cache, or parser optimization is worth testing.")
    lines.append("- Do not treat speed improvements as valid unless task score drift is measured in a later controlled run.")
    lines.append("")
    return "\n".join(lines)
