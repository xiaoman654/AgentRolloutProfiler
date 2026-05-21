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

Final eval64 for candidate:

```bash
cd /root/autodl-fs/WarmGiGPO-WebShop

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

