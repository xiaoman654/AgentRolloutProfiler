#!/usr/bin/env python3
"""Estimate wall-clock savings from alternative validation schedules."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from statistics import mean


EVAL_SIZE_RE = re.compile(r"eval(\d+)", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase2-json", default="reports/phase2_rollout_validation_profile.json")
    parser.add_argument("--out", default="reports/phase3_eval_schedule_estimate.md")
    parser.add_argument("--json-out", default=None)
    parser.add_argument("--total-steps", type=int, default=32)
    parser.add_argument("--normal-step-s", type=float, default=21.5)
    parser.add_argument("--baseline-eval-size", type=int, default=64)
    parser.add_argument("--baseline-eval-freq", type=int, default=8)
    parser.add_argument("--candidate-eval-size", type=int, default=8)
    parser.add_argument("--candidate-eval-freq", type=int, default=8)
    parser.add_argument("--final-eval-size", type=int, default=64)
    return parser.parse_args()


def fmt(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.3f}"


def eval_size_from_name(name: str) -> int | None:
    match = EVAL_SIZE_RE.search(name)
    return int(match.group(1)) if match else None


def load_eval_times(path: Path) -> dict[int, float]:
    data = json.loads(path.read_text(encoding="utf-8"))
    values_by_size: dict[int, list[float]] = {}
    for log_summary in data.get("logs", {}).values():
        size = eval_size_from_name(log_summary.get("short_name", ""))
        if size is None:
            continue
        runtime = log_summary.get("runtime_real_s")
        validation_step = log_summary.get("avg_validation_step_s")
        value = runtime if runtime is not None else validation_step
        if value is None:
            continue
        values_by_size.setdefault(size, []).append(float(value))
    return {size: mean(values) for size, values in sorted(values_by_size.items())}


def validation_count(total_steps: int, freq: int, include_final: bool = True) -> int:
    if freq <= 0:
        return 0
    count = total_steps // freq
    if include_final and total_steps % freq != 0:
        count += 1
    return count


def estimate_schedule(
    *,
    total_steps: int,
    normal_step_s: float,
    eval_times: dict[int, float],
    eval_size: int,
    eval_freq: int,
    final_eval_size: int | None = None,
) -> dict[str, float | int | None]:
    train_time = total_steps * normal_step_s
    eval_time = eval_times.get(eval_size)
    if eval_time is None:
        raise ValueError(f"Missing eval time for eval{eval_size}")
    eval_runs = validation_count(total_steps, eval_freq, include_final=True)
    repeated_eval_time = eval_runs * eval_time
    final_extra_time = 0.0
    if final_eval_size is not None and final_eval_size != eval_size:
        final_eval_time = eval_times.get(final_eval_size)
        if final_eval_time is None:
            raise ValueError(f"Missing eval time for eval{final_eval_size}")
        final_extra_time = final_eval_time
    total_time = train_time + repeated_eval_time + final_extra_time
    return {
        "total_steps": total_steps,
        "normal_step_s": normal_step_s,
        "train_time_s": train_time,
        "eval_size": eval_size,
        "eval_freq": eval_freq,
        "eval_runs": eval_runs,
        "eval_time_s": eval_time,
        "repeated_eval_time_s": repeated_eval_time,
        "final_eval_size": final_eval_size,
        "final_extra_time_s": final_extra_time,
        "total_time_s": total_time,
    }


def build_markdown(summary: dict[str, object]) -> str:
    eval_times: dict[int, float] = summary["eval_times"]
    baseline: dict[str, object] = summary["baseline"]
    candidate: dict[str, object] = summary["candidate"]
    savings_s = baseline["total_time_s"] - candidate["total_time_s"]
    savings_pct = savings_s / baseline["total_time_s"] if baseline["total_time_s"] else 0.0

    lines: list[str] = []
    lines.append("# Phase 3 Eval Schedule Estimate")
    lines.append("")
    lines.append("This report estimates wall-clock savings from changing validation schedule, using measured Phase 2 eval runtimes.")
    lines.append("")
    lines.append("## Measured Eval Runtimes")
    lines.append("")
    lines.append("| Eval size | wall real_s |")
    lines.append("|---:|---:|")
    for size, runtime in eval_times.items():
        lines.append(f"| {size} | {fmt(runtime)} |")
    lines.append("")

    lines.append("## Schedule Estimate")
    lines.append("")
    lines.append("| Scenario | total steps | normal step_s | eval size | eval freq | repeated eval runs | final extra eval | estimated total_s |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for name, item in [("baseline", baseline), ("candidate", candidate)]:
        lines.append(
            f"| {name} | {item['total_steps']} | {fmt(item['normal_step_s'])} | "
            f"{item['eval_size']} | {item['eval_freq']} | {item['eval_runs']} | "
            f"{fmt(item['final_extra_time_s'])} | {fmt(item['total_time_s'])} |"
        )
    lines.append("")
    lines.append("## Estimated Savings")
    lines.append("")
    lines.append(f"- absolute savings: {fmt(savings_s)}s")
    lines.append(f"- relative savings: {fmt(savings_pct * 100.0)}%")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("- This is an estimate, not a replacement for a controlled training run.")
    lines.append("- It is useful for choosing the next low-risk validation scheduling experiment.")
    lines.append("- Keep large evals for final reporting; use smaller evals for frequent progress checks.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    eval_times = load_eval_times(Path(args.phase2_json))
    baseline = estimate_schedule(
        total_steps=args.total_steps,
        normal_step_s=args.normal_step_s,
        eval_times=eval_times,
        eval_size=args.baseline_eval_size,
        eval_freq=args.baseline_eval_freq,
        final_eval_size=None,
    )
    candidate = estimate_schedule(
        total_steps=args.total_steps,
        normal_step_s=args.normal_step_s,
        eval_times=eval_times,
        eval_size=args.candidate_eval_size,
        eval_freq=args.candidate_eval_freq,
        final_eval_size=args.final_eval_size,
    )
    summary = {"eval_times": eval_times, "baseline": baseline, "candidate": candidate}

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_markdown(summary), encoding="utf-8")

    json_out = Path(args.json_out) if args.json_out else out_path.with_suffix(".json")
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"wrote={out_path} json={json_out}")


if __name__ == "__main__":
    main()
