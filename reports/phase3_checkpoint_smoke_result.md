# Phase 3 Checkpoint Smoke Result

## Run

Server path:

```text
/root/autodl-tmp/AgentRolloutProfiler/checkpoints/checkpoint_smoke_tiny
```

The checkpoint smoke was run with:

- tiny WebShop train/eval parquet files
- `env.max_steps=3`
- `env.rollout.n=1`
- `trainer.save_freq=1`
- `trainer.default_local_dir=/root/autodl-tmp/AgentRolloutProfiler/checkpoints/checkpoint_smoke_tiny`
- Ray/TMP directories moved to `/root/autodl-tmp`

## Result

Checkpoint saving works.

Observed files:

```text
global_step_1/data.pt
global_step_2/actor/added_tokens.json
global_step_2/actor/config.json
global_step_2/actor/extra_state_world_size_1_rank_0.pt
global_step_2/actor/generation_config.json
global_step_2/actor/merges.txt
global_step_2/actor/model_world_size_1_rank_0.pt
global_step_2/actor/optim_world_size_1_rank_0.pt
global_step_2/actor/special_tokens_map.json
global_step_2/actor/tokenizer.json
global_step_2/actor/tokenizer_config.json
global_step_2/actor/vocab.json
global_step_2/data.pt
latest_checkpointed_iteration.txt
```

Observed directories:

```text
checkpoint_smoke_tiny
checkpoint_smoke_tiny/global_step_1
checkpoint_smoke_tiny/global_step_2
checkpoint_smoke_tiny/global_step_2/actor
```

Observed actor checkpoint size:

```text
219G    global_step_2/actor
```

## Interpretation

The smoke test confirms that verl-agent can save RL actor checkpoints in this
setup when checkpoint output is moved to the data disk.

However, the saved actor directory is very large because it includes full actor
state and optimizer state files. This changes the Phase 3 experimental boundary:

- Final policy quality comparison is technically feasible.
- Frequent checkpoint saving is not practical on the system disk.
- Controlled schedule-comparison runs should use at most final-checkpoint
  saving, write checkpoints to `/root/autodl-tmp`, and clean up immediately
  after evaluation.
- Phase 3's primary claim should remain wall-clock scheduling optimization
  unless checkpoint export/evaluation is separately verified.

## Next Question

The remaining unknown is whether `global_step_*/actor` can be evaluated directly
by a val-only verl-agent run or must first be exported/converted into a
HuggingFace-loadable model directory.
