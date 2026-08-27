from __future__ import annotations

import unittest

from week7_note.task_system.level5_integration import create_level5_runtime
from week8_note.scripts.articulation_discovery import discover_articulation
from week8_note.scripts.microwave_runtime import (
    ENTRY_HANDLE_PROXY,
    HANDLE_PROXY,
    create_microwave_runtime,
    ensure_week8_task_xml,
)


class ArticulationDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.model, cls.data, _, _ = create_level5_runtime()

    def test_discovers_microwave_door_hinge_from_handle(self) -> None:
        info = discover_articulation(
            self.model,
            self.data,
            "033_microwave_front_door_handle_bar",
        )

        self.assertEqual(info.target_body, "microwave_door")
        self.assertEqual(info.moving_body, "microwave_door")
        self.assertEqual(info.joint_name, "body_to_front_door")
        self.assertEqual(info.joint_type, "hinge")
        self.assertEqual(info.joint_axis_local, (0.0, 0.0, 1.0))
        self.assertEqual(info.joint_range, (0.0, 1.75))

    def test_discovers_slide_joint_from_microwave_tray(self) -> None:
        info = discover_articulation(
            self.model,
            self.data,
            "059_microwave_sliding_tray_front_lip",
        )

        self.assertEqual(info.moving_body, "microwave_tray")
        self.assertEqual(info.joint_name, "body_to_sliding_tray")
        self.assertEqual(info.joint_type, "slide")
        self.assertEqual(info.joint_range, (0.0, 0.22))

    def test_derived_runtime_adds_discoverable_handle_proxy(self) -> None:
        metadata = ensure_week8_task_xml()
        model, data, _, _ = create_microwave_runtime()
        info = discover_articulation(model, data, HANDLE_PROXY)

        self.assertEqual(info.joint_name, "body_to_front_door")
        self.assertEqual(info.joint_type, "hinge")
        self.assertTrue(metadata["task_xml"].endswith(
            "week8_note/xml/microwave_generalization.xml"
        ))

    def test_derived_runtime_discovers_entry_door_from_handle(self) -> None:
        metadata = ensure_week8_task_xml()
        model, data, _, _ = create_microwave_runtime()
        info = discover_articulation(model, data, ENTRY_HANDLE_PROXY)

        self.assertEqual(info.target_body, "entry_door")
        self.assertEqual(info.moving_body, "entry_door")
        self.assertEqual(info.joint_name, "frame_to_door")
        self.assertEqual(info.joint_type, "hinge")
        self.assertEqual(info.joint_axis_local, (0.0, 0.0, 1.0))
        self.assertEqual(info.joint_range, (0.0, 1.5708))
        self.assertEqual(metadata["entry_handle_proxy"], ENTRY_HANDLE_PROXY)


if __name__ == "__main__":
    unittest.main()
