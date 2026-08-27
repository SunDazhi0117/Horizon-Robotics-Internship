# Week 8 New-Task Acceptance Criteria

## 1. Generalization Criteria

- Do not copy the complete cabinet-door task script.
- Do not hard-code the microwave trajectory frame by frame.
- Reuse the Week 7 `TaskState`, executor, grasp, and hinge-follow components.
- Express the new task mainly through YAML target names, angles, parameters, and action order.
- Ensure that new Week 8 code is useful for other hinged objects.

## 2. Task-Outcome Criteria

- The robot reaches the microwave operation region.
- The two fingers are positioned on opposite sides of the handle.
- The microwave door reaches the configured target angle.
- The robot closes the door after the hold phase.
- The gripper releases successfully at the end.
- Result files identify task phases and the phase of any failure.

## 3. Overlap and Contact Criteria

- Environment visual-overlap failure count is 0.
- Forbidden target-contact failure count is 0.
- The gripper does not lose the handle during grasping or door motion.
- The arm does not pass through the microwave door, shell, table, or wall.
- The base does not visibly overlap furniture.
- Adjacent joint changes remain below the configured limit.

## 4. Required Outputs

Acceptance requires at least:

    task YAML
    generated trajectory JSON
    validation summary JSON
    fixed-view GIF or MP4
    top-view GIF or MP4
    short implementation note

## 5. Measured Result

- Task status: PASS
- States: 401
- Actions: 11
- Maximum microwave-door angle: `1.0 rad`
- Final microwave-door angle: `0.0 rad`
- Final gripper opening: `0.04`
- Environment visual-overlap failures: 0
- Forbidden target-contact failures: 0
- Grasp-loss failures: 0
- Maximum adjacent arm-joint change: `0.0548699 rad`
- Front-view video: 201 frames
- Top-view video: 201 frames

The numerical checks and both fixed-view video inspections passed. The acceptance scope covers kinematic trajectories and geometric collision checks; it does not include actuator force control or contact-dynamics stability.
