#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/users/dazhi.sun-labs/projects"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "Neither python3 nor python was found on PATH."
    exit 1
  fi
fi

echo "Workspace: $ROOT"
"$PYTHON_BIN" -V

if ! command -v uv >/dev/null 2>&1; then
  echo
  echo "uv is not installed or not on PATH."
  echo "Install uv first, or ask IT if package installation is restricted."
else
  if [[ -f scenesmith/pyproject.toml ]]; then
    echo
    echo "Restoring SceneSmith uv environment..."
    (cd scenesmith && uv sync)
  fi

  if [[ -f articraft/pyproject.toml ]]; then
    echo
    echo "Restoring Articraft uv environment..."
    (cd articraft && uv sync)
  fi
fi

echo
echo "Creating MuJoCo task venv..."
"$PYTHON_BIN" -m venv scenesmith/.mujoco_venv
scenesmith/.mujoco_venv/bin/python -m pip install --upgrade pip
scenesmith/.mujoco_venv/bin/python -m pip install \
  mujoco \
  numpy \
  scipy \
  pillow \
  pyyaml \
  matplotlib \
  imageio

echo
echo "Environment restore step finished."
echo "Next run:"
echo "  bash dev_machine_migration/scripts/04_check_after_restore.sh"
