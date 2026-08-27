from __future__ import annotations

import unittest

import numpy as np

from week7_note.task_system.mujoco_manipulation import (
    planar_hinge_orbit_base,
)


class PlanarHingeOrbitTests(unittest.TestCase):
    def test_quarter_turn_rotates_position_and_yaw(self) -> None:
        result = planar_hinge_orbit_base(
            base=[2.0, 0.0, 0.25],
            hinge_anchor_xy=[1.0, 0.0],
            signed_angle=np.pi / 2.0,
        )

        np.testing.assert_allclose(
            result,
            [1.0, 1.0, 0.25 + np.pi / 2.0],
            atol=1e-12,
        )

    def test_reverse_turn_returns_to_start(self) -> None:
        start = np.array([2.0, 0.0, 0.25])
        opened = planar_hinge_orbit_base(
            start,
            [1.0, 0.0],
            np.pi / 2.0,
        )
        closed = planar_hinge_orbit_base(
            opened,
            [1.0, 0.0],
            -np.pi / 2.0,
        )

        np.testing.assert_allclose(closed, start, atol=1e-12)

    def test_rejects_invalid_base_shape(self) -> None:
        with self.assertRaisesRegex(ValueError, "three finite values"):
            planar_hinge_orbit_base([1.0, 2.0], [0.0, 0.0], 0.5)


if __name__ == "__main__":
    unittest.main()
