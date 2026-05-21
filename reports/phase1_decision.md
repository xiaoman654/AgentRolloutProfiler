# Phase 1 Profiling Decision

This note summarizes the first profiling decision for AgentRolloutProfiler.
It combines two sources:

- existing WarmGiGPO-WebShop verl-agent RL logs
- a small AutoDL `eval8` run with optional WebShop environment instrumentation

## Baseline Trainer-Level Timing

The log-based baseline in `reports/baseline_profile.md` shows that normal
training steps take tens of seconds, while validation steps take hundreds of
seconds.

| Run | Avg normal step | Avg validation step | Validation testing share |
|---|---:|---:|---:|
| Direct GiGPO | 24.758s | 445.853s | 0.946 |
| SFT + GiGPO | 21.539s | 353.343s | 0.941 |

The dominant validation metric is `timing_s/testing`, not reward computation or
environment bookkeeping.

## Live WebShop Environment Timing

The AutoDL `eval8` run was instrumented with `[ARP_PROFILE]` events in the
WebShop environment manager and worker.

| Event | Count | Avg total_s | Avg env_step_s | Avg projection_s | Avg format_obs_s | Avg build_text_obs_s | Avg obs chars |
|---|---:|---:|---:|---:|---:|---:|---:|
| `manager_reset` | 17 | 0.008 | N/A | N/A | 0.000 | 0.000 | 8.000 |
| `worker_reset` | 17 | 0.006 | N/A | N/A | N/A | N/A | 210.765 |
| `manager_step` | 83 | 0.046 | 0.045 | 0.000 | 0.000 | 0.000 | 1122.084 |
| `worker_step` | 83 | 0.044 | N/A | N/A | N/A | N/A | 1252.699 |

The measured WebShop step path is roughly 40-50 ms per environment step. This is
small compared with the 20-25s normal trainer steps and the 350-450s validation
steps observed in the baseline logs.

## Action and Search Signals

The same small eval run produced:

| Action type | Count |
|---|---:|
| `click` | 5 |
| `search` | 3 |

Search query repetition:

- total search actions: 3
- unique search queries: 3
- observed repeat rate: 0.000

This does not support search caching as a primary optimization yet. The sample is
small, so this is not a final claim about all workloads, but it is enough to keep
cache work out of the critical path for now.

## Decision

Phase 1 rules out WebShop environment stepping as the immediate bottleneck.

Near-term priorities:

1. Profile rollout generation and validation more precisely.
2. Separate model generation, validation rollout count, and evaluation sampling
   effects.
3. Keep WebShop environment compression/cache/parser work as secondary ideas
   unless a larger workload shows different evidence.

Do not make Phase 2 a WebShop kernel or environment-wrapper optimization project
yet. The current evidence points to model-side rollout and validation cost.

## Implications for Phase 2

Recommended next experiment:

- instrument or parse validation runs to split `timing_s/testing` into number of
  eval episodes, average rollout length, generation time, and environment time
- run the same profiler on `eval8`, `eval16`, and `eval64` if available
- compare score drift and latency only after the bottleneck is localized

Deferred optimizations:

- observation compression: low priority because `build_text_obs_s` is near zero
  and average observations are about 1.1k-1.3k characters in this eval
- search cache: low priority because observed search repetition is zero
- action parser optimization: low priority because `projection_s` is near zero

