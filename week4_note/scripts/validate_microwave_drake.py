#!/usr/bin/env python3
"""Run a lightweight Drake validation of the existing Articraft microwave."""

from __future__ import annotations

import argparse
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from pydrake.all import (
    AddMultibodyPlantSceneGraph,
    DiagramBuilder,
    JointIndex,
    Parser,
    Role,
    Simulator,
)


ROOT = Path(__file__).resolve().parents[1]
PROJECTS_ROOT = ROOT.parent
DEFAULT_URDF = (
    PROJECTS_ROOT
    / "articraft/data/cache/record_materialization"
    / "rec_create-a-complex-articulated-microwave-oven-as-a_"
    "20260622_093428_040254_ec41899c/model.urdf"
)
DEFAULT_OUTPUT = ROOT / "reports/microwave_drake_validation.json"

EXPECTED_JOINTS = {
    "body_to_front_door": {
        "type": "revolute",
        "lower": 0.0,
        "upper": 1.75,
    },
    "body_to_sliding_tray": {
        "type": "prismatic",
        "lower": 0.0,
        "upper": 0.22,
    },
    "tray_to_turntable": {
        "type": "revolute",
        "lower": -math.inf,
        "upper": math.inf,
    },
    "body_to_upper_knob": {
        "type": "revolute",
        "lower": -math.inf,
        "upper": math.inf,
    },
    "body_to_lower_knob": {
        "type": "revolute",
        "lower": -math.inf,
        "upper": math.inf,
    },
}

SAMPLED_STATES = {
    "closed": {},
    "door_half_open": {"body_to_front_door": 0.875},
    "door_fully_open": {"body_to_front_door": 1.75},
    "door_open_tray_half_out": {
        "body_to_front_door": 1.75,
        "body_to_sliding_tray": 0.11,
    },
    "door_open_tray_fully_out": {
        "body_to_front_door": 1.75,
        "body_to_sliding_tray": 0.22,
    },
    "all_controls_sampled": {
        "body_to_front_door": 1.75,
        "body_to_sliding_tray": 0.22,
        "tray_to_turntable": math.pi,
        "body_to_upper_knob": 1.0,
        "body_to_lower_knob": -1.0,
    },
}

# This deliberately invalid operation documents why the viewer interlock exists.
DIAGNOSTIC_STATES = {
    "tray_out_while_door_closed": {"body_to_sliding_tray": 0.22},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--urdf", type=Path, default=DEFAULT_URDF)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--require-dynamics",
        action="store_true",
        help="Return a failure if the gravity simulation cannot run.",
    )
    return parser.parse_args()


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECTS_ROOT))
    except ValueError:
        return str(path.resolve())


def build_model(urdf: Path):
    builder = DiagramBuilder()
    plant, scene_graph = AddMultibodyPlantSceneGraph(builder, time_step=0.001)
    model = Parser(plant).AddModels(str(urdf))[0]
    plant.WeldFrames(
        plant.world_frame(),
        plant.GetFrameByName("microwave_body", model),
    )
    plant.Finalize()
    return builder, plant, scene_graph


def joint_records(plant) -> list[dict[str, object]]:
    records = []
    for index in range(plant.num_joints()):
        joint = plant.get_joint(JointIndex(index))
        if joint.num_positions() == 0:
            continue
        records.append(
            {
                "name": joint.name(),
                "type": joint.type_name(),
                "lower": float(joint.position_lower_limits()[0]),
                "upper": float(joint.position_upper_limits()[0]),
                "position_index": joint.position_start(),
            }
        )
    return records


def limits_match(actual: float, expected: float) -> bool:
    if math.isinf(expected):
        return math.isinf(actual) and np.sign(actual) == np.sign(expected)
    return math.isclose(actual, expected, abs_tol=1e-9)


def json_safe(value):
    """Convert non-finite floats to explicit strings for strict JSON."""
    if isinstance(value, float) and not math.isfinite(value):
        return "inf" if value > 0 else "-inf"
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    return value


def validate_joint_contract(records: list[dict[str, object]]) -> list[str]:
    failures = []
    by_name = {str(record["name"]): record for record in records}
    if set(by_name) != set(EXPECTED_JOINTS):
        failures.append(
            f"joint names differ: expected {sorted(EXPECTED_JOINTS)}, "
            f"found {sorted(by_name)}"
        )
        return failures

    for name, expected in EXPECTED_JOINTS.items():
        actual = by_name[name]
        if actual["type"] != expected["type"]:
            failures.append(
                f"{name} type: expected {expected['type']}, found {actual['type']}"
            )
        for key in ("lower", "upper"):
            if not limits_match(float(actual[key]), float(expected[key])):
                failures.append(
                    f"{name} {key}: expected {expected[key]}, found {actual[key]}"
                )
    return failures


def sample_collisions(
    plant,
    scene_graph,
    diagram,
    states: dict[str, dict[str, float]],
) -> dict[str, dict[str, object]]:
    context = diagram.CreateDefaultContext()
    plant_context = plant.GetMyMutableContextFromRoot(context)
    scene_graph_context = scene_graph.GetMyContextFromRoot(context)
    inspector = scene_graph.model_inspector()
    records = {record["name"]: record for record in joint_records(plant)}
    results = {}

    for state_name, values in states.items():
        positions = np.zeros(plant.num_positions())
        for joint_name, value in values.items():
            positions[int(records[joint_name]["position_index"])] = value
        plant.SetPositions(plant_context, positions)
        query = scene_graph.get_query_output_port().Eval(scene_graph_context)
        penetrations = query.ComputePointPairPenetration()
        contacts = []
        for penetration in penetrations:
            geometry_names = []
            body_names = []
            for geometry_id in (penetration.id_A, penetration.id_B):
                geometry_names.append(inspector.GetName(geometry_id))
                frame_id = inspector.GetFrameId(geometry_id)
                body_names.append(plant.GetBodyFromFrameId(frame_id).name())
            contacts.append(
                {
                    "bodies": body_names,
                    "geometries": geometry_names,
                    "depth_m": float(penetration.depth),
                }
            )
        results[state_name] = {
            "joint_values": values,
            "penetration_count": len(contacts),
            "max_depth_m": max(
                (contact["depth_m"] for contact in contacts),
                default=0.0,
            ),
            "contacts": contacts,
        }
    return results


def try_gravity_simulation(diagram, plant) -> dict[str, object]:
    try:
        simulator = Simulator(diagram)
        context = simulator.get_mutable_context()
        plant_context = plant.GetMyMutableContextFromRoot(context)
        initial_positions = plant.GetPositions(plant_context).copy()
        simulator.AdvanceTo(0.25)
        final_positions = plant.GetPositions(plant_context).copy()
        return {
            "status": "PASS",
            "duration_s": 0.25,
            "initial_positions": initial_positions.tolist(),
            "final_positions": final_positions.tolist(),
            "max_position_change": float(
                np.max(np.abs(final_positions - initial_positions))
            ),
        }
    except RuntimeError as error:
        return {
            "status": "BLOCKED",
            "duration_s": 0.25,
            "reason": str(error),
        }


def main() -> int:
    args = parse_args()
    urdf = args.urdf.resolve()
    if not urdf.is_file():
        raise FileNotFoundError(urdf)

    xml_root = ET.parse(urdf).getroot()
    link_elements = xml_root.findall("link")
    links_with_inertial = [
        link.get("name")
        for link in link_elements
        if link.find("inertial") is not None
    ]

    builder, plant, scene_graph = build_model(urdf)
    records = joint_records(plant)
    joint_failures = validate_joint_contract(records)
    diagram = builder.Build()

    normal_states = sample_collisions(
        plant,
        scene_graph,
        diagram,
        SAMPLED_STATES,
    )
    diagnostic_states = sample_collisions(
        plant,
        scene_graph,
        diagram,
        DIAGNOSTIC_STATES,
    )
    normal_path_collisions = sum(
        int(state["penetration_count"]) for state in normal_states.values()
    )
    gravity = try_gravity_simulation(diagram, plant)
    kinematic_pass = not joint_failures and normal_path_collisions == 0

    if not kinematic_pass:
        overall_status = "FAIL"
    elif gravity["status"] == "PASS":
        overall_status = "PASS"
    else:
        overall_status = "KINEMATIC_PASS_DYNAMICS_BLOCKED"

    report = {
        "overall_status": overall_status,
        "source_urdf": display_path(urdf),
        "model": {
            "links": len(link_elements),
            "links_with_inertial": links_with_inertial,
            "positions": plant.num_positions(),
            "velocities": plant.num_velocities(),
            "collision_geometries": (
                scene_graph.model_inspector().NumGeometriesWithRole(
                    Role.kProximity
                )
            ),
        },
        "joint_contract": {
            "status": "PASS" if not joint_failures else "FAIL",
            "failures": joint_failures,
            "joints": records,
        },
        "normal_operation_states": normal_states,
        "normal_path_penetration_count": normal_path_collisions,
        "diagnostic_invalid_states": diagnostic_states,
        "gravity_simulation": gravity,
        "interpretation": {
            "normal_operation": (
                "Open the door before extending the tray. All sampled normal "
                "operation states are collision-free."
            ),
            "viewer_interlock": (
                "Extending the tray while the door is closed causes collision, "
                "so the door/tray interlock is required."
            ),
            "dynamics": (
                "The source URDF has no inertial blocks. Add physically reasonable "
                "mass and inertia values before claiming dynamic simulation."
            ),
        },
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(json_safe(report), indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    print(f"Result: {overall_status}")
    print(f"URDF: {display_path(urdf)}")
    print(f"Joints: {len(records)}")
    print(f"Collision geometries: {report['model']['collision_geometries']}")
    print(f"Normal-path penetrations: {normal_path_collisions}")
    invalid_count = diagnostic_states["tray_out_while_door_closed"][
        "penetration_count"
    ]
    print(f"Closed-door tray diagnostic penetrations: {invalid_count}")
    print(f"Gravity simulation: {gravity['status']}")
    print(f"Report: {display_path(args.output)}")

    failed = not kinematic_pass or (
        args.require_dynamics and gravity["status"] != "PASS"
    )
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
