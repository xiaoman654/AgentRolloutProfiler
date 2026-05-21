# Phase 3 Plan: Evaluation Scheduling Optimization

Phase 1 and Phase 2 ruled out WebShop environment stepping as the dominant
bottleneck. The lowest-risk optimization target is therefore validation
scheduling.

## Hypothesis

Frequent full-size validation is unnecessarily expensive during exploratory RL
runs. Smaller validation sets can be used for progress monitoring, while full
eval64 remains reserved for final reporting.

## Current Estimate

Using measured Phase 2 runtimes:

| Eval size | wall real_s |
|---:|---:|
| 8 | 243.945 |
| 16 | 359.778 |
| 64 | 554.172 |

For a 32-step run with normal step time set to 21.5s:

| Schedule | Repeated eval | Final eval | Estimated total_s |
|---|---:|---:|---:|
| Baseline | eval64 every 8 steps | none | 2904.688 |
| Candidate | eval8 every 8 steps | eval64 | 2217.952 |

Estimated savings:

- absolute: 686.736s
- relative: 23.642%

## Controlled Experiment

Run two short RL jobs with the same model, training data, seed, and RL
hyperparameters:

1. Baseline schedule: `VAL_FILE=text_eval64/test.parquet`, `trainer.test_freq=8`
2. Candidate schedule: `VAL_FILE=text_eval8/test.parquet`, `trainer.test_freq=8`

After the candidate run, run a separate eval64 for final score reporting.

Compare:

- total wall-clock time
- number of validation events
- final eval64 success rate and task score
- whether eval8 progress signal is directionally useful

## Non-Goals

- Do not change GiGPO loss, reward, or KL settings.
- Do not change WebShop internals.
- Do not claim score improvement from scheduling alone.

The expected benefit is wall-clock reduction during exploratory training, not a
better policy.

