from __future__ import annotations

import unittest

import numpy as np

from week7_note.task_system.level5_integration import (
    create_level5_runtime,
    load_level5_states,
)
from week7_note.task_system.mujoco_manipulation import (
    MujocoManipulationActions,
)


class Level5TaskSystemIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.states = load_level5_states()
        _, _, cls.adapter, cls.validator = create_level5_runtime()

    def test_complete_saved_trajectory_converts_to_task_states(self) -> None:
        self.assertEqual(len(self.states), 429)
        self.assertEqual(
            set(self.states[0].object_joints),
            {"left_hinge", "right_hinge"},
        )

    def test_first_state_round_trips_through_real_mujoco_data(self) -> None:
        state = self.states[0]
        self.adapter.apply(state)
        actual = self.adapter.read_state(state)

        np.testing.assert_allclose(actual.base, state.base, atol=1e-12)
        np.testing.assert_allclose(
            actual.arm_qpos,
            state.arm_qpos,
            atol=1e-12,
        )
        self.assertAlmostEqual(actual.gripper, state.gripper, places=12)
        self.assertEqual(
            dict(actual.object_joints),
            dict(state.object_joints),
        )

    def test_real_validator_checks_full_environment(self) -> None:
        state = self.states[0]
        sample = self.validator.validate(state, step_index=0)

        self.assertEqual(len(self.validator.environment_geom_ids), 93)
        self.assertEqual(sample["environment_visual_overlap_count"], 0)
        self.assertEqual(
            sample["forbidden_active_target_contact_count"],
            0,
        )
        self.assertLessEqual(sample["base_command_error"], 1e-12)
        self.assertGreaterEqual(
            sample["active_target_unique_finger_contact_count"],
            2,
        )

    def test_reusable_grasp_target_closes_on_left_handle(self) -> None:
        actions = MujocoManipulationActions(self.adapter, self.validator)
        pregrasp = self.states[335]
        generated = actions.grasp_target(
            pregrasp,
            target_geom="level5_left_handle_sleeve",
            capture_current_transform=True,
            closed_gripper=0.023711985,
            close_steps=17,
            minimum_final_finger_contacts=2,
            phase="test_reusable_grasp",
        )

        self.assertEqual(len(generated), 17)
        self.assertAlmostEqual(generated[-1].gripper, 0.023711985)
        self.assertEqual(
            generated[-1].active_target,
            "level5_left_handle_sleeve",
        )

    def test_reusable_hinge_follow_keeps_short_grasp(self) -> None:
        actions = MujocoManipulationActions(self.adapter, self.validator)
        grasped = self.states[351]
        accepted_short_target = self.states[356]
        target_angle = accepted_short_target.object_joints["left_hinge"]
        generated = actions.follow_hinge_joint(
            grasped,
            joint_name="left_hinge",
            moving_body="cabinet_left_door",
            target_angle=target_angle,
            samples=5,
            base_target=accepted_short_target.base,
            max_joint_step=0.15,
            minimum_each_finger_contacts=2,
            phase="test_reusable_hinge_follow",
        )

        self.assertEqual(len(generated), 4)
        self.assertAlmostEqual(
            generated[-1].object_joints["left_hinge"],
            target_angle,
        )


if __name__ == "__main__":
    unittest.main()
