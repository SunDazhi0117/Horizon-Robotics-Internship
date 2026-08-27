#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

provider="${SCENESMITH_PROVIDER:-codex-cli}"

if [[ "$provider" != "codex-cli" && -z "${OPENAI_API_KEY:-}" ]]; then
  env_file="${SCENESMITH_ENV_FILE:-../articraft/.env}"
  if [[ ! -f "$env_file" ]]; then
    echo "OPENAI_API_KEY is not set and env file was not found: $env_file" >&2
    exit 1
  fi

  set -a
  # shellcheck disable=SC1090
  source "$env_file"
  set +a
fi

if [[ "$provider" != "codex-cli" && -z "${OPENAI_API_KEY:-}" ]]; then
  echo "OPENAI_API_KEY is missing." >&2
  exit 1
fi

export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"

exec uv run python main.py \
  +name=simple_room \
  'experiment.prompts=["A small empty rectangular room, 4 meters by 3 meters, with one standard door and one window. Use plain white walls and a simple wooden floor. Do not add furniture or decorations."]' \
  experiment.pipeline.stop_stage=floor_plan \
  "floor_plan_agent.openai.provider=$provider" \
  floor_plan_agent.materials.use_retrieval_server=false \
  floor_plan_agent.session_memory.enable_summarization=false \
  floor_plan_agent.max_critique_rounds=1 \
  floor_plan_agent.openai.reasoning_effort.designer=low \
  floor_plan_agent.openai.reasoning_effort.critic=low
