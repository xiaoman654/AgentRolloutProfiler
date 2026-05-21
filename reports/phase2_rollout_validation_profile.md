# Phase 2 Rollout and Validation Profile

This report focuses on validation/testing cost, after Phase 1 found that WebShop environment stepping is not the dominant bottleneck.

## Validation Cost Summary

| Log | normal step_s | validation step_s | validation testing_s | wall real_s | non-testing validation_s | testing share | validation rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| `qwen15b_zero_shot_eval16_20260521_100344.log` | N/A | 127.756 | 111.765 | N/A | 15.991 | 0.875 | 2 |
| `qwen15b_zero_shot_eval64_20260521_100937.log` | N/A | N/A | N/A | N/A | N/A | N/A | 1 |
| `qwen15b_zero_shot_eval8_20260521_095937.log` | N/A | 73.016 | 56.589 | N/A | 16.427 | 0.775 | 2 |

## Generation and Length Signals

| Log | gen_s normal | gen_s validation | avg prompt length | avg response length |
|---|---:|---:|---:|---:|
| `qwen15b_zero_shot_eval16_20260521_100344.log` | N/A | 7.335 | 288.000 | 124.000 |
| `qwen15b_zero_shot_eval64_20260521_100937.log` | N/A | N/A | N/A | N/A |
| `qwen15b_zero_shot_eval8_20260521_095937.log` | N/A | 6.767 | 1210.000 | 95.400 |

## Environment Timing Cross-Check

| Log | manager_step_s | worker_step_s | search repeat rate | search total | unique search |
|---|---:|---:|---:|---:|---:|
| `qwen15b_zero_shot_eval16_20260521_100344.log` | 0.040 | 0.038 | 0.000 | 2 | 2 |
| `qwen15b_zero_shot_eval64_20260521_100937.log` | 0.037 | 0.036 | 0.000 | 2 | 2 |
| `qwen15b_zero_shot_eval8_20260521_095937.log` | 0.044 | 0.043 | 0.000 | 5 | 5 |

## Score and Case Counts

| Log | parsed cases | scored cases | nonzero cases | success cases | avg score |
|---|---:|---:|---:|---:|---:|
| `qwen15b_zero_shot_eval16_20260521_100344.log` | 12 | 12 | 0 | 0 | 0.000 |
| `qwen15b_zero_shot_eval64_20260521_100937.log` | 25 | 25 | 0 | 0 | 0.000 |
| `qwen15b_zero_shot_eval8_20260521_095937.log` | 7 | 7 | 0 | 0 | 0.000 |

## Phase 2 Reading Guide

- If `testing share` stays near 1.0, optimization should target validation rollout volume, generation throughput, or evaluation frequency.
- Eval-only logs may not contain `timing_s/testing`; in that case `wall real_s` from `/usr/bin/time -p` is the preferred latency signal.
- If `manager_step_s` and `worker_step_s` remain below 0.1s, WebShop environment stepping is still not the priority.
- If latency scales roughly linearly with eval size, validation batch size/frequency is a direct speed-quality tradeoff.
- If score is unstable at small eval sizes, use small eval only for profiling and keep larger eval for final reporting.
