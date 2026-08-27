#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
default_run="$repo_root/outputs/2026-06-29/17-55-56"
run_dir="$(realpath -m "${1:-$default_run}")"
scene_dir="$run_dir/scene_000"
python_bin="$repo_root/.venv/bin/python"

required_files=(
  "$scene_dir/final_floor_plan/floor_plan.png"
  "$scene_dir/floor_plans/final_floor_plan/floor_plan.blend"
  "$scene_dir/floor_plans/final_floor_plan/floor_plan.dmd.yaml"
  "$scene_dir/floor_plan_export.glb"
)

failed=0
printf 'SceneSmith run: %s\n\n' "$run_dir"
for path in "${required_files[@]}"; do
  if [[ -s "$path" ]]; then
    printf 'OK  %8s  %s\n' "$(du -h "$path" | cut -f1)" "$path"
  else
    printf 'MISSING      %s\n' "$path"
    failed=1
  fi
done

shopt -s nullglob
room_sdf=("$scene_dir"/room_geometry/room_geometry_*.sdf)
shopt -u nullglob
if [[ ${#room_sdf[@]} -gt 0 && -s "${room_sdf[0]}" ]]; then
  printf 'OK  %8s  %s\n' "$(du -h "${room_sdf[0]}" | cut -f1)" "${room_sdf[0]}"
else
  printf 'MISSING      %s\n' "$scene_dir/room_geometry/room_geometry_*.sdf"
  failed=1
fi

viewer_template="$repo_root/viewer/glb_viewer.html"
if [[ -s "$viewer_template" ]]; then
  printf 'OK  %8s  %s\n' "$(du -h "$viewer_template" | cut -f1)" "$viewer_template"
else
  printf 'MISSING      %s\n' "$viewer_template"
  failed=1
fi

if [[ $failed -ne 0 ]]; then
  echo
  echo "SceneSmith output check failed." >&2
  exit 1
fi

echo
"$python_bin" - "$scene_dir/floor_plan_export.glb" <<'PY'
from pathlib import Path
import sys

from pygltflib import GLTF2

path = Path(sys.argv[1])
model = GLTF2().load_binary(path)
print(
    "GLB validation: "
    f"scenes={len(model.scenes or [])}, "
    f"nodes={len(model.nodes or [])}, "
    f"meshes={len(model.meshes or [])}, "
    f"materials={len(model.materials or [])}"
)
if not model.scenes or not model.nodes or not model.meshes:
    raise SystemExit("GLB has no renderable scene content")
PY

echo "All required SceneSmith outputs are ready."

