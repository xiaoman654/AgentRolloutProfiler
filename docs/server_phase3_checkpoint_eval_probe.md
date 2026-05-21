# Server Phase 3 Checkpoint Eval Probe

This probe checks whether a saved verl-agent actor checkpoint can be used
directly as `actor_rollout_ref.model.path` in a val-only WebShop eval run.

It does not train and it does not save another checkpoint.

## Prerequisite

Run the checkpoint smoke first and keep the actor checkpoint on the data disk:

```text
/root/autodl-tmp/AgentRolloutProfiler/checkpoints/checkpoint_smoke_tiny/global_step_2/actor
```

If the smoke checkpoint has already been deleted, rerun:

```bash
cd /root/autodl-fs/AgentRolloutProfiler
bash scripts/run_phase3_checkpoint_smoke_server.sh
```

## Run

```bash
cd /root/autodl-fs/AgentRolloutProfiler
git pull --rebase origin main

bash scripts/run_phase3_checkpoint_eval_probe_server.sh
```

To probe a different actor checkpoint:

```bash
ACTOR_DIR=/path/to/global_step_X/actor \
  bash scripts/run_phase3_checkpoint_eval_probe_server.sh
```

## Inspect

```bash
cd /root/autodl-fs/AgentRolloutProfiler

latest=$(ls -t logs/phase3_checkpoint_eval_probe/checkpoint_eval_probe_*.log | head -1)
echo "$latest"

tail -100 "$latest"
grep -E "Initial validation metrics|step:0|Traceback|Error|RuntimeError|Exception|CUDA out of memory|No such file|safetensors|pytorch_model|model_world_size" \
  "$latest" | tail -120 || true
```

## Interpretation

Pass:

- the run reaches `Initial validation metrics` or `step:0`
- no model-loading traceback appears

Fail:

- model loading fails because `global_step_*/actor` is not a plain
  HuggingFace-loadable model directory
- the log mentions missing `pytorch_model.bin`, missing `model.safetensors`, or
  unsupported checkpoint files

If the probe fails, Phase 3 can still claim wall-clock scheduling savings, but
final policy quality comparison requires a separate export/convert path.
