# Reusable Task System Foundation

This package is the first generalization layer for the Week7 tasks. It does not replace or modify the accepted Level 1-5 trajectories.

## Files

- state.py defines TaskState, the common state class.
- primitives.py defines reusable trajectory operations.
- executor.py maps configured action names to Python functions.
- run_config.py provides a command-line runner.
- mujoco_adapter.py writes TaskState values into MjData and reads them back.
- panda_validation.py performs Panda overlap and target-contact checks.
- level5_integration.py validates the accepted Level 5 trajectory through the new API.
- mujoco_manipulation.py implements reusable grasp-target and hinge-follow actions.
- run_level5_reusable_demo.py regenerates a real left-door grasp and opening from YAML.
- configs/foundation_demo.yaml demonstrates action composition.
- configs/parameter_change_demo.yaml demonstrates parameter-only task changes.
- configs/level5_reusable_left_door.yaml drives real MuJoCo manipulation actions.

## Available actions

- hold_pose repeats the current state.
- move_base follows base waypoints.
- move_arm follows arm-joint waypoints.
- change_gripper opens or closes the gripper.
- grasp_target solves a target-relative hand pose and closes the gripper.
- follow_hinge_joint preserves the hand pose relative to a moving articulated body.

The first four actions operate only on trajectory state. The final two are
bound to a real MuJoCo model, use inverse kinematics, and reject generated
states with visual overlap, forbidden target contact, or a lost grasp.

## Run the example

From the projects directory:

    /home/users/dazhi.sun-labs/projects/scenesmith/.mujoco_venv/bin/python \
      -m week7_note.task_system.run_config \
      week7_note/task_system/configs/foundation_demo.yaml

Run the tests:

    /home/users/dazhi.sun-labs/projects/scenesmith/.mujoco_venv/bin/python \
      -m unittest discover -s week7_note/tests -p "test_task_system.py" -v

Validate all 429 accepted Level 5 states through TaskState and MjData:

    /home/users/dazhi.sun-labs/projects/scenesmith/.mujoco_venv/bin/python \
      -m week7_note.task_system.level5_integration

Generate and validate a left-handle grasp plus a 90-degree opening from YAML:

    /home/users/dazhi.sun-labs/projects/scenesmith/.mujoco_venv/bin/python \
      -m week7_note.task_system.run_level5_reusable_demo

The validation result is saved under task_system/results.

## Design rule

Python implements how an action works. YAML selects actions, targets, parameters, and order. A new task should reuse registered actions whenever possible instead of copying the complete Level 5 script.
