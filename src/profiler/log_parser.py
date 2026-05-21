"""Parse verl-agent console logs for timing and rollout behavior metrics."""

from __future__ import annotations

import re
import json
from pathlib import Path
from typing import Iterable

from .schema import EnvProfileEvent, LogRuntime, ResponseCase, StepMetrics


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
PREFIX_RE = re.compile(r"^\(TaskRunner pid=\d+\)\s*")
STEP_RE = re.compile(r"\bstep:(\d+)\b")
SCORE_RE = re.compile(r"\[text\]\[score\]\s*(-?\d+(?:\.\d+)?)")
ACTION_RE = re.compile(r"<action>(.*?)</action>", re.DOTALL)
ACTION_TYPE_RE = re.compile(r"^\s*([a-zA-Z_ ]+)\[")
PROFILE_MARKER = "[ARP_PROFILE]"
TIME_P_RE = re.compile(r"^(real|user|sys)\s+(\d+(?:\.\d+)?)\s*$")
BASH_TIME_RE = re.compile(r"^(real|user|sys)\s+(\d+)m(\d+(?:\.\d+)?)s\s*$")


def clean_line(line: str) -> str:
    line = ANSI_RE.sub("", line).rstrip("\n")
    return PREFIX_RE.sub("", line)


def parse_step_metrics(path: Path) -> list[StepMetrics]:
    rows: list[StepMetrics] = []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = clean_line(raw)
            step_match = STEP_RE.search(line)
            if not step_match:
                continue
            metrics = parse_metric_segments(line)
            if metrics:
                rows.append(StepMetrics(source_log=str(path), step=int(step_match.group(1)), metrics=metrics))
    return rows


def parse_metric_segments(line: str) -> dict[str, float]:
    """Parse `key:value` metrics from verl-agent's `step:* - key:value` lines."""

    metrics: dict[str, float] = {}
    for segment in line.split(" - "):
        if ":" not in segment:
            continue
        key, value = segment.rsplit(":", 1)
        key = key.strip()
        if key == "step" or not key:
            continue
        try:
            metrics[key] = float(value.strip())
        except ValueError:
            continue
    return metrics


def extract_action(response: str) -> str:
    match = ACTION_RE.search(response)
    if not match:
        return ""
    return " ".join(match.group(1).split())


def action_type(action: str) -> str:
    match = ACTION_TYPE_RE.match(action)
    if not match:
        return "unknown" if action else ""
    return match.group(1).strip().lower().replace(" ", "_")


def parse_response_cases(path: Path) -> list[ResponseCase]:
    cases: list[ResponseCase] = []
    current: ResponseCase | None = None
    section: str | None = None

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = clean_line(raw)

            if "[text][prompt]" in line:
                if current is not None:
                    current.action = extract_action(current.response)
                    current.action_type = action_type(current.action)
                    cases.append(current)
                current = ResponseCase(source_log=str(path), prompt=line.split("[text][prompt]", 1)[1].strip())
                section = "prompt"
                continue

            if current is None:
                continue

            if "[text][response]" in line:
                current.response = line.split("[text][response]", 1)[1].strip()
                section = "response"
                continue

            score_match = SCORE_RE.search(line)
            if score_match:
                current.score = float(score_match.group(1))
                current.action = extract_action(current.response)
                current.action_type = action_type(current.action)
                cases.append(current)
                current = None
                section = None
                continue

            if "test_gen_batch meta info" in line or "validation generation end" in line:
                continue

            if section == "prompt":
                current.prompt += "\n" + line
            elif section == "response":
                current.response += "\n" + line

    if current is not None:
        current.action = extract_action(current.response)
        current.action_type = action_type(current.action)
        cases.append(current)
    return cases


def parse_profile_events(path: Path) -> list[EnvProfileEvent]:
    """Parse optional `[ARP_PROFILE] {...}` JSON lines emitted by env instrumentation."""

    events: list[EnvProfileEvent] = []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = clean_line(raw)
            if PROFILE_MARKER not in line:
                continue
            payload_text = line.split(PROFILE_MARKER, 1)[1].strip()
            try:
                payload = json.loads(payload_text)
            except json.JSONDecodeError:
                continue
            event_name = str(payload.get("event", "unknown"))
            events.append(EnvProfileEvent(source_log=str(path), event=event_name, payload=payload))
    return events


def parse_time_p_runtime(path: Path) -> LogRuntime:
    """Parse shell timing output if it was captured by tee.

    Supports both POSIX `time -p` lines such as `real 73.45` and Bash built-in
    `time` lines such as `real 1m13.450s`.
    """

    values: dict[str, float] = {}
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = clean_line(raw).strip()
            match = TIME_P_RE.match(line)
            if match:
                values[match.group(1)] = float(match.group(2))
                continue
            bash_match = BASH_TIME_RE.match(line)
            if bash_match:
                minutes = int(bash_match.group(2))
                seconds = float(bash_match.group(3))
                values[bash_match.group(1)] = minutes * 60.0 + seconds
    return LogRuntime(
        source_log=str(path),
        real_s=values.get("real"),
        user_s=values.get("user"),
        sys_s=values.get("sys"),
    )


def iter_existing_logs(patterns: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        matched = sorted(Path().glob(pattern)) if not Path(pattern).is_absolute() else sorted(Path(pattern).parent.glob(Path(pattern).name))
        paths.extend(path for path in matched if path.is_file())
    return paths
