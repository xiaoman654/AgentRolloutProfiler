# Phase 3 Checkpoint Eval Probe Result

## Question

Can a saved verl-agent actor checkpoint directory be used directly as
`actor_rollout_ref.model.path` in a val-only WebShop eval run?

Tested actor path:

```text
/root/autodl-tmp/AgentRolloutProfiler/checkpoints/checkpoint_smoke_tiny/global_step_2/actor
```

## Result

Direct evaluation failed during model loading.

Observed error:

```text
OSError: Error no file named pytorch_model.bin, model.safetensors, tf_model.h5,
model.ckpt.index or flax_model.msgpack found in directory
/root/autodl-tmp/AgentRolloutProfiler/checkpoints/checkpoint_smoke_tiny/global_step_2/actor.
```

## Interpretation

The saved `global_step_*/actor` directory is a verl/FSDP trainer checkpoint, not
a plain HuggingFace-loadable model directory. It contains files such as:

```text
model_world_size_1_rank_0.pt
optim_world_size_1_rank_0.pt
extra_state_world_size_1_rank_0.pt
tokenizer.json
config.json
```

This means `actor_rollout_ref.model.path=/path/to/global_step_X/actor` is not
sufficient for final eval.

## Consequence for Phase 3

Phase 3 should keep the main claim as wall-clock scheduling optimization:

> Smaller frequent validation sets can reduce exploratory RL training
> wall-clock cost while preserving a final full eval for reporting.

It should not claim final policy-quality equivalence between schedules unless a
separate export or resume-eval path is implemented.

## Possible Future Work

Two possible paths remain:

1. Find or implement a verl/FSDP actor export step that converts
   `model_world_size_*_rank_*.pt` into a HuggingFace-loadable model directory.
2. Use verl-agent's native resume machinery for a val-only run, if it can load
   trainer checkpoints without taking optimizer-update steps.

Both are out of scope for the current lightweight scheduling optimization.
