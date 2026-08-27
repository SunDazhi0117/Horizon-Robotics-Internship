# Microwave Task Reuse Result

## What Was Implemented

Week 8 did not rename a copy of the cabinet-door task. It reused the Week 7 actions for base motion, arm motion, grasping, hinge following, holding, releasing, and retreating. The new microwave task is defined mainly by the action order and parameters in `configs/microwave_open_hold_close.yaml`.

## New Reusable Capabilities

`discover_articulation` starts from a target handle geom and automatically finds its door body, joint type, axis, motion range, and qpos address.

`move_near_target` reads the current world position and orientation of a target geom. It transforms a target-local base offset from the configuration into world coordinates and selects the equivalent yaw closest to the robot's current orientation. If the target is translated or rotated, the calculated docking pose changes with it.

`approach_target` divides a direct approach into several safe distances. At each stage it solves IK, interpolates the path, and checks environment overlap and forbidden contacts. `retreat_from_target` uses the same safe distances in reverse.

## Why a Derived Model Is Required

The original microwave handle had collision disabled, so it could not verify whether the fingers really touched the handle. Week 8 adds a transparent handle proxy and a door-collision proxy in its own XML without modifying the original Week 6 or Week 7 assets.

The original ground-mounted Panda also could not reach the microwave handle at approximately `1.19 m`. The derived Panda model keeps the wheeled base on the floor, raises the arm mount by `0.48 m`, and adds a visible, collidable support column.

## Action Chain

    hold
    -> move_near_target
    -> approach_target
    -> grasp_target
    -> follow_hinge_joint(open to 1.0 rad)
    -> hold
    -> follow_hinge_joint(close to 0.0 rad)
    -> release
    -> retreat
    -> move_arm home
    -> hold

## Acceptance Result

The task passed with 401 states and 11 actions. The microwave door opened from `0.0 rad` to `1.0 rad` and returned to `0.0 rad`. Environment visual-overlap, forbidden target-contact, and grasp-loss failure counts were all 0. The maximum adjacent arm-joint change was `0.0548699 rad`.

The front and top-view GIFs each contain 201 frames and were inspected manually. The top view verifies that the arm does not pass through the microwave body; the front view verifies the approach, grasp, opening, closing, and retreat relationships.

## What This Result Demonstrates

The result shows that reusable actions from the cabinet-door task can transfer to a microwave door by changing the configuration, target, and a small amount of reusable adaptation logic. It does not yet demonstrate a physically simulated grasp: execution writes qpos values and calls `mj_forward` to generate and validate kinematic states, without force control, sensor feedback, or a learned policy.

## Target-Pose Generalization Upgrade

The baseline configuration stored the final base pose directly in world coordinates as `[3.52167, 3.33753, 0.05]`. The upgraded configuration uses:

    target_geom: week8_microwave_handle_proxy
    base_offset: [-0.32700001, -0.60800185]
    yaw_offset: 0.05

Unit tests verify that the base goal follows translation and rotation of the target frame. The upgraded complete task still passes with 401 states, 11 actions, a maximum door angle of `1.0 rad`, and zero environment-overlap, forbidden-contact, or grasp-loss failures. This capability handles target-pose changes but is not a complete global path planner; the relative distance and docking direction are still supplied by the configuration.
