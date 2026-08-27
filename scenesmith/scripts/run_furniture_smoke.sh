#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

temp_dir="${SCENESMITH_TMPDIR:-$repo_root/outputs/.tmp}"
mkdir -p "$temp_dir"
export TMPDIR="$temp_dir"
export TMP="$temp_dir"
export TEMP="$temp_dir"

source_run="$(realpath -m "${1:-outputs/2026-06-29/17-55-56}")"
run_name="${2:-furniture_smoke_$(date +%Y%m%d_%H%M%S)}"
physics_side_views="${SCENESMITH_PHYSICS_SIDE_VIEWS:-4}"
validation_taa_samples="${SCENESMITH_VALIDATION_TAA_SAMPLES:-8}"

scripts/check_furniture_requirements.sh

if [[ -z "${CUDA_VISIBLE_DEVICES:-}" ]]; then
  gpu_workers="${SCENESMITH_GPU_WORKERS:-1}"
  if ! [[ "$gpu_workers" =~ ^[1-9][0-9]*$ ]]; then
    echo "SCENESMITH_GPU_WORKERS must be a positive integer." >&2
    exit 1
  fi
  CUDA_VISIBLE_DEVICES="$(
    nvidia-smi --query-gpu=index,memory.free --format=csv,noheader,nounits |
      sort -t, -k2,2nr |
      head -n "$gpu_workers" |
      cut -d, -f1 |
      xargs |
      tr ' ' ','
  )"
fi
export CUDA_VISIBLE_DEVICES
echo "Geometry GPUs: $CUDA_VISIBLE_DEVICES"
export LOGLEVEL="INFO"
export NUMBA_DEBUG="0"
export NUMBA_LOG_LEVEL="WARNING"
export NUMBA_CUDA_LOG_LEVEL="WARNING"
export HF_HUB_DISABLE_XET="1"
export SCENESMITH_HUNYUAN_SHAPE_ONLY="1"
export SCENESMITH_VLM_PROVIDER="${SCENESMITH_VLM_PROVIDER:-codex-cli}"
export SCENESMITH_CODEX_MODEL="${SCENESMITH_CODEX_MODEL:-gpt-5.5}"

if [[ -z "${OPENAI_API_KEY:-}" && -f "$repo_root/../articraft/.env" ]]; then
  OPENAI_API_KEY="$(
    .venv/bin/python - <<'PY'
from dotenv import dotenv_values

print(dotenv_values("../articraft/.env").get("OPENAI_API_KEY", ""))
PY
  )"
  export OPENAI_API_KEY
fi

exec uv run python main.py \
  +name="$run_name" \
  'experiment.prompts=["A simple studio room with one compact desk and one chair. Keep the center of the room empty."]' \
  experiment.num_workers=1 \
  experiment.pipeline.start_stage=furniture \
  experiment.pipeline.stop_stage=furniture \
  "experiment.pipeline.resume_from_path=$source_run" \
  experiment.projection.enabled=false \
  experiment.sceneeval_export.enabled=false \
  floor_plan_agent.materials.use_retrieval_server=false \
  "+furniture_agent.openai.provider=$SCENESMITH_VLM_PROVIDER" \
  furniture_agent.session_memory.enable_summarization=false \
  furniture_agent.max_critique_rounds=0 \
  furniture_agent.asset_manager.backend=hunyuan3d \
  furniture_agent.asset_manager.image_generation.backend=local-smoke \
  +furniture_agent.asset_manager.hunyuan3d.use_mini=true \
  furniture_agent.asset_manager.num_side_views_for_physics_analysis="$physics_side_views" \
  furniture_agent.asset_manager.validation_taa_samples="$validation_taa_samples" \
  furniture_agent.asset_manager.router.strategies.generated.max_retries=0 \
  furniture_agent.asset_manager.router.strategies.articulated.enabled=false \
  furniture_agent.asset_manager.router.strategies.thin_covering.enabled=false \
  wall_agent.asset_manager.router.strategies.articulated.enabled=false \
  ceiling_agent.asset_manager.router.strategies.articulated.enabled=false \
  manipuland_agent.asset_manager.router.strategies.articulated.enabled=false
