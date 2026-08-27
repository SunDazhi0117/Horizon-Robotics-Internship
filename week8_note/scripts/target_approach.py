"""Collision-checked target approach built on Week7 manipulation actions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

from week7_note.task_system.mujoco_manipulation import (
    MujocoManipulationActions,
)
from week7_note.task_system.primitives import move_arm, move_base
from week7_note.task_system.state import TaskState


def target_relative_base_goal(
    target_position: Sequence[float],
    target_rotation: Sequence[Sequence[float]] | Sequence[float],
    *,
    base_offset: Sequence[float],
    yaw_offset: float,
    reference_yaw: float,
    heading_axis: Sequence[float] = (1.0, 0.0, 0.0),
) -> np.ndarray:
    """Compute an absolute [x, y, yaw] goal in a target geom's frame."""

    position = np.asarray(target_position, dtype=float)
    if position.shape != (3,) or not np.all(np.isfinite(position)):
        raise ValueError("target_position must contain three finite values")
    rotation = np.asarray(target_rotation, dtype=float)
    if rotation.size != 9:
        raise ValueError("target_rotation must contain nine values")
    rotation = rotation.reshape(3, 3)
    if not np.all(np.isfinite(rotation)) or not np.allclose(
        rotation.T @ rotation,
        np.eye(3),
        atol=1e-5,
    ):
        raise ValueError("target_rotation must be an orthonormal matrix")

    offset = np.asarray(base_offset, dtype=float)
    if offset.shape == (2,):
        offset = np.array([offset[0], offset[1], 0.0], dtype=float)
    if offset.shape != (3,) or not np.all(np.isfinite(offset)):
        raise ValueError("base_offset must contain two or three finite values")

    local_heading = np.asarray(heading_axis, dtype=float)
    if local_heading.shape != (3,) or not np.all(np.isfinite(local_heading)):
        raise ValueError("heading_axis must contain three finite values")
    world_heading = rotation @ local_heading
    horizontal_norm = float(np.linalg.norm(world_heading[:2]))
    if horizontal_norm <= 1e-12:
        raise ValueError("heading_axis must have a horizontal world component")

    target_yaw = float(np.arctan2(world_heading[1], world_heading[0]))
    raw_goal_yaw = target_yaw + float(yaw_offset)
    reference = float(reference_yaw)
    if not np.isfinite(raw_goal_yaw) or not np.isfinite(reference):
        raise ValueError("yaw values must be finite")
    # Use the equivalent angle nearest to the current yaw to avoid a 2-pi turn.
    yaw_delta = float(
        np.arctan2(
            np.sin(raw_goal_yaw - reference),
            np.cos(raw_goal_yaw - reference),
        )
    )
    world_position = position + rotation @ offset
    return np.array(
        [world_position[0], world_position[1], reference + yaw_delta],
        dtype=float,
    )


def generate_target_relative_base_candidates(
    *,
    stand_distance: float,
    center_angle_degrees: float,
    angle_offsets_degrees: Sequence[float],
    detour_distance: float | None = None,
) -> list[dict[str, object]]:
    """Generate ordered target-relative candidates from a polar search rule."""

    radius = float(stand_distance)
    center_angle = float(center_angle_degrees)
    if not np.isfinite(radius) or radius <= 0.0:
        raise ValueError("stand_distance must be positive and finite")
    if not np.isfinite(center_angle):
        raise ValueError("center_angle_degrees must be finite")
    angle_offsets = [float(value) for value in angle_offsets_degrees]
    if not angle_offsets or not np.all(np.isfinite(angle_offsets)):
        raise ValueError(
            "angle_offsets_degrees must contain finite values"
        )

    outer_radius = None
    if detour_distance is not None:
        outer_radius = float(detour_distance)
        if not np.isfinite(outer_radius) or outer_radius <= radius:
            raise ValueError(
                "detour_distance must be finite and greater than stand_distance"
            )

    candidates: list[dict[str, object]] = []
    for index, angle_offset in enumerate(angle_offsets):
        angle = np.deg2rad(center_angle + angle_offset)
        direction = np.array([np.cos(angle), np.sin(angle)], dtype=float)
        candidate: dict[str, object] = {
            "name": f"auto_{index + 1:02d}",
            "base_offset": (direction * radius).tolist(),
        }
        if outer_radius is not None:
            candidate["path_offsets"] = [
                (direction * outer_radius).tolist()
            ]
        candidates.append(candidate)
    return candidates


class TargetApproachActions(MujocoManipulationActions):
    """Add a staged pre-grasp action to the reusable action registry."""

    def action_registry(self) -> dict[str, object]:
        actions = super().action_registry()
        actions["move_near_target"] = self.move_near_target
        actions["approach_target"] = self.approach_target
        actions["retreat_from_target"] = self.retreat_from_target
        return actions

    def move_near_target(
        self,
        state: TaskState,
        *,
        target_geom: str,
        base_offset: Sequence[float] | None = None,
        base_candidates: Sequence[Mapping[str, object]] | None = None,
        candidate_search: Mapping[str, object] | None = None,
        yaw_offset: float = 0.0,
        heading_axis: Sequence[float] = (1.0, 0.0, 0.0),
        steps_per_segment: int = 31,
        phase: str = "move_near_target",
    ) -> list[TaskState]:
        """Move to the first collision-free target-relative base candidate."""

        target_geom = str(target_geom).strip()
        if not target_geom:
            raise ValueError("target_geom must be non-empty")
        self._geom_id(target_geom)
        supplied_modes = sum(
            value is not None
            for value in (base_offset, base_candidates, candidate_search)
        )
        if supplied_modes != 1:
            raise ValueError(
                "provide exactly one of base_offset, base_candidates, or "
                "candidate_search"
            )

        if candidate_search is not None:
            if not isinstance(candidate_search, Mapping):
                raise ValueError("candidate_search must be a mapping")
            try:
                candidates = generate_target_relative_base_candidates(
                    **dict(candidate_search)
                )
            except TypeError as error:
                raise ValueError(f"invalid candidate_search: {error}") from error
            label_candidate = True
            selection_mode = "automatic_search"
        elif base_candidates is None:
            if base_offset is None:
                raise ValueError("base_offset or base_candidates is required")
            candidates = [
                {
                    "name": "direct",
                    "base_offset": base_offset,
                    "yaw_offset": yaw_offset,
                    "heading_axis": heading_axis,
                }
            ]
            label_candidate = False
            selection_mode = "single_offset"
        else:
            if not base_candidates:
                raise ValueError("base_candidates cannot be empty")
            candidates = list(base_candidates)
            label_candidate = True
            selection_mode = "configured_candidates"

        failures: list[str] = []
        attempts: list[dict[str, object]] = []
        report: dict[str, object] = {
            "mode": selection_mode,
            "target_geom": target_geom,
            "candidate_count": len(candidates),
            "selected_candidate": None,
            "attempts": attempts,
        }
        if candidate_search is not None:
            report["search_rule"] = dict(candidate_search)
        self.last_base_candidate_report = report
        for index, candidate in enumerate(candidates):
            if not isinstance(candidate, Mapping):
                raise ValueError(f"base_candidates[{index}] must be a mapping")
            name = str(candidate.get("name", f"candidate_{index + 1}")).strip()
            if not name:
                raise ValueError(f"base_candidates[{index}].name cannot be empty")
            candidate_offset = candidate.get("base_offset")
            if candidate_offset is None:
                raise ValueError(
                    f"base candidate {name!r} is missing base_offset"
                )
            candidate_yaw = float(candidate.get("yaw_offset", yaw_offset))
            candidate_heading = candidate.get("heading_axis", heading_axis)
            raw_path_offsets = candidate.get("path_offsets", ())
            if not isinstance(raw_path_offsets, Sequence) or isinstance(
                raw_path_offsets,
                (str, bytes),
            ):
                raise ValueError(
                    f"base candidate {name!r} path_offsets must be a sequence"
                )
            path_offsets = list(raw_path_offsets)
            candidate_phase = f"{phase}_{name}" if label_candidate else phase
            attempt: dict[str, object] | None = None

            try:
                self.adapter.apply(state)
                target_position, target_rotation = self._geom_pose(target_geom)
                goals = [
                    target_relative_base_goal(
                        target_position,
                        target_rotation,
                        base_offset=offset,
                        yaw_offset=candidate_yaw,
                        reference_yaw=float(state.base[2]),
                        heading_axis=candidate_heading,
                    )
                    for offset in [*path_offsets, candidate_offset]
                ]
                route_points = [state.base[:2], *(goal[:2] for goal in goals)]
                route_length = float(
                    sum(
                        np.linalg.norm(end - start)
                        for start, end in zip(
                            route_points[:-1],
                            route_points[1:],
                        )
                    )
                )
                attempt = {
                    "candidate_index": index,
                    "name": name,
                    "base_offset": np.asarray(
                        candidate_offset,
                        dtype=float,
                    ).tolist(),
                    "path_offsets": [
                        np.asarray(offset, dtype=float).tolist()
                        for offset in path_offsets
                    ],
                    "world_waypoints": [goal.tolist() for goal in goals],
                    "route_length": route_length,
                }
                generated = move_base(
                    state,
                    waypoints=goals,
                    steps_per_segment=steps_per_segment,
                    phase=candidate_phase,
                )
                self._validate_states(generated, previous_state=state)
                attempt["status"] = "selected"
                attempt["generated_state_count"] = len(generated)
                attempts.append(attempt)
                report["selected_candidate"] = name
                report["attempted_candidate_count"] = len(attempts)
                return generated
            except ValueError as error:
                failures.append(f"{name}: {error}")
                rejected = attempt
                if rejected is None:
                    rejected = {
                        "candidate_index": index,
                        "name": name,
                    }
                rejected["status"] = "rejected"
                rejected["failure_reason"] = str(error)
                attempts.append(rejected)

        report["attempted_candidate_count"] = len(attempts)
        raise ValueError(
            "no collision-free base candidate was found; " + "; ".join(failures)
        )

    def _move_through_standoffs(
        self,
        state: TaskState,
        *,
        target_geom: str,
        local_offset: np.ndarray,
        local_rotation: np.ndarray,
        direction: np.ndarray,
        distances: list[float],
        max_step: float,
        phase: str,
    ) -> list[TaskState]:
        generated: list[TaskState] = []
        previous = state
        for stage_index, distance in enumerate(distances):
            self.adapter.apply(previous)
            target_pos, target_rot = self._geom_pose(target_geom)
            desired_pos = target_pos + target_rot @ (
                local_offset + direction * distance
            )
            desired_rot = target_rot @ local_rotation
            solved = self._solve_arm_pose(
                previous,
                desired_pos,
                desired_rot,
                continuity_weight=0.001,
                max_nfev=1600,
                position_tolerance=0.004,
                rotation_tolerance=0.02,
            )
            segment = move_arm(
                previous,
                waypoints=[solved],
                max_step=max_step,
                phase=f"{phase}_{stage_index + 1}",
            )
            self._validate_states(segment, previous_state=previous)
            generated.extend(segment)
            previous = segment[-1]
        return generated

    def _approach_parameters(
        self,
        *,
        target_geom: str,
        hand_offset: Sequence[float],
        hand_rotation: Sequence[Sequence[float]] | Sequence[float],
        approach_direction: Sequence[float],
        standoff_distances: Sequence[float],
    ) -> tuple[str, np.ndarray, np.ndarray, np.ndarray, list[float]]:
        target_geom = str(target_geom).strip()
        if not target_geom:
            raise ValueError("target_geom must be non-empty")
        self._geom_id(target_geom)

        local_offset = np.asarray(hand_offset, dtype=float)
        if local_offset.shape != (3,) or not np.all(np.isfinite(local_offset)):
            raise ValueError("hand_offset must contain three finite values")
        local_rotation = self._rotation_matrix(
            hand_rotation,
            name="hand_rotation",
        )
        direction = np.asarray(approach_direction, dtype=float)
        if direction.shape != (3,) or not np.all(np.isfinite(direction)):
            raise ValueError(
                "approach_direction must contain three finite values"
            )
        norm = float(np.linalg.norm(direction))
        if norm <= 1e-12:
            raise ValueError("approach_direction cannot be zero")
        direction = direction / norm

        distances = [float(value) for value in standoff_distances]
        if not distances or not np.all(np.isfinite(distances)):
            raise ValueError(
                "standoff_distances must contain finite values"
            )
        if any(value <= 0.0 for value in distances):
            raise ValueError("standoff distances must be positive")
        return (
            target_geom,
            local_offset,
            local_rotation,
            direction,
            distances,
        )

    def approach_target(
        self,
        state: TaskState,
        *,
        target_geom: str,
        hand_offset: Sequence[float],
        hand_rotation: Sequence[Sequence[float]] | Sequence[float],
        approach_direction: Sequence[float],
        standoff_distances: Sequence[float],
        max_step: float = 0.03,
        phase: str = "approach_target",
    ) -> list[TaskState]:
        """Approach a target through progressively closer Cartesian stages.

        Each stage is solved with IK from the previous stage. Every dense
        joint-space segment is rejected if the existing Panda validator finds
        an environment overlap or forbidden target contact.
        """

        (
            target_geom,
            local_offset,
            local_rotation,
            direction,
            distances,
        ) = self._approach_parameters(
            target_geom=target_geom,
            hand_offset=hand_offset,
            hand_rotation=hand_rotation,
            approach_direction=approach_direction,
            standoff_distances=standoff_distances,
        )
        if any(end >= start for start, end in zip(distances[:-1], distances[1:])):
            raise ValueError(
                "standoff_distances must be strictly decreasing"
            )
        return self._move_through_standoffs(
            state,
            target_geom=target_geom,
            local_offset=local_offset,
            local_rotation=local_rotation,
            direction=direction,
            distances=distances,
            max_step=max_step,
            phase=phase,
        )

    def retreat_from_target(
        self,
        state: TaskState,
        *,
        target_geom: str,
        hand_offset: Sequence[float],
        hand_rotation: Sequence[Sequence[float]] | Sequence[float],
        approach_direction: Sequence[float],
        standoff_distances: Sequence[float],
        max_step: float = 0.03,
        phase: str = "retreat_from_target",
    ) -> list[TaskState]:
        """Move away from a target through increasing standoff distances."""

        (
            target_geom,
            local_offset,
            local_rotation,
            direction,
            distances,
        ) = self._approach_parameters(
            target_geom=target_geom,
            hand_offset=hand_offset,
            hand_rotation=hand_rotation,
            approach_direction=approach_direction,
            standoff_distances=standoff_distances,
        )
        if any(end <= start for start, end in zip(distances[:-1], distances[1:])):
            raise ValueError(
                "retreat standoff_distances must be strictly increasing"
            )
        cleared_state = state.with_updates(active_target=None)
        return self._move_through_standoffs(
            cleared_state,
            target_geom=target_geom,
            local_offset=local_offset,
            local_rotation=local_rotation,
            direction=direction,
            distances=distances,
            max_step=max_step,
            phase=phase,
        )
