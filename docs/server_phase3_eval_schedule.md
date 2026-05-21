# Server Phase 3 Eval Schedule Commands

These commands run a low-risk validation scheduling experiment on AutoDL.

Expected paths:

```text
/root/autodl-fs/AgentRolloutProfiler
/root/autodl-fs/WarmGiGPO-WebShop
```

## 1. Sync Project

```bash
cd /root/autodl-fs/AgentRolloutProfiler
git pull --rebase origin main

echo "===== active jobs ====="
ps aux | grep -E "main_ppo|TaskRunner|WorkerDict|actor_rollout|vllm|sft_lora.py|python" | grep -v grep || true
nvidia-smi
```

## 2. Generate Schedule Estimate

```bash
cd /root/autodl-fs/AgentRolloutProfiler

python scripts/estimate_eval_schedule_savings.py \
  --phase2-json reports/phase2_rollout_validation_profile.json \
  --out reports/phase3_eval_schedule_estimate.md \
  --json-out reports/phase3_eval_schedule_estimate.json \
  --total-steps 32 \
  --normal-step-s 21.5 \
  --baseline-eval-size 64 \
  --baseline-eval-freq 8 \
  --candidate-eval-size 8 \
  --candidate-eval-freq 8 \
  --final-eval-size 64

cat reports/phase3_eval_schedule_estimate.md
```

## 3. Optional Controlled RL Runs

Run these only when a full comparison is needed. They reuse the WarmGiGPO-WebShop
training script and only change the validation data size and experiment name.

Both runs keep `env.seed=0` from the underlying script. Do not change model,
training data, reward, KL, or rollout hyperparameters between runs.

Important: these commands validate wall-clock scheduling cost. To compare final
model quality, the RL training run must save or expose the final trained policy,
and the final eval64 must load that policy. If no final RL checkpoint is saved,
do not interpret the standalone final eval64 as candidate-model quality.

Current caveat: the WarmGiGPO-WebShop RL scripts set `trainer.save_freq=-1`, so
they do not save final RL actor checkpoints by default. The commands below are
therefore wall-clock schedule comparisons unless checkpoint saving/evaluation is
explicitly enabled and verified.

Baseline schedule:

```bash
cd /root/autodl-fs/WarmGiGPO-WebShop
mkdir -p /root/autodl-fs/AgentRolloutProfiler/logs/phase3_schedule

EXPERIMENT_NAME=qwen15b_sft_gigpo_eval64_freq8_schedule_baseline \
TRAIN_FILE=/root/data/verl-agent/text_128_64/train.parquet \
VAL_FILE=/root/data/verl-agent/text_eval64/test.parquet \
{ time bash scripts/rl/run_qwen15b_sft_verl_gigpo_medium.sh; } \
  2>&1 | tee /root/autodl-fs/AgentRolloutProfiler/logs/phase3_schedule/baseline_eval64_freq8_$(date +%Y%m%d_%H%M%S).log
```

Candidate schedule:

```bash
cd /root/autodl-fs/WarmGiGPO-WebShop
mkdir -p /root/autodl-fs/AgentRolloutProfiler/logs/phase3_schedule

EXPERIMENT_NAME=qwen15b_sft_gigpo_eval8_freq8_schedule_candidate \
TRAIN_FILE=/root/data/verl-agent/text_128_64/train.parquet \
VAL_FILE=/root/data/verl-agent/text_eval8/test.parquet \
{ time bash scripts/rl/run_qwen15b_sft_verl_gigpo_medium.sh; } \
  2>&1 | tee /root/autodl-fs/AgentRolloutProfiler/logs/phase3_schedule/candidate_eval8_freq8_$(date +%Y%m%d_%H%M%S).log
```

Final eval64 for candidate, only if `MODEL_DIR` is pointed at the saved
candidate RL checkpoint:

```bash
cd /root/autodl-fs/WarmGiGPO-WebShop

MODEL_DIR=/path/to/candidate/final/checkpoint \
{ time bash scripts/eval/run_qwen15b_sft_verl_full_eval64.sh; } \
  2>&1 | tee /root/autodl-fs/AgentRolloutProfiler/logs/phase3_schedule/candidate_final_eval64_$(date +%Y%m%d_%H%M%S).log
```

## 4. Parse Results

```bash
cd /root/autodl-fs/AgentRolloutProfiler

python scripts/build_phase2_validation_report.py \
  --logs logs/phase3_schedule/*.log \
  --out reports/phase3_schedule_profile.md \
  --json-out reports/phase3_schedule_profile.json

grep -A12 "Validation Cost Summary" reports/phase3_schedule_profile.md
grep -A12 "Score and Case Counts" reports/phase3_schedule_profile.md
```

## 5. Interpretation Rules

- If only schedule logs are available, report wall-clock savings only.
- If final checkpoints are evaluated on the same eval64 set, report both
  wall-clock savings and final score drift.
- Do not compare baseline eval64-in-training scores with candidate eval8 scores
  as policy-quality evidence; they use different validation sets.
