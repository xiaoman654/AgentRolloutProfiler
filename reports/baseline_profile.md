# Baseline Rollout Profile

Generated from verl-agent console logs.

## Log Summary

| Log | parsed step lines | normal rows | validation rows | avg normal step_s | avg validation step_s | validation testing share |
|---|---:|---:|---:|---:|---:|---:|
| `D:\webshop\logs\rl\qwen15b_gigpo_medium_128_64_20260518_145752.log` | 33 | 28 | 4 | 24.758 | 445.853 | 0.946 |
| `D:\webshop\logs\rl\qwen15b_sft_verl_gigpo_medium_128_64_20260518_141425.log` | 33 | 28 | 4 | 21.539 | 353.343 | 0.941 |

## Overall Timing Averages

| Metric | All rows | Normal rows | Validation rows |
|---|---:|---:|---:|
| `timing_s/gen` | 7.794 | 7.815 | 7.648 |
| `timing_s/reward` | 0.017 | 0.017 | 0.018 |
| `timing_s/old_log_prob` | 2.143 | 2.154 | 2.070 |
| `timing_s/ref` | 6.057 | 6.090 | 5.825 |
| `timing_s/adv` | 0.008 | 0.008 | 0.009 |
| `timing_s/update_actor` | 7.037 | 7.060 | 6.882 |
| `timing_s/testing` | 377.140 | N/A | 377.140 |
| `timing_s/step` | 70.205 | 23.148 | 399.598 |

## Overall Length Averages

| Metric | Average |
|---|---:|
| `prompt_length/mean` | 1042.248 |
| `prompt_length/max` | 2154.078 |
| `prompt_length/clip_ratio` | 0.000 |
| `response_length/mean` | 55.770 |
| `response_length/max` | 97.953 |
| `response_length/clip_ratio` | 0.058 |

## Per-Log Timing and Length

### `qwen15b_gigpo_medium_128_64_20260518_145752.log`

| Metric | Normal rows | Validation rows |
|---|---:|---:|
| `timing_s/gen` | 9.075 | 8.875 |
| `timing_s/reward` | 0.016 | 0.017 |
| `timing_s/old_log_prob` | 2.195 | 2.130 |
| `timing_s/ref` | 6.213 | 5.946 |
| `timing_s/adv` | 0.008 | 0.009 |
| `timing_s/update_actor` | 7.244 | 7.043 |
| `timing_s/testing` | N/A | 421.827 |
| `timing_s/step` | 24.758 | 445.853 |
| `prompt_length/mean` | 1045.411 | 1069.757 |
| `prompt_length/max` | 2108.000 | 2280.750 |
| `prompt_length/clip_ratio` | 0.000 | 0.000 |
| `response_length/mean` | 88.462 | 83.254 |
| `response_length/max` | 127.500 | 128.000 |
| `response_length/clip_ratio` | 0.118 | 0.071 |

### `qwen15b_sft_verl_gigpo_medium_128_64_20260518_141425.log`

| Metric | Normal rows | Validation rows |
|---|---:|---:|
| `timing_s/gen` | 6.554 | 6.421 |
| `timing_s/reward` | 0.017 | 0.018 |
| `timing_s/old_log_prob` | 2.113 | 2.010 |
| `timing_s/ref` | 5.966 | 5.705 |
| `timing_s/adv` | 0.008 | 0.010 |
| `timing_s/update_actor` | 6.875 | 6.721 |
| `timing_s/testing` | N/A | 332.452 |
| `timing_s/step` | 21.539 | 353.343 |
| `prompt_length/mean` | 1039.204 | 1013.897 |
| `prompt_length/max` | 2181.250 | 2159.750 |
| `prompt_length/clip_ratio` | 0.000 | 0.000 |
| `response_length/mean` | 23.690 | 23.992 |
| `response_length/max` | 67.714 | 72.750 |
| `response_length/clip_ratio` | 0.004 | 0.007 |

## Action Type Distribution

| Action type | Count |
|---|---:|
| `click` | 176 |
| `search` | 50 |
| `unknown` | 7 |

## Search Query Repetition

- total search actions: 50
- unique search queries: 50
- observed repeat rate: 0.000

## Parsed Case Scores

- parsed cases: 233
- scored cases: 233
- nonzero-score cases: 22
- success-score-10 cases: 22

## Phase 1 Decision Notes

- Use this report to decide whether observation compression, search cache, or parser optimization is worth testing.
- Do not treat speed improvements as valid unless task score drift is measured in a later controlled run.
