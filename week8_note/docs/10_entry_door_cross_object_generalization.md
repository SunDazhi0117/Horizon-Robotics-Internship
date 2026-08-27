# Entry-Door Cross-Object Generalization

## Goal

This experiment checks whether the Week7 and Week8 action framework can move
from a microwave door to the room's entry door without writing another
monolithic task script.

The task is:

    navigate to the entry door
    -> approach its handle
    -> grasp the handle
    -> open the door to 1.0 rad
    -> hold the open pose
    -> close the door
    -> release and retreat

The stable Week7 scene and accepted microwave results were not overwritten.
The experiment uses a derived Week8 XML and separate outputs.

## What Was Reused

The YAML calls the same action names used by the previous articulated-object
tasks:

- `hold_pose`;
- `move_near_target`;
- `approach_target`;
- `grasp_target`;
- `follow_hinge_joint`;
- `change_gripper`;
- `retreat_from_target`;
- `move_arm`.

`TaskExecutor`, `TaskState`, the MuJoCo state adapter, IK solver, trajectory
interpolation, target-relative navigation, and per-state validator are also
reused. The generic entry point is
`scripts/run_articulated_hinge_task.py`; it reads target and joint information
from YAML rather than containing entry-door-specific motion code.

## Object-Specific Adapter Data

The entry door still needs a small amount of object-specific description:

- handle target: `week8_entry_door_handle_proxy`;
- moving body: `entry_door`;
- hinge joint: `frame_to_door`;
- task-state alias: `entry_hinge`;
- hinge axis: `[0, 0, 1]`;
- hinge range: `[0, 1.5708]` rad;
- a door-panel collision proxy and a graspable handle proxy.

The proxies are added only to the derived
`xml/microwave_generalization.xml`. They make contact and penetration checks
possible without modifying the stable source scene.

Articulation discovery starts from the handle geom, walks to its body, and
finds the body's hinge. The new regression test verifies that this process
resolves `frame_to_door` automatically.

## Door-Follow Motion

The robot first uses automatic target-relative candidate search. It selects
`auto_01` and reaches the work pose through 120 collision-checked states.

During opening, the long door creates a larger handle arc than the microwave
door. The robot base therefore follows the same rotation around the door
hinge. If `p_hinge` is the hinge position, `p_base_start` is the grasp-time
base position, and `R(theta)` is the planar hinge rotation, the base goal is:

    p_base(theta) = p_hinge + R(theta) * (p_base_start - p_hinge)

The base yaw also increases by `theta`. This keeps the door, handle, gripper,
and robot base in a coherent relative arrangement and avoids forcing the arm
to stretch across the full door arc.

## Accepted Result

The accepted run is configured by
`configs/entry_door_open_hold_close.yaml` and contains:

- 11 configured actions;
- 578 commanded states;
- opening from `0.0` to `1.0` rad;
- return to `0.0` rad;
- 99 environment collision geoms checked per state;
- 0 visual-overlap failures;
- 0 forbidden target-contact failures;
- 0 grasp-loss failures;
- maximum adjacent arm-joint step of `0.0298849` rad;
- 146 frames in each fixed-camera GIF.

The structured evaluation result is `PASS`. Front and top-view keyframes were
also inspected to confirm that the robot approaches the handle, keeps the
grasp while the door moves, and returns the door to the closed state.

## Evidence

- Config: `configs/entry_door_open_hold_close.yaml`
- Front view: `assets/entry_door_open_hold_close_generalized.gif`
- Top view: `assets/entry_door_open_hold_close_generalized_top_view.gif`
- Summary: `results/entry_door_open_hold_close_generalized_summary.json`
- Trajectory: `results/entry_door_open_hold_close_generalized_trajectory.json`

## Scope Boundary

This result demonstrates cross-object reuse of a configuration-driven,
collision-checked kinematic task framework. It does not claim automatic
perception, force-controlled grasping, dynamic wheel actuation, or zero-adapter
generalization to an arbitrary unseen object.
