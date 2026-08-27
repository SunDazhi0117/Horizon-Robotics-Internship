#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
default_run="$repo_root/outputs/2026-06-29/17-55-56"
run_dir="$(realpath -m "${1:-$default_run}")"
port="${2:-8080}"
scene_dir="$run_dir/scene_000"
glb_file="$scene_dir/floor_plan_export.glb"
viewer_template="$repo_root/viewer/glb_viewer.html"
three_dir="$repo_root/web_deps/node_modules/three"
python_bin="$repo_root/.venv/bin/python"

if [[ ! -s "$glb_file" ]]; then
  echo "GLB not found: $glb_file" >&2
  echo "Run scripts/export_floor_plan_glb.sh first." >&2
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

cp "$viewer_template" "$scene_dir/glb_viewer_local.html"
ln -sfn "$three_dir" "$scene_dir/three"

available_port=""
for _ in $(seq 1 20); do
  if "$python_bin" - "$port" <<'PY'
import socket
import sys

try:
    with socket.socket() as sock:
        sock.bind(("0.0.0.0", int(sys.argv[1])))
except OSError:
    raise SystemExit(1)
PY
  then
    available_port="$port"
    break
  fi
  port=$((port + 1))
done
if [[ -z "$available_port" ]]; then
  echo "No available viewer port found in the requested range." >&2
  exit 1
fi

url="http://127.0.0.1:$available_port/glb_viewer_local.html"
echo "Serving SceneSmith GLB from: $scene_dir"
echo "Viewer URL: $url"
echo "Press Ctrl+C to stop."

exec "$python_bin" -m http.server "$available_port" \
  --bind 0.0.0.0 \
  --directory "$scene_dir"
