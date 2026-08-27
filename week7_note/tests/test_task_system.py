from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

from week7_note.task_system.executor import TaskExecutor, load_task_config
from week7_note.task_system.primitives import (
    change_gripper,
    move_arm,
    move_base,
)
from week7_note.task_system.state import TaskState


ROOT = Path(__file__).resolve().parents[1]
DEMO_CONFIG = ROOT / "task_system" / "configs" / "foundation_demo.yaml"
PARAMETER_CONFIG = (
    ROOT / "task_system" / "configs" / "parameter_change_demo.yaml"
)


def initial_state() -> TaskState:
    return TaskState(
        phase="initial",
        base=np.array([0.0, 0.0, 0.0]),
        arm_qpos=np.zeros(7),
        gripper=0.04,
        object_joints={
            "cabinet_left_hinge": 0.0,
            "cabinet_right_hinge": 0.0,
        },
    )


class TaskStateTests(unittest.TestCase):
    def test_state_copies_and_freezes_input_arrays(self) -> None:
        base = np.array([1.0, 2.0, 0.5])
        arm = np.zeros(7)
        state = TaskState(
            phase="test",
            base=base,
            arm_qpos=arm,
            gripper=0.04,
        )

        base[0] = 99.0
        arm[0] = 99.0
        self.assertEqual(state.base[0], 1.0)
        self.assertEqual(state.arm_qpos[0], 0.0)
        with self.assertRaises(ValueError):
            state.base[0] = 5.0

    def test_object_joint_update_preserves_other_joints(self) -> None:
        state = initial_state()
        updated = state.with_object_joint("cabinet_left_hinge", 1.57)

        self.assertEqual(updated.object_joints["cabinet_left_hinge"], 1.57)
        self.assertEqual(updated.object_joints["cabinet_right_hinge"], 0.0)
        self.assertEqual(state.object_joints["cabinet_left_hinge"], 0.0)

    def test_invalid_base_shape_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "exactly 3"):
            TaskState(
                phase="invalid",
                base=[0.0, 0.0],
                arm_qpos=np.zeros(7),
                gripper=0.04,
            )


class PrimitiveTests(unittest.TestCase):
    def test_move_base_uses_waypoints_and_preserves_other_state(self) -> None:
        state = initial_state()
        generated = move_base(
            state,
            waypoints=([1.0, 0.0, 0.0], [1.0, 1.0, 0.5]),
            steps_per_segment=5,
            phase="navigate",
        )

        self.assertEqual(len(generated), 8)
        np.testing.assert_allclose(generated[-1].base, [1.0, 1.0, 0.5])
        np.testing.assert_allclose(generated[-1].arm_qpos, state.arm_qpos)
        self.assertEqual(
            dict(generated[-1].object_joints),
            dict(state.object_joints),
        )
        np.testing.assert_allclose(state.base, [0.0, 0.0, 0.0])

    def test_move_arm_respects_maximum_joint_step(self) -> None:
        state = initial_state()
        target = np.array([0.1, -0.1, 0.2, -0.2, 0.1, 0.15, -0.1])
        generated = move_arm(
            state,
            waypoints=(target,),
            max_step=0.1,
            phase="reach",
        )
        path = [state.arm_qpos, *(item.arm_qpos for item in generated)]
        largest_step = max(
            float(np.max(np.abs(end - start)))
            for start, end in zip(path[:-1], path[1:])
        )

        self.assertLessEqual(largest_step, 0.1 + 1e-12)
        np.testing.assert_allclose(generated[-1].arm_qpos, target)

    def test_change_gripper_can_set_and_clear_active_target(self) -> None:
        state = initial_state()
        grasp = change_gripper(
            state,
            target=0.01,
            steps=5,
            phase="grasp",
            active_target="cabinet_left_handle",
        )
        release = change_gripper(
            grasp[-1],
            target=0.04,
            steps=5,
            phase="release",
            active_target=None,
        )

        self.assertEqual(grasp[-1].gripper, 0.01)
        self.assertEqual(grasp[-1].active_target, "cabinet_left_handle")
        self.assertEqual(release[-1].gripper, 0.04)
        self.assertIsNone(release[-1].active_target)


class ExecutorTests(unittest.TestCase):
    def test_demo_config_composes_all_foundation_primitives(self) -> None:
        config = load_task_config(DEMO_CONFIG)
        result = TaskExecutor().execute(config)

        self.assertEqual(result.task_name, "reusable_primitives_foundation_demo")
        self.assertEqual(len(result.states), 18)
        self.assertEqual(len(result.action_ranges), 4)
        self.assertEqual(
            [item.action for item in result.action_ranges],
            ["hold_pose", "move_base", "move_arm", "change_gripper"],
        )
        np.testing.assert_allclose(result.final_state.base, [1.0, 0.5, 0.2])
        self.assertEqual(result.final_state.gripper, 0.01)
        self.assertEqual(
            result.final_state.active_target,
            "cabinet_left_handle",
        )
        self.assertEqual(
            result.final_state.object_joints["cabinet_left_hinge"],
            0.0,
        )

    def test_unknown_action_has_clear_error(self) -> None:
        config = {
            "task_name": "bad_action",
            "initial_state": initial_state().to_dict(),
            "actions": [{"action": "invent_new_code"}],
        }

        with self.assertRaisesRegex(ValueError, "unknown action"):
            TaskExecutor().execute(config)

    def test_parameter_only_config_changes_the_generated_task(self) -> None:
        original = TaskExecutor().execute(load_task_config(DEMO_CONFIG))
        changed = TaskExecutor().execute(load_task_config(PARAMETER_CONFIG))

        self.assertEqual(len(original.states), 18)
        self.assertEqual(len(changed.states), 27)
        np.testing.assert_allclose(changed.final_state.base, [0.8, 0.3, 0.35])
        self.assertEqual(changed.final_state.gripper, 0.008)
        self.assertEqual(
            changed.final_state.active_target,
            "cabinet_right_handle",
        )


if __name__ == "__main__":
    unittest.main()
