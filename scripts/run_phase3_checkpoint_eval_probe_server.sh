#!/usr/bin/env bash
set -euo pipefail

source /root/miniconda3/etc/profile.d/conda.sh
conda activate verl-agent-webshop
source /etc/network_turbo || true

export OMP_NUM_THREADS=1
export HF_HUB_DISABLE_XET=1
export HF_HUB_ENABLE_HF_TRANSFER=0
export VLLM_ATTENTION_BACKEND=XFORMERS
export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}
export TMPDIR=/root/autodl-tmp/tmp
export RAY_TMPDIR=/root/autodl-tmp/ray

PROJECT_DIR=/root/autodl-fs/WarmGiGPO-WebShop
ARP_DIR=/root/autodl-fs/AgentRolloutProfiler
CKPT_ROOT=${CKPT_ROOT:-/root/autodl-tmp/AgentRolloutProfiler/checkpoints/checkpoint_smoke_tiny}
ACTOR_DIR=${ACTOR_DIR:-$CKPT_ROOT/global_step_2/actor}
LOG_DIR="$ARP_DIR/logs/phase3_checkpoint_eval_probe"

mkdir -p "$LOG_DIR" "$TMPDIR" "$RAY_TMPDIR"

echo "===== active jobs ====="
ps aux | grep -E "main_ppo|TaskRunner|WorkerDict|actor_rollout|vllm|sft_lora.py|python" | grep -v grep || true
nvidia-smi

echo "===== stop stale ray and clear system tmp ray sessions ====="
ray stop --force 2>/dev/null || true
rm -rf /tmp/ray /tmp/*ray* 2>/dev/null || true

echo "===== probe paths ====="
echo "CKPT_ROOT=$CKPT_ROOT"
echo "ACTOR_DIR=$ACTOR_DIR"
test -d "$PROJECT_DIR/third_party/verl-agent"
test -f /root/data/verl-agent/text_eval8/train_dummy.parquet
test -f /root/data/verl-agent/text_eval8/test.parquet

if [ ! -d "$ACTOR_DIR" ]; then
  echo "ERROR: actor checkpoint directory does not exist: $ACTOR_DIR" >&2
  echo "Run scripts/run_phase3_checkpoint_smoke_server.sh first, or set ACTOR_DIR=/path/to/global_step_X/actor." >&2
  exit 2
fi

echo "===== actor checkpoint files ====="
find "$ACTOR_DIR" -maxdepth 1 -type f | sort
du -sh "$ACTOR_DIR"
df -hT / /root/autodl-tmp

cd "$PROJECT_DIR/third_party/verl-agent"

echo "===== run direct actor eval probe ====="
{ time python -m verl.trainer.main_ppo \
  algorithm.adv_estimator=gigpo \
  data.train_files=/root/data/verl-agent/text_eval8/train_dummy.parquet \
  data.val_files=/root/data/verl-agent/text_eval8/test.parquet \
  data.train_batch_size=1 \
  data.val_batch_size=1 \
  data.max_prompt_length=4096 \
  data.max_response_length=128 \
  data.filter_overlong_prompts=True \
  data.truncation=error \
  data.return_raw_chat=True \
  actor_rollout_ref.model.path="$ACTOR_DIR" \
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
  env.max_steps=5 \
  env.rollout.n=1 \
  env.resources_per_worker.num_cpus=0.1 \
  trainer.critic_warmup=0 \
  trainer.logger='[console]' \
  trainer.project_name=verl_agent_webshop \
  trainer.experiment_name=checkpoint_eval_probe \
  trainer.n_gpus_per_node=1 \
  trainer.nnodes=1 \
  trainer.save_freq=-1 \
  trainer.test_freq=1000 \
  trainer.total_epochs=1 \
  trainer.val_before_train=True; } \
  2>&1 | tee "$LOG_DIR/checkpoint_eval_probe_$(date +%Y%m%d_%H%M%S).log"

echo "===== latest log ====="
ls -t "$LOG_DIR"/checkpoint_eval_probe_*.log | head -1
