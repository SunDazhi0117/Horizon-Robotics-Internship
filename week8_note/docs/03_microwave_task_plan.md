# Microwave Task: Plan and Implementation

## 1. Task Name

`microwave_open_hold_close`

## 2. Initial State

- The microwave door is closed.
- The gripper is open.
- The robot starts in a collision-free location.
- The arm is in a safe folded or ready pose.

## 3. Action Sequence

    discover microwave articulation
    -> move_near_target using the microwave handle pose
    -> approach_target
    -> grasp_target
    -> follow_hinge_joint to the open angle
    -> hold_pose
    -> follow_hinge_joint back to zero
    -> change_gripper to release
    -> retreat

## 4. YAML Representation

The implemented configuration is stored in `configs/microwave_open_hold_close.yaml` and follows this structure:

    - action: approach_target
      target_geom: microwave_handle

    - action: grasp_target
      target_geom: microwave_handle

    - action: follow_hinge_joint
      joint_name: microwave_hinge
      moving_body: microwave_door
      target_angle: 1.0

    - action: hold_pose
      frames: 12

    - action: follow_hinge_joint
      joint_name: microwave_hinge
      moving_body: microwave_door
      target_angle: 0.0

    - action: change_gripper
      target: 0.04

At runtime, these task aliases map to the actual model names. Automatic discovery confirmed that the real door joint is `body_to_front_door`, its type is hinge, and its range is `[0.0, 1.75] rad`.

## 5. Implementation Sequence

1. List all bodies, geoms, and joints in the MuJoCo scene.
2. Confirm that the microwave door retains an articulated joint.
3. Identify the handle, door body, joint, axis, and motion range.
4. Implement and test articulation discovery.
5. Implement collision-checked `approach_target`.
6. Compose existing actions through YAML.
7. Validate every state and render fixed and top views.

All seven steps are complete. The first version used fixed world coordinates. The upgraded version reads the current handle pose and computes the robot work pose from a base offset expressed in the target frame. Under the fixed-base constraint, tests at several opening angles showed that `1.0 rad` is the largest accepted angle that reliably satisfies IK continuity, grasp retention, and collision constraints.
