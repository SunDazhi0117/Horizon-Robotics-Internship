#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
default_scene="$repo_root/outputs/2026-06-30/17-25-40/scene_000"
scene_dir="$(realpath -m "${1:-$default_scene}")"
blender_bin="${BLENDER_BIN:-$(command -v blender)}"

if [[ -z "$blender_bin" || ! -x "$blender_bin" ]]; then
  echo "Blender executable not found." >&2
  exit 1
fi

"$blender_bin" --background \
  --python "$repo_root/scripts/export_complete_room.py" \
  -- "$scene_dir"
