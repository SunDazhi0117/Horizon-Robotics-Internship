#!/usr/bin/env python
"""Run a minimal MuJoCo hinge-door demo and save a GIF plus summary."""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "egl")

import mujoco
from PIL import Image


ROOT = Path(__file__).resolve().parent
MODEL_XML = ROOT / "hinge_door.xml"
OUTPUT_GIF = ROOT / "hinge_door_opening.gif"
SUMMARY_JSON = ROOT / "hinge_door_result.json"


def main() -> None:
    model = mujoco.MjModel.from_xml_path(str(MODEL_XML))
    data = mujoco.MjData(model)

    duration = 3.0
    framerate = 30
    target_angle = 1.35
    success_threshold = 1.2

    frames: list[Image.Image] = []
    door_angles: list[float] = []
    timevals: list[float] = []

    mujoco.mj_resetData(model, data)
    data.ctrl[0] = target_angle

    with mujoco.Renderer(model, height=600, width=800) as renderer:
        while data.time < duration:
            data.ctrl[0] = target_angle
            mujoco.mj_step(model, data)

            door_angle = float(data.joint("door_hinge").qpos[0])
            door_angles.append(door_angle)
            timevals.append(float(data.time))

            if len(frames) < data.time * framerate:
                renderer.update_scene(data, camera="overview")
                frames.append(Image.fromarray(renderer.render()))

    final_angle = door_angles[-1]
    success = final_angle > success_threshold

    frames[0].save(
        OUTPUT_GIF,
        save_all=True,
        append_images=frames[1:],
        duration=int(1000 / framerate),
        loop=0,
    )

    summary = {
        "model_xml": str(MODEL_XML),
        "output_gif": str(OUTPUT_GIF),
        "duration_sec": duration,
        "target_angle_rad": target_angle,
        "success_threshold_rad": success_threshold,
        "final_door_angle_rad": final_angle,
        "max_door_angle_rad": max(door_angles),
        "num_frames": len(frames),
        "num_steps": len(timevals),
        "success": success,
        "model_stats": {
            "nbody": model.nbody,
            "njnt": model.njnt,
            "ngeom": model.ngeom,
            "nu": model.nu,
        },
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n")

    print("=== MuJoCo Hinge Door Demo ===")
    print(f"model:        {MODEL_XML}")
    print(f"gif:          {OUTPUT_GIF}")
    print(f"summary:      {SUMMARY_JSON}")
    print(f"bodies:       {model.nbody}")
    print(f"joints:       {model.njnt}")
    print(f"geoms:        {model.ngeom}")
    print(f"actuators:    {model.nu}")
    print(f"final angle:  {final_angle:.3f} rad")
    print(f"threshold:    {success_threshold:.3f} rad")
    print(f"result:       {'PASS' if success else 'FAIL'}")


if __name__ == "__main__":
    main()
