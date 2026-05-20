# Project Plan

Project name: AgentRolloutProfiler  
Initial case study: WebShop agent rollouts  
Primary objective: profile and optimize the agent-environment interaction layer
without changing the benchmark kernel or the RL trainer.

## Motivation

WarmGiGPO-WebShop showed that validation and rollout-heavy steps can dominate
wall-clock time. This project turns that observation into a standalone systems
project: measure the interaction-layer bottleneck, then test non-invasive
optimizations.

## Phase 1: Baseline Profiling

Goal: produce a trustworthy latency and behavior breakdown before changing
anything.

Inputs:

- existing verl-agent RL logs
- existing train/eval settings from WarmGiGPO-WebShop
- optional future live WebShop wrapper instrumentation

Metrics:

- `timing_s/gen`
- `timing_s/reward`
- `timing_s/old_log_prob`
- `timing_s/ref`
- `timing_s/adv`
- `timing_s/update_actor`
- `timing_s/testing`
- `timing_s/step`
- prompt length mean/max/clip ratio
- response length mean/max/clip ratio
- action type distribution
- search query repetition rate
- validation-step share of total runtime

Deliverable:

```text
reports/baseline_profile.md
```

Decision after Phase 1:

- If prompt length is large and correlated with generation/testing cost, test
  observation compression.
- If search query repetition is high, test search cache.
- If parser time is visible in live profiling, test lightweight action parsing.
- If none of the above is significant, document negative findings.

## Phase 2: Non-Invasive Optimizations

Pick one or two optimizations based on Phase 1 results.

Candidate A: observation compression

- reduce redundant product text
- keep product ids, names, prices, attributes, and valid actions
- compare prompt length, latency, and score drift

Candidate B: search cache

- cache deterministic search observations by normalized query
- measure cache upper bound first using query repetition
- compare env-step latency and throughput

Candidate C: action parser lightweight path

- precompile regexes
- cache action type parsing
- keep this as a secondary optimization unless profiling says otherwise

Required evaluation:

- average prompt length change
- average step latency change
- rollout throughput change
- success/task-score drift

## Phase 3: Parallel Env-Stepping Prototype

Goal: build a standalone throughput prototype, not a full async trainer.

Scope:

- run multiple independent environment instances concurrently
- measure throughput against a synchronous baseline
- avoid policy staleness and trainer integration in the first version

Out of scope for the first version:

- fully async GiGPO trainer
- partial rollout updates
- modifying verl-agent trainer internals

## Relationship to WarmGiGPO-WebShop

WarmGiGPO-WebShop remains the algorithm project. This repository can use it as a
baseline source, but should not mix algorithm claims with systems optimization
claims.

