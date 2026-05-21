# Phase 3 Checkpoint Feasibility

This note checks whether the Phase 3 schedule experiment can also compare final
policy quality, not only wall-clock cost.

## Finding

verl-agent supports PPO checkpoint saving, but the current WarmGiGPO-WebShop RL
scripts disable it.

Relevant trainer behavior:

- checkpoint root: `trainer.default_local_dir`
- default root: `checkpoints/${trainer.project_name}/${trainer.experiment_name}`
- saved step path: `global_step_${step}`
- actor path under a saved step: `global_step_${step}/actor`
- save condition: `trainer.save_freq > 0` and either last step or
  `global_steps % save_freq == 0`

Current WarmGiGPO-WebShop RL scripts set:

```text
trainer.save_freq=-1
```

Therefore the existing runs do not save final RL actor checkpoints by default.

## Consequence

Phase 3 can currently support a wall-clock scheduling claim:

> using smaller validation sets for frequent progress checks reduces exploratory
> training wall-clock cost.

It cannot yet support a final policy quality equivalence claim unless the
training runs save comparable checkpoints and those checkpoints are evaluated on
the same eval64 set.

## Why `MODEL_DIR=/path/to/checkpoint` Is Not Enough

The evaluation scripts expect `actor_rollout_ref.model.path` to point to a model
directory that can initialize the actor. A verl PPO actor checkpoint is saved
under the trainer checkpoint structure and is not necessarily a plain merged
HuggingFace model directory.

There are two safer options:

1. Use verl-agent's checkpoint resume path for a val-only run, if compatible
   with the WebShop eval script.
2. Add a verified export step that converts the final actor checkpoint into a
   HuggingFace-loadable model directory.

Until one of these is verified, final score comparisons should not be claimed.

## Recommended Next Step

Keep Phase 3 as a scheduling/wall-clock optimization first.

If final model quality comparison is needed later, add a dedicated checkpoint
experiment:

- set `trainer.save_freq=32` or `trainer.save_freq=8`
- set a unique `trainer.default_local_dir`
- run a tiny smoke training job
- verify that `global_step_* / actor` is created
- verify whether val-only resume or HF export can evaluate that exact actor

Concrete server commands are in `docs/server_phase3_checkpoint_smoke.md`.

## Smoke Result

The checkpoint smoke test passed after moving both Ray temporary directories and
checkpoint output to `/root/autodl-tmp`.

Observed saved structure:

- `global_step_2/actor`
- `global_step_2/data.pt`
- `latest_checkpointed_iteration.txt`

The actor checkpoint directory was about 219G because it includes full actor
and optimizer state files. This means checkpoint-based quality comparison is
technically possible but storage-expensive. Phase 3 should not use frequent
checkpoint saves for controlled runs. If final policy quality comparison is
added, save only the final checkpoint, evaluate it immediately, and delete or
export it after use.

Detailed result: `reports/phase3_checkpoint_smoke_result.md`.

The remaining unknown is whether `global_step_*/actor` can be evaluated
directly by a val-only verl-agent run or must first be exported/converted into a
HuggingFace-loadable model directory. Probe commands for this question are in
`docs/server_phase3_checkpoint_eval_probe.md`.

## Eval Probe Result

Directly using `global_step_2/actor` as `actor_rollout_ref.model.path` failed.
The loader expected a HuggingFace-style weight file such as
`pytorch_model.bin` or `model.safetensors`, but the actor checkpoint contains
verl/FSDP files such as `model_world_size_1_rank_0.pt`.

Therefore final policy quality comparison requires either:

1. a verified export/convert path from verl/FSDP actor checkpoint to a
   HuggingFace-loadable model directory, or
2. a verified val-only resume path that evaluates the native trainer checkpoint.

Detailed result: `reports/phase3_checkpoint_eval_probe_result.md`.
