"""Audit visible attachment and support relationships in every Week11 scene."""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

import mujoco
import numpy as np

from week7_note.scripts.level_validation_helpers import geom_obb
from week7_note.task_system.executor import load_task_config


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("week11_note/configs/structural_support_audit.yaml"),
    )
    return parser.parse_args()


def _sequence(value: object, *, field: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field} must be a sequence")
    return value


def _geom_id(model: mujoco.MjModel, name: str) -> int:
    geom_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, name)
    if geom_id < 0:
        raise ValueError(f"MuJoCo geom {name!r} does not exist")
    return geom_id


def _world_bounds(model: mujoco.MjModel, data: mujoco.MjData, geom_id: int):
    center, rotation, half_extent = geom_obb(model, data, geom_id)
    world_half_extent = np.abs(rotation) @ half_extent
    return center - world_half_extent, center + world_half_extent


def _aabb_gap(bounds_a, bounds_b) -> float:
    minimum_a, maximum_a = bounds_a
    minimum_b, maximum_b = bounds_b
    separation = np.maximum(
        0.0,
        np.maximum(minimum_b - maximum_a, minimum_a - maximum_b),
    )
    return float(np.linalg.norm(separation))


def _set_object_joints(
    model: mujoco.MjModel,
    data: mujoco.MjData,
    aliases: Mapping[str, object],
    state: Mapping[str, object],
) -> None:
    joints = state.get("object_joints")
    if not isinstance(joints, Mapping):
        raise ValueError("trajectory state object_joints must be a mapping")
    for state_name, raw_value in joints.items():
        model_name = str(aliases.get(state_name, state_name))
        joint_id = mujoco.mj_name2id(
            model,
            mujoco.mjtObj.mjOBJ_JOINT,
            model_name,
        )
        if joint_id < 0:
            raise ValueError(f"MuJoCo joint {model_name!r} does not exist")
        address = int(model.jnt_qposadr[joint_id])
        data.qpos[address] = float(raw_value)
    mujoco.mj_forward(model, data)


def _selected_states(states: Sequence[object], selector: str):
    if selector == "initial":
        return [(0, states[0])]
    if selector == "final":
        return [(len(states) - 1, states[-1])]
    if selector == "all":
        return list(enumerate(states))
    raise ValueError(f"unsupported state selector {selector!r}")


def main() -> None:
    arguments = _arguments()
    manifest_path = arguments.manifest.expanduser().resolve()
    manifest = load_task_config(manifest_path)
    project_root = manifest_path.parent.parent
    scenes = _sequence(manifest.get("scenes"), field="scenes")
    tolerance = float(manifest.get("default_max_gap", 1e-6))

    scene_reports = []
    total_checks = 0
    total_failures = 0
    for raw_scene in scenes:
        if not isinstance(raw_scene, Mapping):
            raise ValueError("each scene must be a mapping")
        name = str(raw_scene.get("name", "")).strip()
        config_path = project_root / str(raw_scene.get("task_config"))
        trajectory_path = project_root / str(raw_scene.get("trajectory"))
        config = load_task_config(config_path)
        runtime = config.get("runtime")
        if not isinstance(runtime, Mapping):
            raise ValueError(f"{name}: runtime must be a mapping")
        task_xml = project_root / str(runtime.get("task_xml"))
        aliases = runtime.get("object_joint_aliases")
        if not isinstance(aliases, Mapping):
            raise ValueError(f"{name}: object_joint_aliases must be a mapping")
        states = json.loads(trajectory_path.read_text(encoding="utf-8"))
        model = mujoco.MjModel.from_xml_path(str(task_xml))
        data = mujoco.MjData(model)

        checks = []
        for raw_geom in _sequence(
            raw_scene.get("grounded_geoms", ()),
            field=f"{name}.grounded_geoms",
        ):
            geom_name = str(raw_geom)
            _set_object_joints(model, data, aliases, states[0])
            minimum, _ = _world_bounds(model, data, _geom_id(model, geom_name))
            gap = abs(float(minimum[2]))
            passed = gap <= tolerance
            checks.append(
                {
                    "type": "ground",
                    "label": f"{geom_name} touches the ground",
                    "state": "initial",
                    "maximum_gap": gap,
                    "tolerance": tolerance,
                    "passed": passed,
                }
            )

        for raw_check in _sequence(
            raw_scene.get("contact_checks"),
            field=f"{name}.contact_checks",
        ):
            if not isinstance(raw_check, Mapping):
                raise ValueError(f"{name}: each contact check must be a mapping")
            geom_a = str(raw_check.get("a", "")).strip()
            geom_b = str(raw_check.get("b", "")).strip()
            selector = str(raw_check.get("at", "initial"))
            max_gap = float(raw_check.get("max_gap", tolerance))
            gaps = []
            for _, raw_state in _selected_states(states, selector):
                if not isinstance(raw_state, Mapping):
                    raise ValueError(f"{name}: trajectory state must be a mapping")
                _set_object_joints(model, data, aliases, raw_state)
                gaps.append(
                    _aabb_gap(
                        _world_bounds(model, data, _geom_id(model, geom_a)),
                        _world_bounds(model, data, _geom_id(model, geom_b)),
                    )
                )
            measured = max(gaps)
            passed = measured <= max_gap
            checks.append(
                {
                    "type": "contact",
                    "label": str(raw_check.get("label", f"{geom_a} to {geom_b}")),
                    "state": selector,
                    "geom_a": geom_a,
                    "geom_b": geom_b,
                    "maximum_gap": measured,
                    "tolerance": max_gap,
                    "passed": passed,
                }
            )

        failures = [item for item in checks if not item["passed"]]
        total_checks += len(checks)
        total_failures += len(failures)
        scene_reports.append(
            {
                "scene": name,
                "passed": not failures,
                "check_count": len(checks),
                "failure_count": len(failures),
                "failures": failures,
                "checks": checks,
            }
        )

    summary = {
        "passed": total_failures == 0,
        "scene_count": len(scene_reports),
        "check_count": total_checks,
        "failure_count": total_failures,
        "scenes": scene_reports,
    }
    output_path = project_root / "results" / "structural_support_audit.json"
    output_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if total_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
