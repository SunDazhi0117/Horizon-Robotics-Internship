#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scene_dir="$(realpath -m "${1:?Usage: serve_scene_glb.sh SCENE_DIR GLB_FILE [PORT]}")"
glb_name="${2:?Usage: serve_scene_glb.sh SCENE_DIR GLB_FILE [PORT]}"
port="${3:-8900}"
glb_file="$scene_dir/$glb_name"
viewer_file="$scene_dir/scene_viewer.html"
python_bin="$repo_root/.venv/bin/python"

if [[ "$glb_name" == */* ]]; then
  echo "GLB_FILE must be a filename inside SCENE_DIR." >&2
  exit 1
fi
if [[ ! -s "$glb_file" ]]; then
  echo "GLB not found: $glb_file" >&2
  exit 1
fi

cp "$repo_root/viewer/glb_viewer.html" "$viewer_file"
ln -sfn "$repo_root/web_deps/node_modules/three" "$scene_dir/three"

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

url="http://127.0.0.1:$port/scene_viewer.html?model=$glb_name"
echo "Serving scene from: $scene_dir"
echo "Viewer URL: $url"

exec "$python_bin" -m http.server "$port" \
  --bind 0.0.0.0 \
  --directory "$scene_dir"
