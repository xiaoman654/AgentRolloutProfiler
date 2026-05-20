"""Small timing utilities for future live profiling instrumentation."""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class TimerStore:
    """Collect named wall-clock durations."""

    durations: dict[str, list[float]] = field(default_factory=dict)

    def add(self, name: str, seconds: float) -> None:
        self.durations.setdefault(name, []).append(seconds)

    def summary(self) -> dict[str, dict[str, float]]:
        result: dict[str, dict[str, float]] = {}
        for name, values in self.durations.items():
            total = sum(values)
            result[name] = {
                "count": float(len(values)),
                "total_s": total,
                "mean_s": total / len(values) if values else 0.0,
            }
        return result


@contextmanager
def timed(store: TimerStore, name: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        store.add(name, time.perf_counter() - start)

