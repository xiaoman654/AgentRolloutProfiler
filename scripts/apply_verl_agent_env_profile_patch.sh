#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=${PROJECT_DIR:-/root/autodl-fs/AgentRolloutProfiler}
VERL_AGENT_DIR=${VERL_AGENT_DIR:-/root/autodl-fs/WarmGiGPO-WebShop/third_party/verl-agent}
PATCH_FILE="$PROJECT_DIR/patches/verl-agent-webshop-env-profile.patch"

cd "$VERL_AGENT_DIR"

if git apply --reverse --check "$PATCH_FILE" >/dev/null 2>&1; then
  echo "AgentRolloutProfiler env-profile patch already applied."
  exit 0
fi

git apply --check "$PATCH_FILE"
git apply "$PATCH_FILE"
echo "Applied AgentRolloutProfiler env-profile patch to $VERL_AGENT_DIR"

