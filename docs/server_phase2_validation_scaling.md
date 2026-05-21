# Server Phase 2 Validation Scaling Commands

These commands collect validation scaling logs on the AutoDL server.

Goal:

- compare eval8, eval16, and eval64 wall-clock behavior
- keep WebShop env instrumentation enabled
- parse logs with `build_phase2_validation_report.py`
- avoid committing large raw logs

Expected paths:

```text
/root/autodl-fs/AgentRolloutProfiler
/root/autodl-fs/WarmGiGPO-WebShop
```

## 1. Sync Profiler Repo

```bash
cd /root/autodl-fs

export ARP_DIR=/root/autodl-fs/AgentRolloutProfiler
export WARM_DIR=/root/autodl-fs/WarmGiGPO-WebShop

echo "===== sync AgentRolloutProfiler ====="
cd "$ARP_DIR"
git status --short
git pull --rebase origin main

echo "===== check active jobs ====="
ps aux | grep -E "main_ppo|TaskRunner|WorkerDict|actor_rollout|vllm|sft_lora.py|python" | grep -v grep || true
nvidia-smi
```

## 2. Verify Env Instrumentation

```bash
cd /root/autodl-fs/AgentRolloutProfiler

export PROJECT_DIR=/root/autodl-fs/AgentRolloutProfiler
export VERL_AGENT_DIR=/root/autodl-fs/WarmGiGPO-WebShop/third_party/verl-agent

echo "===== ensure env profiling patch ====="
bash scripts/apply_verl_agent_env_profile_patch.sh

echo "===== verify ARP_PROFILE markers ====="
grep -R "ARP_PROFILE" \
  /root/autodl-fs/WarmGiGPO-WebShop/third_party/verl-agent/agent_system/environments/env_manager.py \
  /root/autodl-fs/WarmGiGPO-WebShop/third_party/verl-agent/agent_system/environments/env_package/webshop/envs.py
```

## 3. Run Eval Scaling Jobs

Run these one by one. `eval8` is short; `eval64` is the important comparison.

```bash
cd /root/autodl-fs/WarmGiGPO-WebShop
mkdir -p /root/autodl-fs/AgentRolloutProfiler/logs/phase2_validation

echo "===== eval8 ====="
(/usr/bin/time -p bash scripts/eval/run_qwen15b_zero_shot_eval8.sh) \
  2>&1 | tee /root/autodl-fs/AgentRolloutProfiler/logs/phase2_validation/qwen15b_zero_shot_eval8_$(date +%Y%m%d_%H%M%S).log

echo "===== eval16 ====="
(/usr/bin/time -p bash scripts/eval/run_qwen15b_zero_shot_eval16.sh) \
  2>&1 | tee /root/autodl-fs/AgentRolloutProfiler/logs/phase2_validation/qwen15b_zero_shot_eval16_$(date +%Y%m%d_%H%M%S).log

echo "===== eval64 ====="
(/usr/bin/time -p bash scripts/eval/run_qwen15b_zero_shot_eval64.sh) \
  2>&1 | tee /root/autodl-fs/AgentRolloutProfiler/logs/phase2_validation/qwen15b_zero_shot_eval64_$(date +%Y%m%d_%H%M%S).log
```

## 4. Parse Phase 2 Report

```bash
cd /root/autodl-fs/AgentRolloutProfiler

echo "===== latest phase2 logs ====="
ls -lh logs/phase2_validation/*.log

python scripts/build_phase2_validation_report.py \
  --logs logs/phase2_validation/*.log \
  --out reports/phase2_rollout_validation_profile.md \
  --json-out reports/phase2_rollout_validation_profile.json

echo "===== quick summary ====="
grep -E "Validation Cost Summary|qwen15b_zero_shot|Environment Timing Cross-Check|manager_step|worker_step|testing share" \
  reports/phase2_rollout_validation_profile.md || true

echo "===== output files ====="
ls -lh reports/phase2_rollout_validation_profile.md reports/phase2_rollout_validation_profile.json
```

## 5. Commit Only Reports

Do not commit raw logs unless they are explicitly needed.

```bash
cd /root/autodl-fs/AgentRolloutProfiler

git status --short
git add reports/phase2_rollout_validation_profile.md \
        reports/phase2_rollout_validation_profile.json
git commit -m "Add phase 2 validation scaling profile" || true
git push origin main
```
