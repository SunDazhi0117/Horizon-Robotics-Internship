# Week 8 Robot-Task Generalization Report

## 1. Project Overview

The goal of this stage was not to hand-code another microwave-specific robot trajectory. Instead, it reorganized actions already validated on the Week 7 cabinet-door task into reusable capabilities, composed them through YAML configuration, and adapted the task to target-pose changes and local obstacles.

The final system performs this sequence:

    read microwave and handle state
    -> generate robot work-pose candidates in the target frame
    -> generate candidate detour points automatically
    -> validate candidate routes one by one
    -> reject unsafe candidates
    -> select a safe candidate
    -> approach and grasp the handle
    -> open the microwave door
    -> hold and close the door
    -> release and retreat
    -> save the trajectory, videos, and structured evaluation

This workflow validates action reuse, configuration composition, target-relative coordinates, candidate-route fallback, and automatic candidate generation. It is a configuration-driven kinematic task system, not a learned policy or a complete global path planner.

## 2. Development Stages

### Stage 1: Fixed-Coordinate Baseline

The first configuration stored a robot pose directly in world coordinates:

    waypoints:
      - [3.52167, 3.33753, 0.05]

The robot completed the microwave task, but this coordinate did not update when the microwave moved.

### Stage 2: Target-Relative Work Pose

`move_near_target` replaced the fixed coordinate with an offset relative to the handle:

    target_geom: week8_microwave_handle_proxy
    base_offset: [-0.32700001, -0.60800185]
    yaw_offset: 0.05

The program reads the current handle pose and transforms the local offset into a world-space robot pose.

### Stage 3: Validation with a Moved Object

An independent derived scene translates the complete microwave by `[+0.15, -0.05, 0.0] m` and rotates it by `10 degrees`. The transform is applied consistently to 11 static shell meshes and 5 articulated bodies: the door, tray, turntable, and two knobs.

Without modifying the same target-relative configuration, the robot work pose changes automatically from:

    [3.52167, 3.33753, 0.05]

to:

    [3.83123890, 3.20665270, 0.22453293]

The complete task still passes.

### Stage 4: Manually Specified Candidate Fallback

A red cylinder is added at the preferred work pose. The configuration supplies `preferred` and `backup_right`. After detecting a collision on the preferred route, the system tries the backup route.

This stage exposed an important distinction: reaching and grasping from a pose does not guarantee that the door can be opened from that pose. The first backup pose caused an arm-joint discontinuity greater than `0.15 rad` during opening, so complete-task validation rejected it. The final backup offset `[0.0, -0.60]` passed navigation, grasping, opening, and closing.

### Stage 5: Automatically Generated Candidates

The final configuration describes search rules instead of listing candidate coordinates:

    candidate_search:
      stand_distance: 0.60
      center_angle_degrees: -118.27257832
      angle_offsets_degrees: [0.0, 28.27257832, -25.0, 55.0, -55.0]
      detour_distance: 1.25

The program generates five candidate work poses and their outer detour points. `auto_01` is rejected because it conflicts with the obstacle; the system selects `auto_02` and completes the task.

### Stage 6: Structured Decision Trace

The latest summary JSON records the following for every candidate:

- candidate identifier;
- target-local base offset;
- target-local detour offset;
- transformed world-space waypoints;
- route length;
- selected or rejected status;
- failure reason;
- number of generated states for the selected route.

The system therefore reports not only what it selected but also why it made that choice.

## 3. Relationship Between Configuration and Code

The configuration is the task specification, Python is the action toolbox, and `TaskExecutor` is the dispatcher:

    YAML configuration
    -> load_task_config
    -> Python dictionary
    -> TaskExecutor reads each action
    -> action registry finds the Python function
    -> function generates a TaskState sequence
    -> MuJoCo adapter applies each state
    -> validator checks geometry and contacts

The configuration does not store Python functions. It stores:

- which action to call;
- action order;
- target names;
- numeric parameters;
- search rules;
- acceptance limits.

For example:

    - action: follow_hinge_joint
      joint_name: microwave_hinge
      moving_body: microwave_door
      target_angle: 1.0

The executor finds `follow_hinge_joint()` in the action registry and passes the configured joint, body, and angle into the Python function.

## 4. Reused Week 7 Components

Week 8 did not copy the complete cabinet-door script. It imports the reusable system from `week7_note/task_system/`:

- `TaskState`: stores base, arm, gripper, and object-joint states;
- `move_base`: generates a smooth base trajectory;
- `move_arm`: limits adjacent arm-joint changes;
- `change_gripper`: opens and closes the fingers smoothly;
- `hold_pose`: preserves the current state;
- `grasp_target`: solves target-relative grasp IK and closes the gripper;
- `follow_hinge_joint`: maintains the hand-door relationship while the door rotates;
- `MujocoStateAdapter`: converts between `TaskState` and MuJoCo qpos;
- `PandaStateValidator`: checks overlap, forbidden contact, and grasp retention;
- `TaskExecutor`: composes actions in YAML order.

Week 8 adds reusable target discovery, target-relative work poses, candidate generation, detour fallback, and structured decision recording.

## 5. Target-Relative Coordinate Principle

A fixed world coordinate is valid for only one object pose. Target-relative positioning expresses the robot work pose in the target-handle frame.

Let `p_target` be the target world position, `R_target` its rotation matrix, and `p_offset` the local offset in the configuration. The robot world position is:

    p_robot = p_target + R_target * p_offset

When the microwave translates, `p_target` changes. When it rotates, `R_target` changes. The same local offset therefore follows both position and orientation changes.

Robot yaw is computed from the target orientation and `yaw_offset`. The implementation chooses the equivalent yaw closest to the current heading to avoid unnecessary full rotations.

The corresponding implementation is:

    week8_note/scripts/target_approach.py
    target_relative_base_goal()

## 6. Automatic Candidate Generation

Work-pose candidates are generated in polar coordinates within the target-local frame. For distance `r` and angle `theta`:

    x = r * cos(theta)
    y = r * sin(theta)

`center_angle_degrees` defines the center of the search, and `angle_offsets_degrees` defines the order of directions to try. `stand_distance` creates the final work pose, while `detour_distance` creates a farther point in the same direction.

The implementation is:

    generate_target_relative_base_candidates()

It returns candidate dictionaries in the same format as manually configured candidates, so the downstream selector does not need to know how they were created.

## 7. Route Validation and Fallback

For each candidate, `move_near_target()`:

1. transforms local offsets into world-space waypoints;
2. uses `move_base()` to densely interpolate between waypoints;
3. calls `PandaStateValidator.validate()` for every `TaskState`;
4. checks visual overlap against 96 environment geoms;
5. records a collision reason and continues with the next candidate;
6. returns the first candidate trajectory that passes;
7. raises an error with detailed reasons if all candidates fail.

The latest real decision trace is:

    auto_01
      route length: 1.046846 m
      result: rejected
      reason: visual overlap at generated state 69

    auto_02
      route length: 1.384194 m
      result: selected
      generated navigation states: 100

The system does not cross the obstacle merely because `auto_01` is shorter. Safety constraints take priority.

## 8. Grasp and Hinge-Follow Logic

### Grasping

`grasp_target()` uses a hand offset and rotation defined in the handle frame to calculate an end-effector target pose. IK solves the seven Panda joint angles, followed by:

    move_arm to grasp pose
    -> change_gripper
    -> verify two-finger contact

The original microwave handle did not participate in collision detection. Week 8 therefore adds a transparent handle proxy and door-collision proxy in an independent derived XML. These proxies support contact and penetration checks without changing the visible model.

### Opening and Closing

`follow_hinge_joint()` first records the hand pose relative to the microwave-door body. After increasing the door hinge by a small angle, it recomputes the door world pose and solves new arm IK so that the hand continues following the handle.

Every state checks:

- excessive adjacent joint changes;
- whether both fingers remain in contact with the target;
- overlap with the shell, furniture, or obstacle;
- forbidden contacts.

## 9. Coding Call Chain

The entry script is:

    week8_note/scripts/run_microwave_open_close.py

Its primary execution order is:

    create_microwave_runtime(task_xml)
    -> create MjModel and MjData
    -> create MujocoStateAdapter
    -> create PandaStateValidator
    -> create TargetApproachActions
    -> merge DEFAULT_ACTIONS and manipulation.action_registry()
    -> load YAML configuration
    -> TaskExecutor.execute(config)
    -> validate all generated states
    -> render front and top-view GIFs
    -> save trajectory and summary JSON

Scene derivation is handled by:

    week8_note/scripts/microwave_pose_variant.py

It:

- leaves the stable XML unchanged;
- translates and rotates the complete microwave;
- applies the same transform to static meshes and articulated bodies;
- adds a test obstacle at the preferred work pose;
- saves a scene-transformation report.

## 10. Final Action Sequence

The final YAML contains 11 actions:

    hold_pose
    -> move_near_target
    -> approach_target
    -> grasp_target
    -> follow_hinge_joint(open)
    -> hold_pose
    -> follow_hinge_joint(close)
    -> change_gripper(release)
    -> retreat_from_target
    -> move_arm(home)
    -> hold_pose

`phase` labels a task stage; `action` determines which Python function is called.

## 11. Final Acceptance Result

Latest automatic-candidate task:

- Task: `microwave_open_hold_close_auto_candidates`
- Selected candidate: `auto_02`
- States: 504
- Actions: 11
- Checked environment geoms: 96
- Maximum microwave-door angle: `1.0 rad`
- Final microwave-door angle: `0.0 rad`
- Final gripper opening: `0.04`
- Maximum adjacent arm-joint step: `0.0760742 rad`
- Visual-overlap failures: 0
- Forbidden target-contact failures: 0
- Grasp-loss failures: 0
- Front-view video frames: 169
- Top-view video frames: 169
- Week 8 tests: 10/10 passed
- Final result: PASS

## 12. Saved Evidence

Configuration:

    configs/microwave_open_hold_close_auto_candidates.yaml

Results:

    results/microwave_auto_candidates_blocked_preferred_summary.json
    results/microwave_auto_candidates_blocked_preferred_trajectory.json

Videos:

    assets/microwave_auto_candidates_blocked_preferred.gif
    assets/microwave_auto_candidates_blocked_preferred_top_view.gif

Code:

    scripts/target_approach.py
    scripts/articulation_discovery.py
    scripts/microwave_runtime.py
    scripts/microwave_pose_variant.py
    scripts/run_microwave_open_close.py

## 13. Generalization Achieved

- The same Python actions are used for cabinet and microwave doors.
- YAML changes the order and parameters of reusable actions.
- Robot work poses follow target translation and rotation.
- The configuration describes a search region rather than explicit candidate coordinates.
- Python generates candidate work poses and detour points automatically.
- The system falls back automatically when the preferred route is blocked.
- Every candidate decision has a structured reason record.
- The complete task still validates collision, grasp retention, and joint continuity.

## 14. Current Limitations

- No independent natural-language parser generates reliable YAML automatically.
- There is no A*, RRT, or navigation-mesh global planner.
- The candidate search region is still provided by the configuration.
- Passing navigation checks does not guarantee manipulation feasibility; grasping and opening still require complete-task validation.
- The current system mainly uses qpos and `mj_forward` for kinematic validation.
- There is no force control, sensor feedback, or learned policy.
- Statistical evaluation across many randomized object poses and obstacle layouts has not been completed.

## 15. Conclusion

This stage advances the project from one task with one dedicated trajectory to reusable actions, YAML composition, target-relative coordinates, automatic candidate generation, and collision-aware fallback.

The result is more than a video demonstration. The system stores its task configuration, 504 generated states, candidate decision trace, per-state collision results, grasp-retention results, front and top-view videos, and ten passing automated tests.

The most valuable next step is to add manipulation-reachability scoring to candidate work poses and use A* or RRT for navigation around more complex obstacles. The same task system can then be evaluated on cabinet doors and entry doors.
