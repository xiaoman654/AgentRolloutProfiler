# Phase 3 Eval Schedule Estimate

This report estimates wall-clock savings from changing validation schedule, using measured Phase 2 eval runtimes.

## Measured Eval Runtimes

| Eval size | wall real_s |
|---:|---:|
| 8 | 243.945 |
| 16 | 359.778 |
| 64 | 554.172 |

## Schedule Estimate

| Scenario | total steps | normal step_s | eval size | eval freq | repeated eval runs | final extra eval | estimated total_s |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 32 | 21.500 | 64 | 8 | 4 | 0.000 | 2904.688 |
| candidate | 32 | 21.500 | 8 | 8 | 4 | 554.172 | 2217.952 |

## Estimated Savings

- absolute savings: 686.736s
- relative savings: 23.642%

## Interpretation

- This is an estimate, not a replacement for a controlled training run.
- It is useful for choosing the next low-risk validation scheduling experiment.
- Keep large evals for final reporting; use smaller evals for frequent progress checks.
