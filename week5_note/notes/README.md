# Week5 Note: MuJoCo + Mobile Robot Preparation

Week5 now focuses on the practical path toward robot simulation in MuJoCo.

Current learning goal:

```text
MuJoCo basics
-> load an existing mobile robot
-> drive it in a simple simulation environment
-> later import our generated SceneSmith / Articraft assets
-> eventually manipulate hinged objects
```

## Current Friday Plan

1. Study the MuJoCo tutorial and related examples.
2. Build small MJCF exercises, especially hinge joints and actuator control.
3. Find an existing mobile robot URDF or MJCF model.
4. Put the robot into a simple simulation scene and drive it.
5. Plan how to convert or rebuild our generated SceneSmith / Articraft scene in MuJoCo.

## Notes

- [00_prerequisite_simulator_notes.md](docs/00_prerequisite_simulator_notes.md)  
  Compact background notes from the earlier SceneSmith/Articraft/Drake simulator investigation.
- [01_mujoco_core_concepts.md](docs/01_mujoco_core_concepts.md)  
  The MuJoCo concepts to understand first: `mjModel`, `mjData`, MJCF, joints, actuators, `qpos`, `qvel`, `ctrl`, `mj_step`, rendering, and task success checks.
- [02_mujoco_scene_import_test.md](docs/02_mujoco_scene_import_test.md)  
  First practical test exporting an existing SceneSmith room/furniture scene into MuJoCo MJCF and rendering a preview.
- [04_hinge_door_mujoco_demo.md](docs/04_hinge_door_mujoco_demo.md)  
  Minimal MuJoCo hinge-door demo with actuator control, GIF rendering, and PASS / FAIL validation.

## Practical Next Steps

Recommended small tasks:

- Write a minimal `hinge_door.xml`.
- Write a Python script that opens and closes the hinge door.
- Learn how `mjModel`, `mjData`, `qpos`, `qvel`, `ctrl`, `geom`, `joint`, and `actuator` work.
- Test one existing mobile robot model in a very simple world.
- Keep SceneSmith/Articraft conversion as the later step, not the first step.

## Boundary

This folder is for learning notes and planning. It should not claim that we already
have a MuJoCo robot task suite.

Current status:

- We have generated and viewed interactive scenes.
- We have done an initial Drake robot-loading experiment.
- We have imported one static SceneSmith room/furniture scene into MuJoCo MJCF.
- We have run a minimal MuJoCo hinge-door demo with one joint and one actuator.
- We have not yet driven a mobile robot in MuJoCo.
- We have not yet completed robot manipulation of hinged objects.
