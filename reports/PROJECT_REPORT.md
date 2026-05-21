# AgentRolloutProfiler Project Report

## Executive Summary

AgentRolloutProfiler is a profiling-first systems project for Agentic RL
training with WebShop and verl-agent. The original hypothesis was that WebShop
environment interaction might be a major wall-clock bottleneck and could be
optimized through interaction-layer changes such as observation compression,
search caching, or action parser optimization.

The measured result is different and more useful:

> WebShop environment stepping is not the current bottleneck. Validation
> rollout and model-generation/runtime overhead dominate wall-clock time.

The project therefore shifted from "optimize WebShop environment calls" to a
more evidence-backed systems conclusion:

> In this verl-agent + WebShop setup, exploratory Agentic RL runs should reduce
> frequent full validation cost through evaluation scheduling, while preserving
> full eval for final reporting.

## Setup

Case study:

- environment: WebShop
- trainer stack: WarmGiGPO-WebShop using `third_party/verl-agent`
- algorithm context: GiGPO-style Agentic RL
- model family: Qwen2.5-1.5B-Instruct in the WarmGiGPO-WebShop experiments
- hardware context: single A800 server on AutoDL

This repository stays separate from the algorithm project:

- WarmGiGPO-WebShop: SFT warm-start + GiGPO post-training experiments
- AgentRolloutProfiler: profiling, bottleneck analysis, and scheduling
  optimization study

## Phase 1: Baseline Profiling

### Goal

Determine whether WebShop environment calls, action parsing, search, or
observation construction are large enough to justify environment-wrapper
optimization.

### Method

Two evidence sources were used:

1. Existing verl-agent console logs from WarmGiGPO-WebShop RL runs.
2. A live small WebShop eval run with `[ARP_PROFILE]` instrumentation added to
   verl-agent's environment manager and WebShop worker.

The optional instrumentation measured:

- manager reset/step time
- worker reset/step time
- environment step time
- observation formatting/build time
- action type
- observation character count

### Trainer-Level Baseline

From existing RL logs:

| Run | Avg normal step | Avg validation step | Validation testing share |
|---|---:|---:|---:|
| Direct GiGPO | 24.758s | 445.853s | 0.946 |
| SFT + GiGPO | 21.539s | 353.343s | 0.941 |

The dominant validation component is `timing_s/testing`, not reward computation
or environment bookkeeping.

### Environment-Level Profile

From the small `eval8` instrumentation run:

| Event | Count | Avg total_s | Avg env_step_s | Avg obs chars |
|---|---:|---:|---:|---:|
| `manager_reset` | 17 | 0.008 | N/A | 8.000 |
| `worker_reset` | 17 | 0.006 | N/A | 210.765 |
| `manager_step` | 83 | 0.046 | 0.045 | 1122.084 |
| `worker_step` | 83 | 0.044 | N/A | 1252.699 |

Action/search signals from the same run:

- search actions: 3
- unique search queries: 3
- observed repeat rate: 0.000

### Phase 1 Decision

WebShop environment stepping is tens of milliseconds per step, while trainer
steps are tens to hundreds of seconds. This rules out environment step,
observation construction, action parsing, and search caching as the first
optimization target for the measured workload.

Deferred:

- observation compression
- search result cache
- action parser micro-optimization

These ideas are not wrong, but the current profile does not support making them
the main line.

## Phase 2: Validation Scaling

### Goal

Quantify validation wall-clock scaling and compare it against measured WebShop
environment time.

### Method

Timed eval runs were collected for eval8, eval16, and eval64. The same
environment-level instrumentation was used as a cross-check.

### Results

| Eval size | Wall real_s |
|---:|---:|
| 8 | 243.945 |
| 16 | 359.778 |
| 64 | 554.172 |

Environment timing during the same family of eval runs:

| Eval size | manager_step_s | worker_step_s | manager_step count |
|---:|---:|---:|---:|
| 8 | 0.047 | 0.046 | 83 |
| 16 | 0.040 | 0.038 | 163 |
| 64 | 0.037 | 0.035 | 311 |

For eval64, measured WebShop manager-step time is approximately:

```text
311 * 0.037s = 11.5s
```

But the total eval64 wall time is:

```text
554.172s
```

Thus environment stepping accounts for only a small part of wall-clock
validation cost.

### Phase 2 Decision

The relevant optimization target is validation/runtime scheduling rather than
WebShop environment internals.

Likely contributors to the non-environment cost:

- model loading/startup overhead
- Ray/vLLM orchestration
- rollout generation
- prompt prefill and sampling
- validation episode volume

## Phase 3: Evaluation Scheduling

### Goal

Estimate a low-risk scheduling optimization:

- use smaller eval sets for frequent progress monitoring
- preserve full eval64 for final reporting

This changes evaluation cost, not reward design, policy updates, or WebShop
semantics.

### Estimate

Using measured eval runtimes and normal step time of 21.5s:

| Scenario | Steps | Repeated eval | Final eval | Estimated total_s |
|---|---:|---|---:|---:|
| Baseline | 32 | eval64 every 8 steps | 0 | 2904.688 |
| Candidate | 32 | eval8 every 8 steps | eval64 | 2217.952 |

Estimated savings:

```text
absolute: 686.736s
relative: 23.642%
```

### Interpretation

The estimate supports a practical systems recommendation:

> During exploratory Agentic RL runs, use small validation sets for progress
> checks and reserve full validation for final reporting.

This is a wall-clock optimization. It should not be presented as a model-quality
improvement.

## Checkpoint Feasibility

### Why This Matters

To compare final model quality between validation schedules, the actual trained
policy must be saved and evaluated on the same eval64 set.

WarmGiGPO-WebShop scripts currently set:

```text
trainer.save_freq=-1
```

So prior runs did not save final RL actor checkpoints by default.

### Smoke Test

A tiny checkpoint smoke run was added with:

- `trainer.save_freq=1`
- checkpoint output moved to `/root/autodl-tmp`
- Ray/TMP directories moved to `/root/autodl-tmp`

Result:

- checkpoint saving works
- `latest_checkpointed_iteration.txt` was created
- `global_step_2/actor` was created

Observed actor checkpoint size:

```text
219G
```

This makes checkpoint-based quality comparison technically possible but
storage-expensive.

### Direct Eval Probe

Directly using:

```text
global_step_2/actor
```

as:

```text
actor_rollout_ref.model.path
```

failed with:

```text
OSError: Error no file named pytorch_model.bin, model.safetensors,
tf_model.h5, model.ckpt.index or flax_model.msgpack found in directory ...
```

The saved actor is a verl/FSDP checkpoint containing files such as:

```text
model_world_size_1_rank_0.pt
optim_world_size_1_rank_0.pt
extra_state_world_size_1_rank_0.pt
```

It is not a plain HuggingFace-loadable model directory.

### Boundary

The project should not claim final policy-quality equivalence between schedules
unless one of these is implemented and verified:

1. export/convert verl/FSDP actor checkpoint to a HuggingFace-loadable model
2. run a val-only resume path using verl-agent's native trainer checkpoint

Both are out of scope for the current lightweight scheduling study.

## Final Conclusions

1. WebShop environment interaction was measured and ruled out as the primary
   bottleneck for this setup.
2. Validation/runtime overhead dominates exploratory Agentic RL wall-clock cost.
3. Eval-size scheduling is a better first optimization than WebShop environment
   compression/cache/parser work.
4. A measured schedule estimate suggests about 23.6% wall-clock reduction for a
   32-step exploratory run when replacing repeated eval64 with repeated eval8
   plus final eval64.
5. RL checkpoint saving is feasible but expensive; direct eval of saved actor
   checkpoints is not currently supported through `actor_rollout_ref.model.path`.

## Recommended Stopping Point

This project is complete as a profiling and systems-diagnosis project.

The strongest defensible claim is:

> Built a profiling pipeline for verl-agent + WebShop Agentic RL, ruled out
> environment stepping as the bottleneck, quantified validation scaling, and
> proposed an evaluation-scheduling optimization estimated to reduce exploratory
> training wall-clock by about 23.6%, with checkpoint feasibility and evaluation
> boundaries verified.

## Future Work

Optional extensions:

- implement checkpoint export from verl/FSDP actor state to HuggingFace format
- verify val-only resume evaluation for trainer checkpoints
- measure GPU utilization during validation to separate model generation from
  Ray/vLLM orchestration
- test scheduling optimization in a controlled short RL run after checkpoint
  evaluation is solved
- revisit observation compression or search caching only if a larger workload
  shows environment interaction becoming significant
