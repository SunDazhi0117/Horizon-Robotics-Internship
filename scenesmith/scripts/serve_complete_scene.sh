#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
default_scene="$repo_root/outputs/2026-06-30/17-25-40/scene_000"
scene_dir="$(realpath -m "${1:-$default_scene}")"
port="${2:-8899}"
glb_file="$scene_dir/complete_room_with_furniture.glb"
viewer_template="$repo_root/viewer/glb_viewer.html"
viewer_file="$scene_dir/complete_scene_viewer.html"
three_dir="$repo_root/web_deps/node_modules/three"
python_bin="$repo_root/.venv/bin/python"

if [[ ! -s "$glb_file" ]]; then
  echo "Complete GLB not found: $glb_file" >&2
  echo "Run scripts/export_complete_room.sh first." >&2
  exit 1
fi
if [[ ! -s "$viewer_template" ]]; then
  echo "Viewer template not found: $viewer_template" >&2
  exit 1
fi
if [[ ! -d "$three_dir" ]]; then
  echo "Local Three.js dependency not found: $three_dir" >&2
  exit 1
fi

cp "$viewer_template" "$viewer_file"
ln -sfn "$three_dir" "$scene_dir/three"

if ! "$python_bin" - "$port" <<'PY'
import socket
import sys

with socket.socket() as sock:
    sock.bind(("0.0.0.0", int(sys.argv[1])))
PY
then
  echo "Port $port is already in use." >&2
  exit 1
fi

url="http://127.0.0.1:$port/complete_scene_viewer.html?model=complete_room_with_furniture.glb"
echo "Serving complete SceneSmith scene from: $scene_dir"
echo "Viewer URL: $url"

exec "$python_bin" -m http.server "$port" \
  --bind 0.0.0.0 \
  --directory "$scene_dir"
