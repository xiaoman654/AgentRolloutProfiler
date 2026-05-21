# Server Phase 3 Checkpoint Smoke Commands

These commands verify whether verl-agent can save an RL actor checkpoint in the
WarmGiGPO-WebShop setup. This is a prerequisite for comparing final policy
quality under different validation schedules.

Expected paths:

```text
/root/autodl-fs/AgentRolloutProfiler
/root/autodl-fs/WarmGiGPO-WebShop
```

## 1. Sync and Pre-Check

```bash
cd /root/autodl-fs/AgentRolloutProfiler
git pull --rebase origin main

echo "===== active jobs ====="
ps aux | grep -E "main_ppo|TaskRunner|WorkerDict|actor_rollout|vllm|sft_lora.py|python" | grep -v grep || true
nvidia-smi
```

## 2. Run Tiny Checkpoint Smoke

This is a self-contained version of the existing tiny smoke run with checkpoint
saving enabled. Use the explicit `python -m verl.trainer.main_ppo` command here
because the existing smoke script does not forward arbitrary CLI overrides.

```bash
source /root/miniconda3/etc/profile.d/conda.sh
conda activate verl-agent-webshop
source /etc/network_turbo || true

export OMP_NUM_THREADS=1
export HF_HUB_DISABLE_XET=1
export HF_HUB_ENABLE_HF_TRANSFER=0
export VLLM_ATTENTION_BACKEND=XFORMERS
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}

PROJECT_DIR=/root/autodl-fs/WarmGiGPO-WebShop
ARP_DIR=/root/autodl-fs/AgentRolloutProfiler
MODEL_DIR=/root/.cache/huggingface/hub/models--Qwen--Qwen2.5-1.5B-Instruct/snapshots/989aa7980e4cf806f80c7fef2b1adb7bc71aa306
CKPT_DIR="$PROJECT_DIR/checkpoints/verl_agent_webshop/checkpoint_smoke_tiny"

mkdir -p "$ARP_DIR/logs/phase3_checkpoint"

cd "$PROJECT_DIR/third_party/verl-agent"

echo "===== remove old smoke checkpoint dir ====="
rm -rf "$CKPT_DIR"

echo "===== run checkpoint smoke ====="
{ time python -m verl.trainer.main_ppo \
  algorithm.adv_estimator=gigpo \
  data.train_files=/root/data/verl-agent/text_tiny/train.parquet \
  data.val_files=/root/data/verl-agent/text_tiny/test.parquet \
  data.train_batch_size=1 \
  data.val_batch_size=1 \
  data.max_prompt_length=4096 \
  data.max_response_length=128 \
  data.filter_overlong_prompts=True \
  data.truncation=error \
  data.return_raw_chat=True \
  actor_rollout_ref.model.path="$MODEL_DIR" \
  actor_rollout_ref.actor.optim.lr=1e-6 \
  actor_rollout_ref.model.use_remove_padding=True \
  actor_rollout_ref.model.enable_gradient_checkpointing=False \
  actor_rollout_ref.actor.ppo_mini_batch_size=1 \
  actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu=1 \
  actor_rollout_ref.actor.use_kl_loss=True \
  actor_rollout_ref.actor.kl_loss_coef=0.01 \
  actor_rollout_ref.actor.kl_loss_type=low_var_kl \
  actor_rollout_ref.actor.fsdp_config.param_offload=False \
  actor_rollout_ref.actor.fsdp_config.optimizer_offload=False \
  actor_rollout_ref.rollout.log_prob_micro_batch_size_per_gpu=1 \
  actor_rollout_ref.rollout.tensor_model_parallel_size=1 \
  actor_rollout_ref.rollout.name=vllm \
  actor_rollout_ref.rollout.gpu_memory_utilization=0.35 \
  actor_rollout_ref.rollout.enable_chunked_prefill=False \
  actor_rollout_ref.rollout.enforce_eager=False \
  actor_rollout_ref.rollout.free_cache_engine=False \
  actor_rollout_ref.rollout.val_kwargs.temperature=0.4 \
  actor_rollout_ref.rollout.val_kwargs.do_sample=True \
  actor_rollout_ref.ref.log_prob_micro_batch_size_per_gpu=1 \
  actor_rollout_ref.ref.fsdp_config.param_offload=True \
  actor_rollout_ref.actor.use_invalid_action_penalty=True \
  actor_rollout_ref.actor.invalid_action_penalty_coef=0.1 \
  algorithm.use_kl_in_reward=False \
  algorithm.gamma=0.95 \
  algorithm.gigpo.step_advantage_w=1.0 \
  algorithm.gigpo.mode=mean_norm \
  env.env_name=Webshop \
  env.seed=0 \
  env.max_steps=3 \
  env.rollout.n=1 \
  env.resources_per_worker.num_cpus=0.1 \
  trainer.critic_warmup=0 \
  trainer.logger='[console]' \
  trainer.project_name=verl_agent_webshop \
  trainer.experiment_name=checkpoint_smoke_tiny \
  trainer.n_gpus_per_node=1 \
  trainer.nnodes=1 \
  trainer.default_local_dir="$CKPT_DIR" \
  trainer.save_freq=1 \
  trainer.resume_mode=disable \
  trainer.max_actor_ckpt_to_keep=1 \
  trainer.max_critic_ckpt_to_keep=1 \
  trainer.test_freq=1000 \
  trainer.total_epochs=1 \
  trainer.val_before_train=False; } \
  2>&1 | tee "$ARP_DIR/logs/phase3_checkpoint/checkpoint_smoke_tiny_$(date +%Y%m%d_%H%M%S).log"
```

## 3. Inspect Checkpoint Structure

```bash
cd /root/autodl-fs/WarmGiGPO-WebShop

CKPT_DIR=/root/autodl-fs/WarmGiGPO-WebShop/checkpoints/verl_agent_webshop/checkpoint_smoke_tiny

echo "===== checkpoint tree ====="
find "$CKPT_DIR" -maxdepth 4 -type f | sort | head -200

echo "===== checkpoint dirs ====="
find "$CKPT_DIR" -maxdepth 4 -type d | sort

echo "===== latest tracker ====="
cat "$CKPT_DIR/latest_checkpointed_iteration.txt" || true

echo "===== actor dir size ====="
du -sh "$CKPT_DIR"/global_step_*/actor 2>/dev/null || true
```

## 4. Check Log Markers

```bash
cd /root/autodl-fs/AgentRolloutProfiler

latest=$(ls -t logs/phase3_checkpoint/checkpoint_smoke_tiny_*.log | head -1)
echo "$latest"

grep -E "save_checkpoint|local_global_step_folder|Saving|Saved checkpoint|global_step_|Error|Traceback|CUDA out of memory|RuntimeError|real|user|sys" \
  "$latest" | tail -120
```

## 5. Interpretation

The smoke test passes if:

- `latest_checkpointed_iteration.txt` exists
- at least one `global_step_*` directory exists
- `global_step_*/actor` exists and contains checkpoint files
- the log has no traceback or OOM

The smoke test does not prove that the actor checkpoint is directly
HuggingFace-loadable. It only proves that verl-agent checkpoint saving works.
The next question is whether val-only resume or an export step can evaluate this
actor checkpoint.
