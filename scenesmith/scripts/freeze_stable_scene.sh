#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
default_scene="$repo_root/outputs/2026-06-30/17-25-40/scene_000"
scene_dir="$(realpath -m "${1:-$default_scene}")"
version="${2:-stable_scene_v1}"
stable_dir="$scene_dir/$version"

if [[ -e "$stable_dir" ]]; then
  echo "Stable version already exists and will not be overwritten: $stable_dir" >&2
  exit 1
fi

temp_dir="$(mktemp -d)"
trap 'rm -rf "$temp_dir"' EXIT

python "$repo_root/scripts/validate_complete_scene.py" \
  "$scene_dir" \
  --version "$version" \
  --json-output "$temp_dir/acceptance_report.json" \
  --markdown-output "$temp_dir/ACCEPTANCE_REPORT.md"

mkdir "$stable_dir"
cp --reflink=auto --preserve=timestamps \
  "$scene_dir/complete_room_with_furniture.glb" \
  "$scene_dir/complete_room_with_furniture.blend" \
  "$scene_dir/complete_room_with_furniture_report.json" \
  "$stable_dir/"
cp --preserve=timestamps \
  "$repo_root/viewer/glb_viewer.html" \
  "$stable_dir/complete_scene_viewer.html"
cp --preserve=timestamps \
  "$scene_dir/room_studio/scene_states/scene_after_furniture/scene_state.json" \
  "$stable_dir/source_scene_state.json"
cp "$temp_dir/acceptance_report.json" "$temp_dir/ACCEPTANCE_REPORT.md" "$stable_dir/"

for optional_file in \
  complete_scene_browser_check.json \
  complete_scene_desktop.png \
  complete_scene_mobile.png
do
  if [[ -s "$scene_dir/$optional_file" ]]; then
    cp --reflink=auto --preserve=timestamps \
      "$scene_dir/$optional_file" \
      "$stable_dir/$optional_file"
  fi
done

ln -s ../../../../../web_deps/node_modules/three "$stable_dir/three"

(
  cd "$stable_dir"
  sha256sum \
    complete_room_with_furniture.glb \
    complete_room_with_furniture.blend \
    complete_room_with_furniture_report.json \
    complete_scene_viewer.html \
    source_scene_state.json \
    acceptance_report.json \
    ACCEPTANCE_REPORT.md \
    > SHA256SUMS
  sha256sum --check SHA256SUMS
)

echo "Frozen stable scene: $stable_dir"
