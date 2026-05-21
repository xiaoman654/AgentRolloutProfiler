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

Current Phase 1 finding: live WebShop environment profiling measured
environment steps at roughly 40-50 ms, while trainer logs show normal steps in
the 20s range and validation steps in the 350-450s range. The immediate
bottleneck is therefore not WebShop environment stepping; the next focus is
rollout generation and validation profiling. See `reports/phase1_decision.md`.

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

For Phase 2 validation-specific analysis:

```bash
python scripts/build_phase2_validation_report.py \
  --logs /path/to/WarmGiGPO-WebShop/logs/eval/*.log \
  --out reports/phase2_rollout_validation_profile.md \
  --json-out reports/phase2_rollout_validation_profile.json
```

For Phase 3 evaluation-schedule estimates:

```bash
python scripts/estimate_eval_schedule_savings.py \
  --phase2-json reports/phase2_rollout_validation_profile.json \
  --out reports/phase3_eval_schedule_estimate.md \
  --json-out reports/phase3_eval_schedule_estimate.json
```

For the optional checkpoint smoke test, see:

```text
docs/server_phase3_checkpoint_smoke.md
```

To test whether a saved actor checkpoint can be evaluated directly, see:

```text
docs/server_phase3_checkpoint_eval_probe.md
```

## Optional Env-Level Instrumentation

Log-based profiling can only see trainer-level metrics. To profile WebShop
environment calls, apply the optional patch to the WarmGiGPO-WebShop
`third_party/verl-agent` checkout:

```bash
cd /root/autodl-fs/AgentRolloutProfiler
bash scripts/apply_verl_agent_env_profile_patch.sh
```

Then run a small eval or RL job with `tee` logging. The log will contain
`[ARP_PROFILE]` JSON lines for WebShop worker and manager events. Re-run
`scripts/analyze_verl_log_timing.py` on that log to add environment-level timing
tables to the report.

See `docs/env_instrumentation.md` for details.

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
