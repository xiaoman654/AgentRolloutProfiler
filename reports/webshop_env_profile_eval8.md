# Baseline Rollout Profile

Generated from verl-agent console logs.

## Log Summary

| Log | parsed step lines | normal rows | validation rows | avg normal step_s | avg validation step_s | validation testing share |
|---|---:|---:|---:|---:|---:|---:|
| `logs/webshop_profile/qwen15b_zero_shot_eval8_env_profile_20260521_093739.log` | 2 | 0 | 1 | N/A | 70.389 | 0.770 |

## Overall Timing Averages

| Metric | All rows | Normal rows | Validation rows |
|---|---:|---:|---:|
| `timing_s/gen` | 6.828 | N/A | 6.828 |
| `timing_s/reward` | 0.003 | N/A | 0.003 |
| `timing_s/old_log_prob` | 1.858 | N/A | 1.858 |
| `timing_s/ref` | 5.627 | N/A | 5.627 |
| `timing_s/adv` | 0.003 | N/A | 0.003 |
| `timing_s/update_actor` | 1.884 | N/A | 1.884 |
| `timing_s/testing` | 54.183 | N/A | 54.183 |
| `timing_s/step` | 70.389 | N/A | 70.389 |

## Overall Length Averages

| Metric | Average |
|---|---:|
| `prompt_length/mean` | 1210.000 |
| `prompt_length/max` | 2512.000 |
| `prompt_length/clip_ratio` | 0.000 |
| `response_length/mean` | 95.400 |
| `response_length/max` | 128.000 |
| `response_length/clip_ratio` | 0.200 |

## Per-Log Timing and Length

### `qwen15b_zero_shot_eval8_env_profile_20260521_093739.log`

| Metric | Normal rows | Validation rows |
|---|---:|---:|
| `timing_s/gen` | N/A | 6.828 |
| `timing_s/reward` | N/A | 0.003 |
| `timing_s/old_log_prob` | N/A | 1.858 |
| `timing_s/ref` | N/A | 5.627 |
| `timing_s/adv` | N/A | 0.003 |
| `timing_s/update_actor` | N/A | 1.884 |
| `timing_s/testing` | N/A | 54.183 |
| `timing_s/step` | N/A | 70.389 |
| `prompt_length/mean` | N/A | 1210.000 |
| `prompt_length/max` | N/A | 2512.000 |
| `prompt_length/clip_ratio` | N/A | 0.000 |
| `response_length/mean` | N/A | 95.400 |
| `response_length/max` | N/A | 128.000 |
| `response_length/clip_ratio` | N/A | 0.200 |

## Action Type Distribution

| Action type | Count |
|---|---:|
| `click` | 5 |
| `search` | 3 |

## Search Query Repetition

- total search actions: 3
- unique search queries: 3
- observed repeat rate: 0.000

## Parsed Case Scores

- parsed cases: 8
- scored cases: 8
- nonzero-score cases: 0
- success-score-10 cases: 0

## Environment-Level Profile Events

| Event | Count | avg total_s | avg env_step_s | avg projection_s | avg format_obs_s | avg build_text_obs_s | avg obs chars |
|---|---:|---:|---:|---:|---:|---:|---:|
| `manager_reset` | 17 | 0.008 | N/A | N/A | 0.000 | 0.000 | 8.000 |
| `worker_reset` | 17 | 0.006 | N/A | N/A | N/A | N/A | 210.765 |
| `manager_step` | 83 | 0.046 | 0.045 | 0.000 | 0.000 | 0.000 | 1122.084 |
| `worker_step` | 83 | 0.044 | N/A | N/A | N/A | N/A | 1252.699 |

## Phase 1 Decision Notes

- Use this report to decide whether observation compression, search cache, or parser optimization is worth testing.
- Do not treat speed improvements as valid unless task score drift is measured in a later controlled run.
