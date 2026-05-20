# WebShop Env-Level Instrumentation

This document describes the optional profiling patch for collecting
environment-level timing from verl-agent WebShop runs.

## What It Measures

The patch emits JSON lines prefixed with:

```text
[ARP_PROFILE]
```

Events:

- `worker_reset`: WebShop worker reset and available-action extraction.
- `worker_step`: raw `WebAgentTextEnv.step`, available-action extraction, and
  reward rewriting.
- `manager_reset`: vector env reset, task extraction, observation formatting,
  and prompt construction.
- `manager_step`: action projection, vector env step, observation formatting,
  and prompt construction.

These events are parsed by:

```bash
python scripts/analyze_verl_log_timing.py --logs ... --out reports/baseline_profile.md
```

## Why This Is a Patch

Phase 1 should avoid changing the RL trainer. The patch only adds timing prints
around the WebShop env wrapper path and leaves GiGPO optimization unchanged.

## Server Usage

From the server:

```bash
cd /root/autodl-fs/AgentRolloutProfiler
bash scripts/apply_verl_agent_env_profile_patch.sh
```

Then run the same WarmGiGPO-WebShop evaluation or RL command with `tee` logging.
The resulting log will include `[ARP_PROFILE]` lines and can be analyzed by this
project.

## Caution

The patch prints one JSON line per env manager/worker step, so logs will grow.
Use it for profiling runs, not for every long experiment.

