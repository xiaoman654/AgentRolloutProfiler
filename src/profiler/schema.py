"""Data structures used by the profiling reports."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StepMetrics:
    """Metrics parsed from one verl-agent `step:*` console line."""

    source_log: str
    step: int
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass
class ResponseCase:
    """Prompt/response/score case parsed from validation log output."""

    source_log: str
    prompt: str = ""
    response: str = ""
    score: float | None = None
    action: str = ""
    action_type: str = ""

