# Task 2: Reach Cabinet Handle

## Goal

Validate that the real Hello Robot Stretch model can move its upper body toward a task-relevant articulated object handle inside the generated SceneSmith + Articraft room.

This is a pre-manipulation task. It checks whether the robot can place its gripper near the cabinet handle. It does not yet grasp the handle or open the cabinet door.

## Files

- Script: `scripts/run_stretch_reach_cabinet_handle.py`
- Task XML: `xml/articulated_demo_stretch_reach_cabinet_handle.xml`
- Summary: `outputs/reach_cabinet_handle_summary.json`
- Motion GIF: `outputs/reach_cabinet_handle_motion.gif`
- Start images:
  - `outputs/reach_cabinet_handle_start_top.png`
  - `outputs/reach_cabinet_handle_start_diag.png`
- Final images:
  - `outputs/reach_cabinet_handle_final_top.png`
  - `outputs/reach_cabinet_handle_final_diag.png`

## Setup

- Robot base pose: `[4.15, 2.92]`
- Robot yaw: `1.5708 rad`
- Target handle: `010_double_door_cabinet_right_door_right_handle`
- Target lift command: `0.095`
- Target arm extension command: `0.52`
- Target gripper command: `0.035`

## Result

- Handle position: `[4.8820, 2.8720, 0.7000]`
- Gripper position: `[4.8914, 2.8912, 0.6939]`
- Gripper-to-handle distance: `0.0222 m`
- Success threshold: `0.08 m`
- Lift qpos: `0.0947`
- Arm extension total: `0.5200`
- Final contact count: `5`
- Result: `PASS`

## What This Proves

This verifies that:

- the generated cabinet handle has a measurable MuJoCo world position,
- the Stretch robot can be positioned in front of the cabinet,
- Stretch's lift and arm extension actuators work inside the generated room,
- the gripper can reach the cabinet handle region within a small distance threshold.

## What This Does Not Prove Yet

This does not prove:

- autonomous navigation from the room entrance to the cabinet,
- inverse kinematics planning,
- physical grasping,
- contact-rich manipulation,
- opening the cabinet door with the robot,
- robust collision-free task execution.

## Next Step

The next useful task is to add a simple interaction stage:

1. reach the cabinet handle,
2. close the gripper or hold near the handle,
3. drive the cabinet hinge actuator open,
4. validate that the cabinet door angle reaches a target value.

That would still be a simplified task, but it would connect reaching to an articulated-object state change.
