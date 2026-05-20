# AgentRolloutProfiler

AgentRolloutProfiler is a profiling-first systems project for multi-step LLM
agent rollouts. The first target environment is WebShop, motivated by the
WarmGiGPO-WebShop experiments where validation and environment interaction
dominated wall-clock time.

This repository is intentionally separate from the algorithm project:

- WarmGiGPO-WebShop: SFT warm-start and GiGPO post-training study.
- AgentRolloutProfiler: rollout interaction-layer profiling and optimization.

## Phase 1 Goal

Phase 1 does not modify WebShop, verl-agent, or the GiGPO trainer. It measures
where time is spent and produces a baseline profile:

- generation time
- reference log-prob time
- actor update time
- validation/testing time
- total step time
- response length and clipping
- prompt length and clipping
- action type distribution from logged responses
- search query repetition from logged actions

The first runnable path is log-based profiling using existing verl-agent logs.
Live environment instrumentation can be added after the baseline is clear.

## Initial Layout

```text
configs/
  webshop_profile.yaml

scripts/
  analyze_verl_log_timing.py

src/
  profiler/
    log_parser.py
    report.py
    schema.py
    timers.py

reports/
  baseline_profile.md
```

## Quick Start

From this repository:

```bash
python scripts/analyze_verl_log_timing.py \
  --logs /path/to/WarmGiGPO-WebShop/logs/rl/*.log \
  --out reports/baseline_profile.md \
  --json-out reports/baseline_profile.json
```

The markdown report is for reading. The JSON report is for later plotting,
regression checks, and comparing optimization variants.

On the AutoDL server, the expected project paths are:

```text
/root/autodl-fs/AgentRolloutProfiler
/root/autodl-fs/WarmGiGPO-WebShop
```

The first phase can reuse the existing `verl-agent-webshop` conda environment.

## Project Boundary

This project should stay profiling-driven:

1. Measure first.
2. Choose at most one or two non-invasive optimizations.
3. Report both speed and score drift.
4. Avoid modifying the async trainer loop until a standalone throughput
   prototype proves value.
