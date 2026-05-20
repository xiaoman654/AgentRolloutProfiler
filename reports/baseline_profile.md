# Baseline Rollout Profile

Generated from verl-agent console logs.

## Log Summary

| Log | parsed step lines | normal rows | validation rows | avg normal step_s | avg validation step_s | validation testing share |
|---|---:|---:|---:|---:|---:|---:|
| `D:\webshop\logs\rl\qwen15b_gigpo_medium_128_64_20260518_145752.log` | 33 | 28 | 4 | 24.758 | 445.853 | 0.946 |
| `D:\webshop\logs\rl\qwen15b_sft_verl_gigpo_medium_128_64_20260518_141425.log` | 33 | 28 | 4 | 21.539 | 353.343 | 0.941 |

## Timing Averages

| Metric | Average |
|---|---:|
| `timing_s/gen` | 7.794 |
| `timing_s/reward` | 0.017 |
| `timing_s/old_log_prob` | 2.143 |
| `timing_s/ref` | 6.057 |
| `timing_s/adv` | 0.008 |
| `timing_s/update_actor` | 7.037 |
| `timing_s/testing` | 377.140 |
| `timing_s/step` | 70.205 |

## Length Averages

| Metric | Average |
|---|---:|
| `prompt_length/mean` | 1042.248 |
| `prompt_length/max` | 2154.078 |
| `prompt_length/clip_ratio` | 0.000 |
| `response_length/mean` | 55.770 |
| `response_length/max` | 97.953 |
| `response_length/clip_ratio` | 0.058 |

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
