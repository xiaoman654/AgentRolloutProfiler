# Phase 2 Rollout and Validation Profile

This report focuses on validation/testing cost, after Phase 1 found that WebShop environment stepping is not the dominant bottleneck.

## Validation Cost Summary

| Log | normal step_s | validation step_s | validation testing_s | non-testing validation_s | testing share | validation rows |
|---|---:|---:|---:|---:|---:|---:|
| `qwen15b_gigpo_medium_128_64_20260518_145752.log` | 24.758 | 445.853 | 421.827 | 24.026 | 0.946 | 4 |
| `qwen15b_sft_verl_gigpo_medium_128_64_20260518_141425.log` | 21.539 | 353.343 | 332.452 | 20.891 | 0.941 | 4 |

## Generation and Length Signals

| Log | gen_s normal | gen_s validation | avg prompt length | avg response length |
|---|---:|---:|---:|---:|
| `qwen15b_gigpo_medium_128_64_20260518_145752.log` | 9.075 | 8.875 | 1048.454 | 87.811 |
| `qwen15b_sft_verl_gigpo_medium_128_64_20260518_141425.log` | 6.554 | 6.421 | 1036.041 | 23.728 |

## Environment Timing Cross-Check

| Log | manager_step_s | worker_step_s | search repeat rate | search total | unique search |
|---|---:|---:|---:|---:|---:|
| `qwen15b_gigpo_medium_128_64_20260518_145752.log` | N/A | N/A | 0.000 | 25 | 25 |
| `qwen15b_sft_verl_gigpo_medium_128_64_20260518_141425.log` | N/A | N/A | 0.000 | 25 | 25 |

## Score and Case Counts

| Log | parsed cases | scored cases | nonzero cases | success cases | avg score |
|---|---:|---:|---:|---:|---:|
| `qwen15b_gigpo_medium_128_64_20260518_145752.log` | 134 | 134 | 3 | 3 | 0.224 |
| `qwen15b_sft_verl_gigpo_medium_128_64_20260518_141425.log` | 99 | 99 | 19 | 19 | 1.919 |

## Phase 2 Reading Guide

- If `testing share` stays near 1.0, optimization should target validation rollout volume, generation throughput, or evaluation frequency.
- If `manager_step_s` and `worker_step_s` remain below 0.1s, WebShop environment stepping is still not the priority.
- If latency scales roughly linearly with eval size, validation batch size/frequency is a direct speed-quality tradeoff.
- If score is unstable at small eval sizes, use small eval only for profiling and keep larger eval for final reporting.
