# Task 3: Navigate And Reach Cabinet Handle

## Goal

Combine the previous two validations into one MuJoCo run:

1. Stretch navigates from a start pose to the cabinet-front region.
2. Stretch aligns its base toward the cabinet handle.
3. Stretch raises the lift and extends the arm.
4. The gripper reaches near the right cabinet handle.

This is the first combined navigation + pre-manipulation task in the generated SceneSmith + Articraft room.

## Files

- Script: `scripts/run_stretch_navigate_and_reach_cabinet_handle.py`
- Task XML: `xml/articulated_demo_stretch_navigate_and_reach_cabinet.xml`
- Summary: `outputs/combined_nav_reach_summary.json`
- Motion GIF: `outputs/combined_nav_reach_motion.gif`
- Start image: `outputs/combined_nav_reach_start_top.png`
- After-navigation image: `outputs/combined_nav_reach_after_navigation_top.png`
- Final images:
  - `outputs/combined_nav_reach_final_top.png`
  - `outputs/combined_nav_reach_final_diag.png`

## Navigation Result

- Start XY: `[3.10, 2.35]`
- Waypoints:
  - `[3.55, 2.35]`
  - `[3.55, 2.95]`
  - `[4.22, 2.86]`
- Reached waypoints: `3 / 3`
- Final navigation XY: `[4.1863, 2.8897]`
- Distance to reach base target: `0.0449 m`
- Navigation success radius: `0.045 m`
- Navigation result: `PASS`

## Alignment Result

- Target reach yaw: `1.5708 rad`
- Final yaw error: `0.0550 rad`
- Alignment result: `PASS`

## Reach Result

- Target handle: `010_double_door_cabinet_right_door_right_handle`
- Handle position: `[4.8820, 2.8720, 0.7000]`
- Gripper position: `[4.9265, 2.9200, 0.6939]`
- Gripper-to-handle distance: `0.0657 m`
- Reach success threshold: `0.08 m`
- Lift qpos: `0.0947`
- Arm extension total: `0.5200`
- Reach result: `PASS`

## Important Detail

This task no longer snaps the base pose before the reach stage. The base approaches and aligns through MuJoCo controls.

This is still not a full autonomous manipulation task. It does not yet grasp the handle or physically open the cabinet door.

## What This Proves

This verifies that:

- the generated articulated room can run in MuJoCo,
- the real Stretch model can move inside the room,
- waypoint navigation can bring the robot close to the cabinet,
- base alignment can orient the robot for reaching,
- lift and arm actuators can move the gripper near a generated cabinet handle,
- task success can be measured numerically from MuJoCo state.

## Next Step

The next task should add a simplified interaction:

1. navigate and reach the handle,
2. close or position the gripper near the handle,
3. drive the cabinet hinge open,
4. validate the cabinet door joint angle.

That would become the first simplified "open cabinet" task.
