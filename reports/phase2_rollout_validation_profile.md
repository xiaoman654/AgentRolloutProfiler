# Phase 2 Rollout and Validation Profile

This report focuses on validation/testing cost, after Phase 1 found that WebShop environment stepping is not the dominant bottleneck.

## Validation Cost Summary

| Log | normal step_s | validation step_s | validation testing_s | wall real_s | non-testing validation_s | testing share | validation rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| `qwen15b_zero_shot_eval16_timed_20260521_103026.log` | N/A | N/A | N/A | N/A | N/A | N/A | 0 |
| `qwen15b_zero_shot_eval16_timed_20260521_103501.log` | N/A | 129.533 | 111.517 | 359.778 | 18.016 | 0.861 | 2 |
| `qwen15b_zero_shot_eval64_timed_20260521_103026.log` | N/A | N/A | N/A | N/A | N/A | N/A | 0 |
| `qwen15b_zero_shot_eval64_timed_20260521_104100.log` | N/A | 554.172 | 554.172 | 554.172 | 0.000 | N/A | 1 |
| `qwen15b_zero_shot_eval8_timed_20260521_103026.log` | N/A | N/A | N/A | N/A | N/A | N/A | 0 |
| `qwen15b_zero_shot_eval8_timed_20260521_103057.log` | N/A | 70.860 | 54.808 | 243.945 | 16.052 | 0.773 | 2 |

## Generation and Length Signals

| Log | gen_s normal | gen_s validation | avg prompt length | avg response length |
|---|---:|---:|---:|---:|
| `qwen15b_zero_shot_eval16_timed_20260521_103026.log` | N/A | N/A | N/A | N/A |
| `qwen15b_zero_shot_eval16_timed_20260521_103501.log` | N/A | 7.261 | 288.000 | 124.000 |
| `qwen15b_zero_shot_eval64_timed_20260521_103026.log` | N/A | N/A | N/A | N/A |
| `qwen15b_zero_shot_eval64_timed_20260521_104100.log` | N/A | N/A | N/A | N/A |
| `qwen15b_zero_shot_eval8_timed_20260521_103026.log` | N/A | N/A | N/A | N/A |
| `qwen15b_zero_shot_eval8_timed_20260521_103057.log` | N/A | 6.778 | 1210.000 | 95.400 |

## Environment Timing Cross-Check

| Log | manager_step_s | worker_step_s | search repeat rate | search total | unique search |
|---|---:|---:|---:|---:|---:|
| `qwen15b_zero_shot_eval16_timed_20260521_103026.log` | N/A | N/A | 0.000 | 0 | 0 |
| `qwen15b_zero_shot_eval16_timed_20260521_103501.log` | 0.040 | 0.038 | 0.000 | 2 | 2 |
| `qwen15b_zero_shot_eval64_timed_20260521_103026.log` | N/A | N/A | 0.000 | 0 | 0 |
| `qwen15b_zero_shot_eval64_timed_20260521_104100.log` | 0.037 | 0.035 | 0.000 | 9 | 9 |
| `qwen15b_zero_shot_eval8_timed_20260521_103026.log` | N/A | N/A | 0.000 | 0 | 0 |
| `qwen15b_zero_shot_eval8_timed_20260521_103057.log` | 0.047 | 0.046 | 0.000 | 1 | 1 |

## Score and Case Counts

| Log | parsed cases | scored cases | nonzero cases | success cases | avg score |
|---|---:|---:|---:|---:|---:|
| `qwen15b_zero_shot_eval16_timed_20260521_103026.log` | 0 | 0 | 0 | 0 | N/A |
| `qwen15b_zero_shot_eval16_timed_20260521_103501.log` | 13 | 13 | 0 | 0 | 0.000 |
| `qwen15b_zero_shot_eval64_timed_20260521_103026.log` | 0 | 0 | 0 | 0 | N/A |
| `qwen15b_zero_shot_eval64_timed_20260521_104100.log` | 28 | 28 | 1 | 1 | 0.357 |
| `qwen15b_zero_shot_eval8_timed_20260521_103026.log` | 0 | 0 | 0 | 0 | N/A |
| `qwen15b_zero_shot_eval8_timed_20260521_103057.log` | 5 | 5 | 0 | 0 | 0.000 |

## Phase 2 Reading Guide

- If `testing share` stays near 1.0, optimization should target validation rollout volume, generation throughput, or evaluation frequency.
- Eval-only logs may not contain `timing_s/testing`; in that case `wall real_s` from shell `time` output is the preferred latency signal.
- If `manager_step_s` and `worker_step_s` remain below 0.1s, WebShop environment stepping is still not the priority.
- If latency scales roughly linearly with eval size, validation batch size/frequency is a direct speed-quality tradeoff.
- If score is unstable at small eval sizes, use small eval only for profiling and keep larger eval for final reporting.
