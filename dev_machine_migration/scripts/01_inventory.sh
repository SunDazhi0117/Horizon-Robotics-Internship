#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/users/dazhi.sun-labs/projects"
OUT="$ROOT/dev_machine_migration/inventory"

mkdir -p "$OUT"
cd "$ROOT"

{
  echo "# Migration Inventory"
  echo
  date
  echo
  echo "## Workspace"
  pwd
  echo
  echo "## Directory sizes"
  du -sh \
    articraft \
    scenesmith \
    week1_note \
    week2_note \
    week3_note \
    week4_note \
    week5_note \
    week6_note \
    week7_note \
    week8_note \
    .vscode \
    dev_machine_migration 2>/dev/null || true
  echo
  echo "## Virtual environments"
  find . -maxdepth 3 -type d \( \
    -name ".venv" -o \
    -name ".mujoco_venv" -o \
    -name "node_modules" -o \
    -name "__pycache__" \
  \) | sort
  echo
  echo "## Python versions"
  python -V 2>/dev/null || true
  scenesmith/.mujoco_venv/bin/python -V 2>/dev/null || true
  scenesmith/.venv/bin/python -V 2>/dev/null || true
  articraft/.venv/bin/python -V 2>/dev/null || true
  echo
  echo "## Dependency files"
  find . -maxdepth 3 -type f \( \
    -name "pyproject.toml" -o \
    -name "uv.lock" -o \
    -name "requirements*.txt" -o \
    -name "environment*.yml" -o \
    -name "package.json" \
  \) | sort
  echo
  echo "## Week6-Week8 important outputs"
  find week6_note week7_note week8_note -type f \( \
    -name "*.gif" -o \
    -name "*.mp4" -o \
    -name "*.json" -o \
    -name "*.yaml" -o \
    -name "*.xml" -o \
    -name "*.md" \
  \) -printf "%s %p\n" | sort -nr | head -300
  echo
  echo "## VSCode files"
  find .vscode -maxdepth 2 -type f -print 2>/dev/null | sort || true
} | tee "$OUT/inventory_$(date +%Y%m%d_%H%M%S).txt"

echo
echo "Inventory saved under: $OUT"

