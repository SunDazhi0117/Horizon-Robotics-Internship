#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage:"
  echo "  bash dev_machine_migration/scripts/02_sync_to_new_machine.sh user@new-host /target/projects/path"
  exit 2
fi

REMOTE_HOST="$1"
REMOTE_PATH="$2"
ROOT="/home/users/dazhi.sun-labs/projects"

cd "$ROOT"

rsync -avh --info=progress2 \
  --exclude='**/.venv/' \
  --exclude='**/.mujoco_venv/' \
  --exclude='**/node_modules/' \
  --exclude='**/__pycache__/' \
  --exclude='**/.pytest_cache/' \
  --exclude='**/.mypy_cache/' \
  --exclude='**/.ruff_cache/' \
  --exclude='**/.DS_Store' \
  --exclude='**/*.pyc' \
  --exclude='**/*.pyo' \
  . \
  "$REMOTE_HOST:$REMOTE_PATH/"

echo
echo "Sync complete:"
echo "$ROOT -> $REMOTE_HOST:$REMOTE_PATH"

