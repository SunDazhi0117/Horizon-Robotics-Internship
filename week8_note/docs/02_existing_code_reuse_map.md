# Existing Code Reuse Map

## 1. Keep Stable Week 7 Code in Place

The reusable Week 7 implementation remains in:

    week7_note/task_system/

Week 8 imports these modules directly. This preserves the Week 7 tests and stable results while clearly separating existing capabilities from new Week 8 work.

## 2. Components Reused by the New Task

### TaskState

Stores:

    base
    arm_qpos
    gripper
    object_joints
    active_target

The microwave task only needs a new joint name in `object_joints`; it does not require a new state class.

### move_base

Moves the robot base into the microwave operation region. Only the waypoints change; the motion algorithm is reused.

### move_arm

Connects arm-joint waypoints while limiting the maximum change between adjacent states.

### grasp_target

Accepts the microwave handle geom, solves arm IK, and closes the gripper.

### follow_hinge_joint

Accepts the microwave-door body, hinge joint, and target angle, then keeps the hand following the moving door.

### change_gripper and hold_pose

Release the gripper and hold the current task state, respectively.

### MujocoStateAdapter

Writes a `TaskState` into `data.qpos`, calls `mj_forward`, and reads the resulting state back.

### PandaStateValidator

Checks:

- visual overlap between the robot and the environment;
- forbidden handle contacts;
- whether both fingers remain on the target;
- consistency between written and recovered states;
- excessive arm-joint changes between adjacent states.

## 3. Reusable Capabilities Added in Week 8

### discover_articulation

Starting from a target handle, discovers:

    handle geom
    -> owning body
    -> moving door body
    -> hinge joint
    -> axis and range

### approach_target

Uses target position and orientation to generate:

    safe pre-grasp pose
    -> collision-checked approach path
    -> final grasp pose

These capabilities allow microwave doors, entry doors, and cabinet doors to share the same execution framework more easily.
