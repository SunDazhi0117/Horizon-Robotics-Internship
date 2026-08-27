#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="$repo_root/.venv/bin/python"
hunyuan_dir="$repo_root/external/Hunyuan3D-2"
hunyuan_model="$HOME/.cache/hy3dgen/tencent/Hunyuan3D-2mini/hunyuan3d-dit-v2-mini-turbo/model.fp16.safetensors"
hunyuan_model_size=3822584202

failed=0

check_path() {
  local path="$1"
  local label="$2"
  if [[ -e "$path" ]]; then
    printf 'OK      %s: %s\n' "$label" "$path"
  else
    printf 'MISSING %s: %s\n' "$label" "$path"
    failed=1
  fi
}

check_path "$python_bin" "SceneSmith Python"
check_path "$hunyuan_dir/hy3dgen" "Hunyuan3D source"
if [[ -f "$hunyuan_model" ]] \
  && [[ "$(stat -c %s "$hunyuan_model")" -eq "$hunyuan_model_size" ]] \
  && [[ ! -e "$hunyuan_model.aria2" ]]; then
  printf 'OK      Hunyuan3D mini weights: %s\n' "$hunyuan_model"
else
  printf 'MISSING Hunyuan3D mini weights: run scripts/download_hunyuan3d_mini.sh\n'
  failed=1
fi

echo
"$python_bin" - <<'PY' || failed=1
import importlib.util

required = ["torch", "pydrake", "bpy", "hy3dgen"]
missing = []
for name in required:
    installed = importlib.util.find_spec(name) is not None
    print(f"{'OK     ' if installed else 'MISSING'} Python module: {name}")
    if not installed:
        missing.append(name)
if missing:
    raise SystemExit(1)
PY

echo
"$python_bin" - <<'PY' || failed=1
import torch

print(f"PyTorch: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if not torch.cuda.is_available():
    raise SystemExit(1)
for index in range(torch.cuda.device_count()):
    properties = torch.cuda.get_device_properties(index)
    memory_gib = properties.total_memory / 1024**3
    print(f"GPU {index}: {properties.name}, {memory_gib:.1f} GiB")
if not any(
    torch.cuda.get_device_properties(index).total_memory >= 23 * 1024**3
    for index in range(torch.cuda.device_count())
):
    raise SystemExit("No GPU with at least 23 GiB was detected")
PY

echo
if [[ $failed -ne 0 ]]; then
  echo "Furniture requirements are not ready." >&2
  exit 1
fi
echo "Furniture requirements are ready for the Hunyuan3D smoke test."
