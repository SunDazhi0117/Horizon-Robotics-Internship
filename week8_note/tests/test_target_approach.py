from __future__ import annotations

import unittest

import numpy as np
from scipy.spatial.transform import Rotation

from week6_note.scripts import run_panda_reach_cabinet_handle as cab
from week7_note.task_system.state import TaskState
from week8_note.scripts.microwave_runtime import (
    HANDLE_PROXY,
    create_microwave_runtime,
)
from week8_note.scripts.microwave_pose_variant import (
    BLOCKED_TASK_XML,
    MOVED_TASK_XML,
    ensure_preferred_base_blocked_xml,
    ensure_moved_microwave_xml,
)
from week7_note.task_system.executor import load_task_config, state_from_config
from week8_note.scripts.run_microwave_open_close import DEFAULT_CONFIG_PATH
from week8_note.scripts.target_approach import (
    TargetApproachActions,
    generate_target_relative_base_candidates,
    target_relative_base_goal,
)


REFERENCE_OFFSET = np.array([-0.11035779, 0.01626286, -0.00269677])
REFERENCE_ROTATION = np.array(
    [
        [-0.03796533, -0.15830286, 0.98666045],
        [0.00879656, -0.98738697, -0.15808094],
        [0.99924034, 0.00267762, 0.038879],
    ]
)
FRONT_ROTATION = Rotation.from_euler("z", 90, degrees=True).as_matrix()
MICROWAVE_HAND_OFFSET = FRONT_ROTATION @ REFERENCE_OFFSET
MICROWAVE_HAND_ROTATION = FRONT_ROTATION @ REFERENCE_ROTATION


def work_state() -> TaskState:
    return TaskState(
        phase="microwave_work_pose",
        base=[3.52167, 3.33753, 0.05],
        arm_qpos=cab.PANDA_HOME,
        gripper=0.04,
        object_joints={
            "left_hinge": 0.0,
            "right_hinge": 0.0,
            "microwave_hinge": 0.0,
        },
    )


def initial_state() -> TaskState:
    return TaskState(
        phase="initial",
        base=[3.62, 2.28, 0.0],
        arm_qpos=cab.PANDA_HOME,
        gripper=0.04,
        object_joints={
            "left_hinge": 0.0,
            "right_hinge": 0.0,
            "microwave_hinge": 0.0,
        },
    )


class TargetApproachTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _, _, cls.adapter, cls.validator = create_microwave_runtime()

    def test_staged_microwave_approach_has_no_overlap(self) -> None:
        actions = TargetApproachActions(self.adapter, self.validator)
        generated = actions.approach_target(
            work_state(),
            target_geom=HANDLE_PROXY,
            hand_offset=MICROWAVE_HAND_OFFSET,
            hand_rotation=MICROWAVE_HAND_ROTATION,
            approach_direction=[0.0, -1.0, 0.0],
            standoff_distances=[0.45, 0.32, 0.22, 0.14, 0.09],
            max_step=0.03,
        )

        self.assertGreater(len(generated), 50)
        final_sample = self.validator.validate(
            generated[-1],
            step_index=len(generated) - 1,
        )
        self.assertEqual(final_sample["environment_visual_overlap_count"], 0)

    def test_target_relative_goal_follows_translation_and_rotation(self) -> None:
        offset = [-0.3, -0.6]
        identity_goal = target_relative_base_goal(
            [3.0, 4.0, 1.2],
            np.eye(3),
            base_offset=offset,
            yaw_offset=0.05,
            reference_yaw=0.0,
        )
        rotated_goal = target_relative_base_goal(
            [5.0, 7.0, 1.2],
            Rotation.from_euler("z", 90, degrees=True).as_matrix(),
            base_offset=offset,
            yaw_offset=0.05,
            reference_yaw=0.0,
        )

        np.testing.assert_allclose(identity_goal, [2.7, 3.4, 0.05])
        np.testing.assert_allclose(
            rotated_goal,
            [5.6, 6.7, np.pi / 2.0 + 0.05],
        )

    def test_polar_search_rule_generates_offsets_and_detours(self) -> None:
        candidates = generate_target_relative_base_candidates(
            stand_distance=0.6,
            center_angle_degrees=-90.0,
            angle_offsets_degrees=[0.0, 90.0],
            detour_distance=1.2,
        )

        self.assertEqual([item["name"] for item in candidates], ["auto_01", "auto_02"])
        np.testing.assert_allclose(candidates[0]["base_offset"], [0.0, -0.6], atol=1e-9)
        np.testing.assert_allclose(candidates[0]["path_offsets"][0], [0.0, -1.2], atol=1e-9)
        np.testing.assert_allclose(candidates[1]["base_offset"], [0.6, 0.0], atol=1e-9)

    def test_move_near_microwave_uses_target_relative_goal(self) -> None:
        actions = TargetApproachActions(self.adapter, self.validator)
        generated = actions.move_near_target(
            initial_state(),
            target_geom=HANDLE_PROXY,
            base_offset=[-0.32700001, -0.60800185],
            yaw_offset=0.05,
            steps_per_segment=51,
        )

        self.assertEqual(len(generated), 50)
        np.testing.assert_allclose(
            generated[-1].base,
            [3.52167, 3.33753, 0.05],
            atol=1e-6,
        )
        final_sample = self.validator.validate(
            generated[-1],
            step_index=len(generated) - 1,
        )
        self.assertEqual(final_sample["environment_visual_overlap_count"], 0)

    def test_same_config_repositions_base_for_moved_microwave(self) -> None:
        ensure_moved_microwave_xml()
        _, _, adapter, validator = create_microwave_runtime(MOVED_TASK_XML)
        actions = TargetApproachActions(adapter, validator)
        config = load_task_config(DEFAULT_CONFIG_PATH)
        state = state_from_config(config["initial_state"])
        parameters = dict(config["actions"][1])
        self.assertEqual(parameters.pop("action"), "move_near_target")
        generated = actions.move_near_target(state, **parameters)

        np.testing.assert_allclose(
            generated[-1].base,
            [3.83123890, 3.20665270, 0.22453293],
            atol=1e-6,
        )
        self.assertFalse(
            np.allclose(generated[-1].base, [3.52167, 3.33753, 0.05])
        )
        final_sample = validator.validate(
            generated[-1],
            step_index=len(generated) - 1,
        )
        self.assertEqual(final_sample["environment_visual_overlap_count"], 0)

    def test_blocked_preferred_base_uses_backup_route(self) -> None:
        ensure_preferred_base_blocked_xml()
        _, _, adapter, validator = create_microwave_runtime(BLOCKED_TASK_XML)
        actions = TargetApproachActions(adapter, validator)
        config = load_task_config(
            "week8_note/configs/"
            "microwave_open_hold_close_candidate_fallback.yaml"
        )
        state = state_from_config(config["initial_state"])
        parameters = dict(config["actions"][1])
        self.assertEqual(parameters.pop("action"), "move_near_target")
        generated = actions.move_near_target(state, **parameters)

        self.assertEqual(
            generated[-1].phase,
            "navigate_to_microwave_backup_right",
        )
        np.testing.assert_allclose(
            generated[-1].base,
            [4.15188154, 3.27131594, 0.22453293],
            atol=1e-6,
        )
        self.assertEqual(len(generated), 100)
        final_sample = validator.validate(
            generated[-1],
            step_index=len(generated) - 1,
        )
        self.assertEqual(final_sample["environment_visual_overlap_count"], 0)

    def test_automatic_search_skips_blocked_first_candidate(self) -> None:
        ensure_preferred_base_blocked_xml()
        _, _, adapter, validator = create_microwave_runtime(BLOCKED_TASK_XML)
        actions = TargetApproachActions(adapter, validator)
        config = load_task_config(
            "week8_note/configs/microwave_open_hold_close_auto_candidates.yaml"
        )
        state = state_from_config(config["initial_state"])
        parameters = dict(config["actions"][1])
        self.assertEqual(parameters.pop("action"), "move_near_target")
        generated = actions.move_near_target(state, **parameters)

        self.assertEqual(
            generated[-1].phase,
            "navigate_to_microwave_auto_02",
        )
        np.testing.assert_allclose(
            generated[-1].base,
            [4.15188154, 3.27131594, 0.22453293],
            atol=1e-6,
        )
        self.assertEqual(len(generated), 100)
        final_sample = validator.validate(
            generated[-1],
            step_index=len(generated) - 1,
        )
        self.assertEqual(final_sample["environment_visual_overlap_count"], 0)

        report = actions.last_base_candidate_report
        self.assertEqual(report["mode"], "automatic_search")
        self.assertEqual(report["candidate_count"], 5)
        self.assertEqual(report["attempted_candidate_count"], 2)
        self.assertEqual(report["selected_candidate"], "auto_02")
        self.assertEqual(report["attempts"][0]["status"], "rejected")
        self.assertIn(
            "visual overlap detected",
            report["attempts"][0]["failure_reason"],
        )
        self.assertEqual(report["attempts"][1]["status"], "selected")
        self.assertGreater(report["attempts"][1]["route_length"], 0.0)


if __name__ == "__main__":
    unittest.main()
