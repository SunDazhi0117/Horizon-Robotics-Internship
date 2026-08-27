# Week6: Panda Cabinet Open-Close Task

This directory contains the retained Week6 cabinet-manipulation result and the
runtime assets required by Week7.

## Final Task

The mobile Panda:

1. approaches the cabinet handle;
2. closes both fingers around the handle;
3. opens the right cabinet door to `90 deg`;
4. follows the handle back to the closed pose;
5. releases the handle.

Result: `PASS`

Viewer:

`http://127.0.0.1:8899/week6_note/`

## Final Artifacts

- Video: `assets/videos/panda_open_close_cabinet.gif`
- Summary: `assets/results/panda_open_close_cabinet_summary.json`
- Open image: `assets/images/panda_open_close_cabinet_open_diag.png`
- Closed image: `assets/images/panda_open_close_cabinet_closed_final_diag.png`
- Closed top view: `assets/images/panda_open_close_cabinet_closed_final_top.png`
- Validation sheet: `assets/images/panda_open_close_cabinet_frames_sheet.png`
- Acceptance report: `docs/ACCEPTANCE_REPORT.md`

## Required Runtime Files

The following scripts are retained because the final Week6 task and Week7
Level 1-3 import them:

- `scripts/run_panda_reach_cabinet_handle.py`
- `scripts/run_panda_handle_pull_minimal.py`
- `scripts/run_panda_handle_pull_90_attempt.py`
- `scripts/run_panda_open_close_cabinet.py`

Required model data:

- `assets/franka_panda/`
- `assets/meshes/`
- `xml/articulated_demo_with_actuators.xml`
- `xml/franka_panda_shifted_for_cabinet.xml`
- `xml/articulated_demo_room_with_panda_reach.xml`
- `xml/articulated_demo_room_with_panda_minimal_handle_pull.xml`

## Reproduce

```bash
cd /home/users/dazhi.sun-labs/projects
MUJOCO_GL=egl \
  scenesmith/.mujoco_venv/bin/python \
  week6_note/scripts/run_panda_open_close_cabinet.py
```

## Validation

- Target hinge angle: `1.5708 rad`
- Maximum hinge angle: `1.5708 rad`
- Final hinge angle: `0.0 rad`
- Open-pose finger contacts: `2`
- Closed-pose finger contacts: `2`
- Forbidden door-slab contacts: `0`

This is a scripted MuJoCo waypoint demonstration, not a learned policy or
force-controlled manipulation benchmark.
