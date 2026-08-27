#!/usr/bin/env python3
"""Level 5: sequentially open both cabinet doors without visual overlap.

The Panda opens the right door from the accepted Level 3 fixed-base grasp,
releases and retreats, moves around the cabinet with a tucked arm, then locks
at a mirrored left work station and opens the left door. Every dense state is
checked against the complete cabinet geometry before it is rendered.
"""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco
import numpy as np
from PIL import Image
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from week6_note.scripts import run_panda_handle_pull_minimal as minimal
from week6_note.scripts import run_panda_reach_cabinet_handle as cab
from week7_note.scripts import level_validation_helpers as validation
from week7_note.scripts import run_level_2_handle_follow_open_90 as level_2
from week7_note.scripts import run_level_3_fixed_base_arm_only_open_90 as level_3

XML_DIR = ROOT / "xml"
IMAGE_DIR = ROOT / "assets" / "images"
VIDEO_DIR = ROOT / "assets" / "videos"
RESULT_DIR = ROOT / "assets" / "results"

TASK_XML = XML_DIR / "level_5_sequential_open_both_doors.xml"
GIF_PATH = VIDEO_DIR / "level_5_sequential_open_both_doors.gif"
TOP_GIF_PATH = VIDEO_DIR / "level_5_sequential_open_both_doors_top_view.gif"
RIGHT_GIF_PATH = (
    VIDEO_DIR / "level_5_sequential_open_both_doors_right_side_view.gif"
)
SUMMARY_PATH = RESULT_DIR / "level_5_sequential_open_both_doors_summary.json"
TRAJECTORY_PATH = RESULT_DIR / "level_5_sequential_open_both_doors_trajectory.json"
FRAME_SHEET_PATH = IMAGE_DIR / "level_5_sequential_open_both_doors_frames_sheet.png"
TOP_FRAME_SHEET_PATH = IMAGE_DIR / "level_5_sequential_open_both_doors_top_frames_sheet.png"
RIGHT_FRAME_SHEET_PATH = (
    IMAGE_DIR
    / "level_5_sequential_open_both_doors_right_side_frames_sheet.png"
)

LEFT_HANDLE = "level5_left_handle_sleeve"
LEFT_SUPPORTS = (
    "level5_left_handle_support_upper",
    "level5_left_handle_support_lower",
    "level5_left_handle_mount_upper",
    "level5_left_handle_mount_lower",
)
RIGHT_HANDLE = minimal.HANDLE_SLEEVE_GEOM

LEFT_WORK_BASE = np.array([4.49, 3.60, -0.05])
LEFT_OPEN_END_BASE = np.array([4.20, 3.30, -0.45])
RIGHT_WORK_BASE = level_3.FIXED_BASE.copy()
RIGHT_RETREAT_BASE = np.array([3.85, 2.30, 0.05])
LEFT_STAGING_BASE = np.array([3.40, 3.20, -0.05])
LEFT_PREAPPROACH_BASE = np.array([3.40, 3.60, -0.05])
TARGET_ANGLE = np.pi / 2.0
LEFT_GRASP_THETA = np.radians(-45.0)
LEFT_OPEN_SAMPLE_COUNT = 65
GRASP_FINGER = level_3.GRASP_FINGER
OPEN_FINGER = cab.FINGER_OPEN_START
FRAME_DURATION_MS = 92


def render_right_side(
    model: mujoco.MjModel,
    data: mujoco.MjData,
) -> np.ndarray:
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    camera.lookat[:] = [4.38, 3.00, 0.70]
    camera.distance = 1.85
    camera.azimuth = 55.0
    camera.elevation = -24.0
    with mujoco.Renderer(model, width=820, height=620) as renderer:
        renderer.update_scene(data, camera=camera)
        return renderer.render()


def ensure_level_5_xml() -> None:
    minimal.ensure_minimal_task_xml()
    tree = ET.parse(minimal.TASK_XML)
    root = tree.getroot()
    root.set("model", "level_5_sequential_open_both_doors")

    compiler = root.find("compiler")
    mesh_dir = (
        (minimal.TASK_XML.parent / compiler.get("meshdir", "")).resolve()
        if compiler is not None
        else minimal.TASK_XML.parent
    )
    for mesh in root.findall("./asset/mesh"):
        file_name = mesh.get("file")
        if file_name and not Path(file_name).is_absolute():
            mesh.set("file", str((mesh_dir / file_name).resolve()))
    if compiler is not None:
        compiler.attrib.pop("meshdir", None)

    left_door = root.find(".//body[@name='cabinet_left_door']")
    if left_door is None:
        raise RuntimeError("cabinet_left_door is missing")

    for geom in list(left_door.findall("geom")):
        name = geom.get("name", "")
        if name in {LEFT_HANDLE, *LEFT_SUPPORTS}:
            left_door.remove(geom)
        elif name == "007_double_door_cabinet_left_door_left_door_slab":
            geom.set("contype", "1")
            geom.set("conaffinity", "1")

    ET.SubElement(
        left_door,
        "geom",
        {
            "name": LEFT_HANDLE,
            "type": "box",
            "pos": "-0.113 -0.418 0.600",
            "size": "0.024 0.022 0.135",
            "rgba": "0.88 0.86 0.76 1",
            "contype": "2",
            "conaffinity": "3",
        },
    )
    for name, z in (
        ("level5_left_handle_support_upper", 0.695),
        ("level5_left_handle_support_lower", 0.505),
    ):
        ET.SubElement(
            left_door,
            "geom",
            {
                "name": name,
                "type": "box",
                "pos": f"-0.066 -0.418 {z}",
                "size": "0.050 0.011 0.012",
                "rgba": "0.82 0.80 0.72 1",
                "contype": "0",
                "conaffinity": "0",
            },
        )
    for name, z in (
        ("level5_left_handle_mount_upper", 0.695),
        ("level5_left_handle_mount_lower", 0.505),
    ):
        ET.SubElement(
            left_door,
            "geom",
            {
                "name": name,
                "type": "box",
                "pos": f"-0.020 -0.418 {z}",
                "size": "0.006 0.032 0.026",
                "rgba": "0.76 0.74 0.66 1",
                "contype": "0",
                "conaffinity": "0",
            },
        )

    XML_DIR.mkdir(parents=True, exist_ok=True)
    tree.write(TASK_XML, encoding="utf-8", xml_declaration=True)


def joint_value(model: mujoco.MjModel, data: mujoco.MjData, name: str) -> float:
    joint_id = minimal.obj_id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
    return float(data.qpos[int(model.jnt_qposadr[joint_id])])


def set_state(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    base: np.ndarray,
    qpos: np.ndarray,
    finger: float,
    left_hinge: float,
    right_hinge: float,
) -> None:
    cab.set_scene_qpos(
        model,
        data,
        base,
        qpos,
        finger,
        right_hinge_angle=right_hinge,
    )
    left_id = minimal.obj_id(model, mujoco.mjtObj.mjOBJ_JOINT, "left_hinge")
    data.qpos[int(model.jnt_qposadr[left_id])] = left_hinge
    mujoco.mj_forward(model, data)


def actual_base_pose(model: mujoco.MjModel, data: mujoco.MjData) -> np.ndarray:
    return np.array(
        [
            cab.MOBILE_BASE_START[0] + joint_value(model, data, "mobile_base_x"),
            cab.MOBILE_BASE_START[1] + joint_value(model, data, "mobile_base_y"),
            joint_value(model, data, "mobile_base_yaw"),
        ]
    )


def environment_target_ids(model: mujoco.MjModel) -> list[int]:
    panda_ids = set(validation.panda_geom_ids(model))
    excluded = {"reference_ground", "000_Mesh_0"}
    return [
        geom_id
        for geom_id in range(model.ngeom)
        if geom_id not in panda_ids
        and (
                mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, geom_id)
                or ""
            )
        not in excluded
    ]


def handle_contacts(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    handle_name: str,
) -> tuple[set[str], list[dict]]:
    handle_id = minimal.obj_id(
        model,
        mujoco.mjtObj.mjOBJ_GEOM,
        handle_name,
    )
    finger_bodies: set[str] = set()
    forbidden: list[dict] = []
    for index in range(data.ncon):
        contact = data.contact[index]
        geom1 = int(contact.geom1)
        geom2 = int(contact.geom2)
        if handle_id not in {geom1, geom2}:
            continue
        other = geom2 if geom1 == handle_id else geom1
        body = validation.body_name_for_geom(model, other)
        if not body.startswith(validation.PANDA_BODY_PREFIXES):
            continue
        record = {
            "other_geom": validation.geom_name(model, other),
            "other_body": body,
            "distance": float(contact.dist),
        }
        if body in validation.ALLOWED_HANDLE_BODIES:
            finger_bodies.add(body)
        else:
            forbidden.append(record)
    return finger_bodies, forbidden


def validate_state(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    phase: str,
    step_index: int,
    base: np.ndarray,
    qpos: np.ndarray,
    finger: float,
    left_hinge: float,
    right_hinge: float,
    panda_ids: list[int],
    environment_ids: list[int],
    active_handle: str | None,
    previous_qpos: np.ndarray | None,
) -> dict:
    set_state(
        model,
        data,
        base,
        qpos,
        finger,
        left_hinge,
        right_hinge,
    )
    overlap = validation.visual_overlap_sample(
        model,
        data,
        phase,
        step_index,
        panda_ids,
        environment_ids,
        allowed_finger_target_geoms={LEFT_HANDLE, RIGHT_HANDLE},
    )
    contact_bodies: set[str] = set()
    forbidden_contacts: list[dict] = []
    distance = None
    if active_handle is not None:
        contact_bodies, forbidden_contacts = handle_contacts(
            model,
            data,
            active_handle,
        )
        distance = float(
            np.linalg.norm(
                minimal.gripper_center(model, data)
                - minimal.geom_pos(model, data, active_handle)
            )
        )
    actual_base = actual_base_pose(model, data)
    return {
        "phase": phase,
        "step_index": step_index,
        "base": actual_base.tolist(),
        "commanded_base": base.tolist(),
        "base_command_error": float(np.linalg.norm(actual_base - base)),
        "panda_qpos": qpos.tolist(),
        "finger": float(finger),
        "left_hinge": float(left_hinge),
        "right_hinge": float(right_hinge),
        "active_handle": active_handle,
        "gripper_to_active_handle_distance": distance,
        "active_handle_finger_contacts": sorted(contact_bodies),
        "active_handle_unique_finger_contact_count": len(contact_bodies),
        "forbidden_active_handle_contacts": forbidden_contacts,
        "forbidden_active_handle_contact_count": len(forbidden_contacts),
        "environment_visual_overlap_count": overlap["visual_overlap_count"],
        "environment_visual_overlaps": overlap["visual_overlaps"],
        "max_joint_step_from_previous": (
            0.0
            if previous_qpos is None
            else float(np.max(np.abs(qpos - previous_qpos)))
        ),
    }


def arm_bounds(model: mujoco.MjModel) -> tuple[np.ndarray, np.ndarray]:
    return level_3.arm_joint_bounds(model)


def solve_arm_pose(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    base: np.ndarray,
    left_hinge: float,
    right_hinge: float,
    seed: np.ndarray,
    desired_pos: np.ndarray,
    desired_rot: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
) -> tuple[np.ndarray, dict]:
    def residual(qpos: np.ndarray) -> np.ndarray:
        set_state(
            model,
            data,
            base,
            qpos,
            GRASP_FINGER,
            left_hinge,
            right_hinge,
        )
        hand_pos, hand_rot = level_2.body_pose(model, data, "hand")
        position_error = hand_pos - desired_pos
        rotation_error = Rotation.from_matrix(
            desired_rot.T @ hand_rot
        ).as_rotvec()
        continuity = (qpos - seed) / 0.55
        return np.concatenate(
            (
                position_error * 100.0,
                rotation_error * 30.0,
                continuity * 0.006,
            )
        )

    result = least_squares(
        residual,
        np.clip(seed, lower, upper),
        bounds=(lower, upper),
        xtol=1e-11,
        ftol=1e-11,
        gtol=1e-11,
        max_nfev=900,
    )
    set_state(
        model,
        data,
        base,
        result.x,
        GRASP_FINGER,
        left_hinge,
        right_hinge,
    )
    hand_pos, hand_rot = level_2.body_pose(model, data, "hand")
    return result.x, {
        "ik_success": bool(result.success),
        "hand_position_error": float(np.linalg.norm(hand_pos - desired_pos)),
        "hand_rotation_error": float(
            np.linalg.norm(
                Rotation.from_matrix(desired_rot.T @ hand_rot).as_rotvec()
            )
        ),
        "function_evaluations": int(result.nfev),
    }


def solve_left_trajectory(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    lower: np.ndarray,
    upper: np.ndarray,
) -> list[dict]:
    set_state(
        model,
        data,
        RIGHT_WORK_BASE,
        level_3.GRASP_Q,
        GRASP_FINGER,
        0.0,
        0.0,
    )
    ref_hand_pos, ref_hand_rot = level_2.body_pose(model, data, "hand")
    ref_handle_pos = minimal.geom_pos(model, data, RIGHT_HANDLE)
    ref_offset = ref_hand_pos - ref_handle_pos
    rotation = Rotation.from_euler("z", LEFT_GRASP_THETA).as_matrix()

    set_state(
        model,
        data,
        LEFT_WORK_BASE,
        level_3.GRASP_Q,
        GRASP_FINGER,
        0.0,
        TARGET_ANGLE,
    )
    desired_pos = (
        minimal.geom_pos(model, data, LEFT_HANDLE) + rotation @ ref_offset
    )
    desired_rot = rotation @ ref_hand_rot
    seed = np.array(
        [
            -0.8426698746,
            -0.8482959948,
            -1.3223416967,
            -1.6481431448,
            -2.0774300951,
            2.8514452244,
            2.0126592125,
        ]
    )
    start_q, start_ik = solve_arm_pose(
        model,
        data,
        LEFT_WORK_BASE,
        0.0,
        TARGET_ANGLE,
        seed,
        desired_pos,
        desired_rot,
        lower,
        upper,
    )
    if (
        start_ik["hand_position_error"] > 0.002
        or start_ik["hand_rotation_error"] > 0.01
    ):
        raise RuntimeError(f"Left grasp IK failed: {start_ik}")

    set_state(
        model,
        data,
        LEFT_WORK_BASE,
        start_q,
        GRASP_FINGER,
        0.0,
        TARGET_ANGLE,
    )
    door_pos_0, door_rot_0 = level_2.body_pose(
        model,
        data,
        "cabinet_left_door",
    )
    hand_pos_0, hand_rot_0 = level_2.body_pose(model, data, "hand")
    door_to_hand_pos = door_rot_0.T @ (hand_pos_0 - door_pos_0)
    door_to_hand_rot = door_rot_0.T @ hand_rot_0

    previous = start_q
    rows: list[dict] = []
    for raw_alpha in np.linspace(0.0, 1.0, LEFT_OPEN_SAMPLE_COUNT):
        alpha = level_2.smooth(float(raw_alpha))
        hinge = TARGET_ANGLE * alpha
        base = (
            (1.0 - alpha) * LEFT_WORK_BASE
            + alpha * LEFT_OPEN_END_BASE
        )
        set_state(
            model,
            data,
            base,
            previous,
            GRASP_FINGER,
            hinge,
            TARGET_ANGLE,
        )
        door_pos, door_rot = level_2.body_pose(
            model,
            data,
            "cabinet_left_door",
        )
        target_pos = door_pos + door_rot @ door_to_hand_pos
        target_rot = door_rot @ door_to_hand_rot
        solved, ik = solve_arm_pose(
            model,
            data,
            base,
            hinge,
            TARGET_ANGLE,
            previous,
            target_pos,
            target_rot,
            lower,
            upper,
        )
        rows.append(
            {
                "left_hinge": float(hinge),
                "base": base.tolist(),
                "panda_qpos": solved.tolist(),
                **ik,
            }
        )
        previous = solved
    return rows


def interpolate_joint_path(
    path: list[np.ndarray],
    max_step: float = 0.045,
) -> list[np.ndarray]:
    dense: list[np.ndarray] = [path[0].copy()]
    for start, end in zip(path[:-1], path[1:]):
        count = max(
            2,
            int(np.ceil(np.max(np.abs(end - start)) / max_step)) + 1,
        )
        dense.extend(
            (1.0 - alpha) * start + alpha * end
            for alpha in np.linspace(0.0, 1.0, count)[1:]
        )
    return dense


def interpolate_base_path(
    waypoints: tuple[np.ndarray, ...],
    steps_per_edge: int = 31,
) -> list[np.ndarray]:
    dense: list[np.ndarray] = [waypoints[0].copy()]
    for start, end in zip(waypoints[:-1], waypoints[1:]):
        dense.extend(
            (1.0 - level_2.smooth(float(alpha))) * start
            + level_2.smooth(float(alpha)) * end
            for alpha in np.linspace(0.0, 1.0, steps_per_edge)[1:]
        )
    return dense


def append_state(
    sequence: list[dict],
    phase: str,
    base: np.ndarray,
    qpos: np.ndarray,
    finger: float,
    left_hinge: float,
    right_hinge: float,
    active_handle: str | None,
) -> None:
    sequence.append(
        {
            "phase": phase,
            "base": np.asarray(base, dtype=float),
            "qpos": np.asarray(qpos, dtype=float),
            "finger": float(finger),
            "left_hinge": float(left_hinge),
            "right_hinge": float(right_hinge),
            "active_handle": active_handle,
        }
    )


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    ensure_level_5_xml()

    right_rows = json.loads(level_3.TRAJECTORY_PATH.read_text(encoding="utf-8"))
    if not right_rows:
        raise RuntimeError("Level 3 right-door trajectory is empty")

    model = mujoco.MjModel.from_xml_path(str(TASK_XML))
    data = mujoco.MjData(model)
    lower, upper = arm_bounds(model)
    panda_ids = validation.panda_geom_ids(model)
    environment_ids = environment_target_ids(model)
    left_rows = solve_left_trajectory(model, data, lower, upper)

    right_end = np.asarray(right_rows[-1]["panda_qpos"], dtype=float)
    left_start = np.asarray(left_rows[0]["panda_qpos"], dtype=float)
    tucked = cab.PANDA_HOME.copy()

    sequence: list[dict] = []
    for _ in range(8):
        append_state(
            sequence,
            "hold_right_grasp",
            RIGHT_WORK_BASE,
            np.asarray(right_rows[0]["panda_qpos"]),
            GRASP_FINGER,
            0.0,
            0.0,
            RIGHT_HANDLE,
        )
    for row in right_rows:
        append_state(
            sequence,
            "open_right_door",
            RIGHT_WORK_BASE,
            np.asarray(row["panda_qpos"]),
            GRASP_FINGER,
            0.0,
            float(row["hinge"]),
            RIGHT_HANDLE,
        )
    for alpha in np.linspace(0.0, 1.0, 17)[1:]:
        append_state(
            sequence,
            "release_right_handle",
            RIGHT_WORK_BASE,
            right_end,
            (1.0 - alpha) * GRASP_FINGER + alpha * OPEN_FINGER,
            0.0,
            TARGET_ANGLE,
            None,
        )
    for base in interpolate_base_path(
        (RIGHT_WORK_BASE, RIGHT_RETREAT_BASE),
        steps_per_edge=41,
    )[1:]:
        append_state(
            sequence,
            "base_retreat_from_right_door",
            base,
            right_end,
            OPEN_FINGER,
            0.0,
            TARGET_ANGLE,
            None,
        )
    for qpos in interpolate_joint_path([right_end, tucked])[1:]:
        append_state(
            sequence,
            "fold_arm_at_right_clearance_station",
            RIGHT_RETREAT_BASE,
            qpos,
            OPEN_FINGER,
            0.0,
            TARGET_ANGLE,
            None,
        )
    for base in interpolate_base_path(
        (RIGHT_RETREAT_BASE, LEFT_STAGING_BASE),
        steps_per_edge=51,
    )[1:]:
        append_state(
            sequence,
            "rear_clearance_move_to_left_side",
            base,
            tucked,
            OPEN_FINGER,
            0.0,
            TARGET_ANGLE,
            None,
        )
    for qpos in interpolate_joint_path([tucked, left_start])[1:]:
        append_state(
            sequence,
            "unfold_arm_at_left_staging_station",
            LEFT_STAGING_BASE,
            qpos,
            OPEN_FINGER,
            0.0,
            TARGET_ANGLE,
            None,
        )
    for base in interpolate_base_path(
        (
            LEFT_STAGING_BASE,
            LEFT_PREAPPROACH_BASE,
            LEFT_WORK_BASE,
        ),
        steps_per_edge=41,
    )[1:]:
        append_state(
            sequence,
            "base_approach_left_handle",
            base,
            left_start,
            OPEN_FINGER,
            0.0,
            TARGET_ANGLE,
            None,
        )
    for alpha in np.linspace(0.0, 1.0, 17)[1:]:
        append_state(
            sequence,
            "grasp_left_handle",
            LEFT_WORK_BASE,
            left_start,
            (1.0 - alpha) * OPEN_FINGER + alpha * GRASP_FINGER,
            0.0,
            TARGET_ANGLE,
            LEFT_HANDLE,
        )
    for row in left_rows:
        append_state(
            sequence,
            "open_left_door",
            np.asarray(row["base"]),
            np.asarray(row["panda_qpos"]),
            GRASP_FINGER,
            float(row["left_hinge"]),
            TARGET_ANGLE,
            LEFT_HANDLE,
        )
    for _ in range(12):
        append_state(
            sequence,
            "hold_both_doors_open",
            np.asarray(left_rows[-1]["base"]),
            np.asarray(left_rows[-1]["panda_qpos"]),
            GRASP_FINGER,
            TARGET_ANGLE,
            TARGET_ANGLE,
            LEFT_HANDLE,
        )

    samples: list[dict] = []
    previous_qpos: np.ndarray | None = None
    frames: list[Image.Image] = []
    top_frames: list[Image.Image] = []
    right_frames: list[Image.Image] = []
    render_stride = max(1, len(sequence) // 180)
    for index, state in enumerate(sequence):
        sample = validate_state(
            model,
            data,
            state["phase"],
            index,
            state["base"],
            state["qpos"],
            state["finger"],
            state["left_hinge"],
            state["right_hinge"],
            panda_ids,
            environment_ids,
            state["active_handle"],
            previous_qpos,
        )
        samples.append(sample)
        if index % render_stride == 0 or index == len(sequence) - 1:
            frames.append(Image.fromarray(minimal.render(model, data, "diag")))
            top_frames.append(Image.fromarray(minimal.render(model, data, "top")))
            right_frames.append(
                Image.fromarray(render_right_side(model, data))
            )
        previous_qpos = state["qpos"]

    overlap_failures = [
        sample
        for sample in samples
        if sample["environment_visual_overlap_count"] > 0
    ]
    forbidden_contact_failures = [
        sample
        for sample in samples
        if sample["forbidden_active_handle_contact_count"] > 0
    ]
    right_open_samples = [
        sample for sample in samples if sample["phase"] == "open_right_door"
    ]
    left_open_samples = [
        sample for sample in samples if sample["phase"] == "open_left_door"
    ]
    right_max_distance = max(
        sample["gripper_to_active_handle_distance"]
        for sample in right_open_samples
    )
    left_max_distance = max(
        sample["gripper_to_active_handle_distance"]
        for sample in left_open_samples
    )
    right_min_contacts = min(
        sample["active_handle_unique_finger_contact_count"]
        for sample in right_open_samples
    )
    left_min_contacts = min(
        sample["active_handle_unique_finger_contact_count"]
        for sample in left_open_samples
    )
    max_base_command_error = max(
        sample["base_command_error"] for sample in samples
    )
    max_joint_step = max(
        sample["max_joint_step_from_previous"] for sample in samples
    )
    right_open_base_drift = max(
        float(
            np.linalg.norm(
                np.asarray(sample["base"]) - RIGHT_WORK_BASE
            )
        )
        for sample in right_open_samples
    )
    left_open_base_drift = max(
        float(
            np.linalg.norm(
                np.asarray(sample["base"]) - LEFT_WORK_BASE
            )
        )
        for sample in left_open_samples
    )
    allowed_base_motion_phases = {
        "base_retreat_from_right_door",
        "rear_clearance_move_to_left_side",
        "base_approach_left_handle",
        "open_left_door",
    }
    base_motion_outside_planned_phase_count = 0
    right_hinge_motion_outside_open_count = 0
    left_hinge_motion_outside_open_count = 0
    for previous, current in zip(samples[:-1], samples[1:]):
        if (
            np.linalg.norm(
                np.asarray(current["base"]) - np.asarray(previous["base"])
            )
            > 1e-9
            and current["phase"] not in allowed_base_motion_phases
        ):
            base_motion_outside_planned_phase_count += 1
        if (
            abs(current["right_hinge"] - previous["right_hinge"]) > 1e-9
            and current["phase"] != "open_right_door"
        ):
            right_hinge_motion_outside_open_count += 1
        if (
            abs(current["left_hinge"] - previous["left_hinge"]) > 1e-9
            and current["phase"] != "open_left_door"
        ):
            left_hinge_motion_outside_open_count += 1
    right_open_monotonic = all(
        current["right_hinge"] >= previous["right_hinge"] - 1e-9
        for previous, current in zip(
            right_open_samples[:-1],
            right_open_samples[1:],
        )
    )
    left_open_monotonic = all(
        current["left_hinge"] >= previous["left_hinge"] - 1e-9
        for previous, current in zip(
            left_open_samples[:-1],
            left_open_samples[1:],
        )
    )
    final = samples[-1]
    passed = bool(
        final["right_hinge"] >= TARGET_ANGLE - 0.01
        and final["left_hinge"] >= TARGET_ANGLE - 0.01
        and right_max_distance <= 0.06
        and left_max_distance <= 0.06
        and right_min_contacts >= 2
        and left_min_contacts >= 2
        and max_base_command_error <= 1e-9
        and right_open_base_drift <= 1e-9
        and base_motion_outside_planned_phase_count == 0
        and right_hinge_motion_outside_open_count == 0
        and left_hinge_motion_outside_open_count == 0
        and right_open_monotonic
        and left_open_monotonic
        and max_joint_step <= 0.20
        and not overlap_failures
        and not forbidden_contact_failures
    )

    frames[0].save(
        GIF_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
    )
    top_frames[0].save(
        TOP_GIF_PATH,
        save_all=True,
        append_images=top_frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
    )
    right_frames[0].save(
        RIGHT_GIF_PATH,
        save_all=True,
        append_images=right_frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
    )
    level_2.save_frame_sheet(frames, FRAME_SHEET_PATH)
    level_2.save_frame_sheet(top_frames, TOP_FRAME_SHEET_PATH)
    level_2.save_frame_sheet(right_frames, RIGHT_FRAME_SHEET_PATH)
    TRAJECTORY_PATH.write_text(
        json.dumps(samples, indent=2) + "\n",
        encoding="utf-8",
    )

    summary = {
        "task_name": "level_5_sequential_open_both_doors",
        "scope": "open the right cabinet door, reposition safely, then open the left cabinet door",
        "passed_full_validation": passed,
        "right_opening_base_locked": right_open_base_drift <= 1e-9,
        "left_opening_base_locked": left_open_base_drift <= 1e-9,
        "left_opening_uses_controlled_base_motion": True,
        "base_moved_only_in_planned_phases": (
            base_motion_outside_planned_phase_count == 0
        ),
        "right_opening_maximum_base_drift": right_open_base_drift,
        "left_opening_maximum_base_drift": left_open_base_drift,
        "left_opening_start_base": LEFT_WORK_BASE.tolist(),
        "left_opening_end_base": LEFT_OPEN_END_BASE.tolist(),
        "left_opening_base_displacement": float(
            np.linalg.norm(LEFT_OPEN_END_BASE - LEFT_WORK_BASE)
        ),
        "base_motion_outside_planned_phase_count": (
            base_motion_outside_planned_phase_count
        ),
        "right_hinge_motion_outside_open_phase_count": (
            right_hinge_motion_outside_open_count
        ),
        "left_hinge_motion_outside_open_phase_count": (
            left_hinge_motion_outside_open_count
        ),
        "right_opening_monotonic": right_open_monotonic,
        "left_opening_monotonic": left_open_monotonic,
        "right_work_base": RIGHT_WORK_BASE.tolist(),
        "left_work_base": LEFT_WORK_BASE.tolist(),
        "target_angle_each_door": TARGET_ANGLE,
        "final_right_hinge_angle": final["right_hinge"],
        "final_left_hinge_angle": final["left_hinge"],
        "right_open_sample_count": len(right_open_samples),
        "left_open_sample_count": len(left_open_samples),
        "total_validated_sample_count": len(samples),
        "right_max_gripper_to_handle_distance": right_max_distance,
        "left_max_gripper_to_handle_distance": left_max_distance,
        "right_min_unique_finger_contacts": right_min_contacts,
        "left_min_unique_finger_contacts": left_min_contacts,
        "max_base_command_error": max_base_command_error,
        "max_joint_step": max_joint_step,
        "environment_geom_count_checked": len(environment_ids),
        "environment_visual_overlap_failure_count": len(
            overlap_failures
        ),
        "forbidden_active_handle_contact_failure_count": len(
            forbidden_contact_failures
        ),
        "right_retreat_base": RIGHT_RETREAT_BASE.tolist(),
        "left_staging_base": LEFT_STAGING_BASE.tolist(),
        "left_preapproach_base": LEFT_PREAPPROACH_BASE.tolist(),
        "motion_gif": str(GIF_PATH),
        "top_view_gif": str(TOP_GIF_PATH),
        "right_side_view_gif": str(RIGHT_GIF_PATH),
        "trajectory": str(TRAJECTORY_PATH),
        "frame_sheet": str(FRAME_SHEET_PATH),
        "top_frame_sheet": str(TOP_FRAME_SHEET_PATH),
        "right_side_frame_sheet": str(RIGHT_FRAME_SHEET_PATH),
        "task_xml": str(TASK_XML),
        "note": (
            "The base is locked while opening the right door. After releasing "
            "the right handle, the robot tucks the arm and follows a checked "
            "clearance route. The left door then uses coordinated base and arm "
            "motion to keep clear of the adjacent cabinet."
        ),
    }
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))
    if not passed:
        print("First overlap failures:", overlap_failures[:3])
        print("First contact failures:", forbidden_contact_failures[:3])
        raise SystemExit(1)


if __name__ == "__main__":
    main()
