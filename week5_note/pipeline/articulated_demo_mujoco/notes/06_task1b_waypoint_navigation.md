# Task 1b: Waypoint Navigation To Cabinet

## Goal

Move the real Hello Robot Stretch model inside the generated SceneSmith + Articraft room toward the double-door cabinet operation region.

This task improves on the first cabinet navigation smoke test. Instead of driving in one straight line, the robot follows three intermediate targets:

1. Move out from the start pose.
2. Turn toward the cabinet-side aisle.
3. Stop in front of the cabinet target region.

## Files

- Script: `scripts/run_stretch_waypoint_to_cabinet.py`
- Task XML: `xml/articulated_demo_stretch_waypoint_cabinet.xml`
- Summary: `outputs/waypoint_cabinet_summary.json`
- Motion GIF: `outputs/waypoint_cabinet_motion.gif`
- Start image: `outputs/waypoint_cabinet_start_top.png`
- Final images:
  - `outputs/waypoint_cabinet_final_top.png`
  - `outputs/waypoint_cabinet_final_diag.png`

## Result

- Start XY: `[3.10, 2.35]`
- Waypoints:
  - `[3.55, 2.35]`
  - `[3.55, 2.95]`
  - `[4.45, 2.95]`
- Reached waypoints: `3 / 3`
- Final XY: `[4.1001, 2.9527]`
- Final distance to target: `0.3499 m`
- Success radius: `0.35 m`
- Elapsed simulated time: `13.62 s`
- Final contact count: `5`
- Result: `PASS`

## What This Proves

This verifies that:

- The generated room can be loaded in MuJoCo.
- The reconstructed cabinet, door, and microwave geometry can coexist with a real robot model.
- Stretch can be placed inside the generated room.
- Stretch can be controlled with MuJoCo actuators.
- A simple controller can move the robot toward a task-relevant object region.

## What This Does Not Prove Yet

This is not a full manipulation task yet.

It does not prove:

- robust collision-free path planning,
- contact-aware navigation,
- reaching or grasping,
- opening the cabinet,
- opening the microwave,
- mobile manipulation policy learning.

## Next Step

The next useful step is to turn this into a two-stage task:

1. Navigate to the cabinet-front region.
2. Use the arm/lift/gripper to reach the cabinet handle area.

After that, the task can be extended into opening the cabinet door.
