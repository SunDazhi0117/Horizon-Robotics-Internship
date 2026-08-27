#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

temp_dir="${SCENESMITH_TMPDIR:-$repo_root/outputs/.tmp}"
mkdir -p "$temp_dir"
export TMPDIR="$temp_dir"
export TMP="$temp_dir"
export TEMP="$temp_dir"

timestamp="$(date +%Y%m%d_%H%M%S)"
floor_name="static_reading_room_floor_$timestamp"
furniture_name="static_reading_room_furniture_$timestamp"
prompt="${SCENESMITH_SCENE_PROMPT:-A small realistic single-room reading and work studio with one entrance door and three windows. Keep a broad open path from the entrance through the center. The room should contain only static non-articulated furniture: one compact study desk, two simple reading chairs, one low coffee table, one bookcase, and one low closed storage cabinet. Place furniture along the room perimeter and do not add wall-mounted objects, loose objects, appliances, articulated doors, drawers, or decorations.}"

export LOGLEVEL="INFO"
export NUMBA_DEBUG="0"
export NUMBA_LOG_LEVEL="WARNING"
export NUMBA_CUDA_LOG_LEVEL="WARNING"
export HF_HUB_DISABLE_XET="1"
export SCENESMITH_HUNYUAN_SHAPE_ONLY="1"
export SCENESMITH_VLM_PROVIDER="${SCENESMITH_VLM_PROVIDER:-codex-cli}"
export SCENESMITH_CODEX_MODEL="${SCENESMITH_CODEX_MODEL:-gpt-5.5}"
physics_side_views="${SCENESMITH_PHYSICS_SIDE_VIEWS:-4}"
validation_taa_samples="${SCENESMITH_VALIDATION_TAA_SAMPLES:-8}"

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

scripts/check_furniture_requirements.sh

echo "Generating floor plan: $floor_name"
uv run python main.py \
  +name="$floor_name" \
  "experiment.prompts=[\"$prompt\"]" \
  experiment.num_workers=1 \
  experiment.pipeline.start_stage=floor_plan \
  experiment.pipeline.stop_stage=floor_plan \
  experiment.projection.enabled=false \
  experiment.sceneeval_export.enabled=false \
  "floor_plan_agent.openai.provider=$SCENESMITH_VLM_PROVIDER" \
  floor_plan_agent.materials.use_retrieval_server=false \
  floor_plan_agent.session_memory.enable_summarization=false \
  floor_plan_agent.max_critique_rounds=0 \
  floor_plan_agent.openai.codex_cli_reasoning_effort=medium \
  floor_plan_agent.openai.reasoning_effort.designer=low \
  floor_plan_agent.openai.reasoning_effort.critic=low

floor_run="$(realpath outputs/latest-run)"
floor_plan="$floor_run/scene_000/floor_plans/final_floor_plan/floor_plan.dmd.yaml"
if [[ ! -s "$floor_plan" ]]; then
  echo "Floor plan checkpoint was not generated: $floor_plan" >&2
  exit 1
fi

echo "Generating static furniture from: $floor_run"
uv run python main.py \
  +name="$furniture_name" \
  "experiment.prompts=[\"$prompt\"]" \
  experiment.num_workers=1 \
  experiment.pipeline.start_stage=furniture \
  experiment.pipeline.stop_stage=furniture \
  "experiment.pipeline.resume_from_path=$floor_run" \
  experiment.projection.enabled=false \
  experiment.sceneeval_export.enabled=false \
  floor_plan_agent.materials.use_retrieval_server=false \
  "+furniture_agent.openai.provider=$SCENESMITH_VLM_PROVIDER" \
  +furniture_agent.openai.codex_cli_reasoning_effort=medium \
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

furniture_run="$(realpath outputs/latest-run)"
echo "Floor run: $floor_run"
echo "Static furniture run: $furniture_run"
