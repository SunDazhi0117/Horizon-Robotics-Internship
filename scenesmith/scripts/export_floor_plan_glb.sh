#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
default_run="$repo_root/outputs/2026-06-29/17-55-56"
run_dir="$(realpath -m "${1:-$default_run}")"
scene_dir="$run_dir/scene_000"
blend_file="$scene_dir/floor_plans/final_floor_plan/floor_plan.blend"
glb_file="$scene_dir/floor_plan_export.glb"
python_bin="$repo_root/.venv/bin/python"

if [[ ! -x "$python_bin" ]]; then
  echo "SceneSmith Python environment not found: $python_bin" >&2
  exit 1
fi

"$python_bin" "$repo_root/scripts/export_floor_plan_glb.py" \
  "$blend_file" \
  "$glb_file"

