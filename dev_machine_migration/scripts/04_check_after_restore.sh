#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/users/dazhi.sun-labs/projects"
cd "$ROOT"

if [[ ! -x scenesmith/.mujoco_venv/bin/python ]]; then
  echo "Missing MuJoCo venv: scenesmith/.mujoco_venv"
  echo "Run: bash dev_machine_migration/scripts/03_restore_envs_on_new_machine.sh"
  exit 1
fi

echo "## Basic paths"
test -d scenesmith
test -d articraft
test -d week6_note
test -d week7_note
test -d week8_note
test -f .vscode/settings.json
echo "Basic folders: OK"

echo
echo "## Key Week8 artifacts"
test -f week8_note/configs/entry_door_open_hold_close_auto_orbit.yaml
test -f week8_note/assets/entry_door_open_hold_close_auto_orbit.gif
test -f week8_note/assets/entry_door_open_hold_close_auto_orbit_top_view.gif
test -f week8_note/results/entry_door_open_hold_close_auto_orbit_summary.json
echo "Week8 artifacts: OK"

echo
echo "## MuJoCo import"
scenesmith/.mujoco_venv/bin/python - <<'PY'
import mujoco
print("MuJoCo:", mujoco.__version__)
PY

echo
echo "## Week7 tests"
PYTHONDONTWRITEBYTECODE=1 scenesmith/.mujoco_venv/bin/python -m unittest discover -s week7_note/tests -v

echo
echo "## Week8 tests"
PYTHONDONTWRITEBYTECODE=1 scenesmith/.mujoco_venv/bin/python -m unittest discover -s week8_note/tests -v

echo
echo "Restore check: PASS"
