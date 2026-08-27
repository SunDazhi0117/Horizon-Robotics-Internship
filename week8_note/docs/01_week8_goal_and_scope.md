# Week 8 Goals and Scope

## 1. Primary Goal

Week 8 is not intended to prove that the robot can open the same cabinet door again. The central question is:

> Can the reusable actions validated on the cabinet-door task be transferred to a new articulated object without rewriting the complete task implementation?

The first new task is opening and closing a microwave door.

## 2. What Generalization Means Here

Previous approach:

    Cabinet-door task -> one task-specific Python script
    Microwave task    -> another task-specific Python script
    Entry-door task   -> another task-specific Python script

Week 8 approach:

    The same reusable Python actions
    + different target names
    + different initial states
    + different joint parameters
    + different YAML action sequences
    -> different tasks

Success is determined by whether a new task is expressed mainly through configuration, not by the number of lines of code.

## 3. Permitted Additions

Appropriate additions include:

- reusable logic for discovering a target geom, body, and joint;
- reusable logic for computing a pre-grasp pose;
- collision-checked target approach logic;
- a YAML configuration for the microwave task;
- validation reports and videos for the new task.

The following should not be added:

- a renamed copy of the Week 7 cabinet-door script;
- a frame-by-frame hard-coded microwave trajectory;
- a complete set of actions that works only for one microwave;
- changes to the stable Week 7 Level 1-5 results.

## 4. Starting Point and Current Boundary

The project already provided:

- a reusable `TaskState`;
- a configuration-driven `TaskExecutor`;
- reusable trajectory primitives;
- `grasp_target`;
- `follow_hinge_joint`;
- a MuJoCo state adapter;
- Panda visual-overlap and forbidden-contact validation.

Week 8 added:

- discovery of the moving body, joint, axis, and range from a target geom;
- staged IK and per-state validation for approaching a new handle;
- a YAML sequence for opening, holding, closing, releasing, and retreating;
- front and top-view GIFs with numerical and visual acceptance checks.

With a fixed base, the door opens reliably to `1.0 rad`; the implementation does not force it to the model limit of `1.75 rad`. The trajectory is validated by writing qpos and calling `mj_forward`, so this result does not yet represent force control or a physically simulated grasp.
