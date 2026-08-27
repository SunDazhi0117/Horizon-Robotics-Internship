# Week 7 Robot-Task Code Learning Guide

This folder is for learning only. It does not modify the stable Level 1-5 tasks, trajectories, or videos.

The objective is not to memorize every line. It is to understand how a robot task is decomposed into states, trajectories, validation, and results.

## Recommended Order for Beginners

1. [00_python_basics.md](00_python_basics.md): Python syntax used by this project.
2. [01_overall_workflow.md](01_overall_workflow.md): the complete execution workflow.
3. [02_task_sequence_and_state.md](02_task_sequence_and_state.md): task scripts and per-frame state.
4. [03_interpolation_and_motion.md](03_interpolation_and_motion.md): continuous motion between key poses.
5. [04_ik_and_door_following.md](04_ik_and_door_following.md): how the arm follows a handle.
6. [05_collision_and_validation.md](05_collision_and_validation.md): penetration and contact checks.
7. [06_rendering_and_evaluation.md](06_rendering_and_evaluation.md): videos and PASS/FAIL evaluation.
8. [07_generalization_plan.md](07_generalization_plan.md): reusing code for new tasks.
9. [08_generalization_implementation.md](08_generalization_implementation.md): the first reusable task system.

Read one document at a time. Run or trace the shortest examples by hand before moving on.

Each note answers four questions:

1. What is the code trying to do?
2. What does the Python syntax mean?
3. How do variable values change during execution?
4. What must you remember for this project?

## First-Pass Learning Goals

- Explain the difference between `mjModel` and `mjData`.
- Explain why `sequence` is a frame-by-frame task script.
- Identify what `base`, `qpos`, `finger`, and door-hinge values control.
- Explain how `append_state()` adds one state.
- Explain how interpolation connects two key poses.
- List the checks performed by `validate_state()`.
- Explain why a plausible video does not prove that a task passed.

You do not need to write inverse kinematics or memorize the MuJoCo API on the first pass.

## Safe to Skip Initially

- the full mathematical derivation of OBB intersection;
- detailed rotation-matrix and rotation-vector formulas;
- the numerical algorithm inside `least_squares`;
- XML mesh-path repair details;
- GIF encoding parameters.

## Related Source Files

- [Level 5 main task](../scripts/run_level_5_sequential_open_both_doors.py)
- [Shared collision validation](../scripts/level_validation_helpers.py)
- [Level 5 evaluation](../scripts/evaluate_level_5_sequential_open_both_doors.py)

## Final Self-Check

For any task-code block, answer:

1. Which task phase does it belong to?
2. Does it change the base, arm, gripper, or object joint?
3. Does it create one key pose or a continuous trajectory?
4. Is collision validation performed?
5. Which parameters must change for another door?
