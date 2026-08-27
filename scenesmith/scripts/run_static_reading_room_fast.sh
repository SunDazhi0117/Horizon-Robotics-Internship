#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Fast preview keeps the same model and inference-step count, but uses several
# GPUs for independent assets and a lighter mesh/validation resolution.
export SCENESMITH_GPU_WORKERS="${SCENESMITH_GPU_WORKERS:-1}"
export SCENESMITH_HUNYUAN_INFERENCE_STEPS="${SCENESMITH_HUNYUAN_INFERENCE_STEPS:-5}"
export SCENESMITH_HUNYUAN_OCTREE_RESOLUTION="${SCENESMITH_HUNYUAN_OCTREE_RESOLUTION:-128}"
export SCENESMITH_PHYSICS_SIDE_VIEWS="${SCENESMITH_PHYSICS_SIDE_VIEWS:-2}"
export SCENESMITH_VALIDATION_TAA_SAMPLES="${SCENESMITH_VALIDATION_TAA_SAMPLES:-4}"

echo "SceneSmith fast preview"
echo "  GPU workers: $SCENESMITH_GPU_WORKERS"
echo "  Hunyuan steps: $SCENESMITH_HUNYUAN_INFERENCE_STEPS"
echo "  Octree resolution: $SCENESMITH_HUNYUAN_OCTREE_RESOLUTION"
echo "  Physics side views: $SCENESMITH_PHYSICS_SIDE_VIEWS"
echo "  Validation TAA samples: $SCENESMITH_VALIDATION_TAA_SAMPLES"

if [[ "${SCENESMITH_DRY_RUN:-0}" == "1" ]]; then
  exit 0
fi

exec "$repo_root/scripts/run_static_reading_room.sh" "$@"
