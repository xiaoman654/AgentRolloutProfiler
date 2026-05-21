# Phase 2 Decision

This note summarizes the timed validation scaling run.

## Inputs

Timed eval logs were collected on the AutoDL server using Bash `time` and
WebShop environment instrumentation.

Useful timed logs:

| Eval size | Log | wall real_s |
|---:|---|---:|
| 8 | `qwen15b_zero_shot_eval8_timed_20260521_103057.log` | 243.945 |
| 16 | `qwen15b_zero_shot_eval16_timed_20260521_103501.log` | 359.778 |
| 64 | `qwen15b_zero_shot_eval64_timed_20260521_104100.log` | 554.172 |

Earlier empty timed logs from the missing `/usr/bin/time` attempt are ignored by
the reporting script.

## Environment Timing Remains Small

| Eval size | manager_step_s | worker_step_s | manager_step count |
|---:|---:|---:|---:|
| 8 | 0.047 | 0.046 | 83 |
| 16 | 0.040 | 0.038 | 163 |
| 64 | 0.037 | 0.035 | 311 |

Even for eval64, the measured WebShop manager step path is roughly
`311 * 0.037 = 11.5s`, while wall-clock runtime is about `554s`. This again
rules out WebShop environment stepping as the main bottleneck.

## Validation Cost Pattern

The measured wall time grows with eval size, but not perfectly linearly:

- eval8: 243.945s
- eval16: 359.778s, about 1.48x eval8
- eval64: 554.172s, about 2.27x eval8

This suggests a fixed startup/model-loading overhead plus rollout generation
cost. Small eval runs are useful for quick profiling, but they overrepresent
startup overhead. Eval64 is still the better anchor for final wall-clock claims.

## Decision

Phase 2 should not optimize WebShop search/cache/parser paths first.

Next priority:

1. Split eval wall time into startup/model-loading time versus active rollout
   time.
2. Measure GPU utilization during eval to see whether generation is saturated
   or waiting on CPU/Ray scheduling.
3. Test validation frequency/size tradeoffs in the training loop, because
   validation is expensive relative to normal training steps.

## Candidate Phase 3 Optimization

The safest first optimization is not a benchmark-kernel change. It is a training
schedule optimization:

- keep `eval64` for final reporting
- use smaller eval such as `eval8` or `eval16` for frequent progress checks
- reduce validation frequency during exploratory RL runs

This is a low-risk systems optimization because it changes when and how much to
evaluate, not the policy, reward, or WebShop environment.

