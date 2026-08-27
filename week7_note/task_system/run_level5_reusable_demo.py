"""Run reusable grasp and hinge-follow actions in the real Level 5 model."""

from __future__ import annotations

import json
from pathlib import Path

from .executor import DEFAULT_ACTIONS, TaskExecutor, load_task_config
from .level5_integration import (
    create_level5_runtime,
    validate_level5_states,
)
from .mujoco_manipulation import MujocoManipulationActions


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "configs" / "level5_reusable_left_door.yaml"
TRAJECTORY_PATH = ROOT / "results" / "reusable_left_door_trajectory.json"
RESULT_PATH = ROOT / "results" / "reusable_left_door_validation.json"


def main() -> None:
    _, _, adapter, validator = create_level5_runtime()
    manipulation = MujocoManipulationActions(adapter, validator)
    actions = dict(DEFAULT_ACTIONS)
    actions.update(manipulation.action_registry())

    result = TaskExecutor(actions).execute(load_task_config(CONFIG_PATH))
    states = list(result.states)
    _, summary = validate_level5_states(states, validator)
    reference_trajectory = summary.pop("source_trajectory")
    final_angle = float(result.final_state.object_joints["left_hinge"])
    target_angle = 1.5707963267948966
    summary.update(
        {
            "integration_name": "reusable_left_door_grasp_and_open",
            "task_name": result.task_name,
            "action_count": len(result.action_ranges),
            "actions": [
                action_range.to_dict()
                for action_range in result.action_ranges
            ],
            "target_left_hinge": target_angle,
            "final_left_hinge": final_angle,
            "final_target_error": abs(final_angle - target_angle),
            "source_config": str(CONFIG_PATH),
            "generated_trajectory": str(TRAJECTORY_PATH),
            "reference_stable_trajectory": reference_trajectory,
        }
    )
    summary["passed"] = bool(
        summary["passed"] and summary["final_target_error"] <= 1e-9
    )

    TRAJECTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRAJECTORY_PATH.write_text(
        json.dumps([state.to_dict() for state in states], indent=2) + "\n",
        encoding="utf-8",
    )
    RESULT_PATH.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    if not summary["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
