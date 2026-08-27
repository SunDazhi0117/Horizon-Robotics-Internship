# Week5: MuJoCo Simulation Preparation

Week5 is organized around one main goal:

```text
learn MuJoCo
-> import an existing SceneSmith scene as a static mesh
-> build a minimal articulated-object demo
-> prepare for mobile robot loading later
```

## Folder Structure

```text
week5_note/
  README.md
  notes/
    README.md
    docs/
  experiments/
    hinge_door/
  pipeline/
    stretch_robot/
    static_scene_import/
    native_scene_import/
    articulated_demo_mujoco/
```

## Main Sections

- `notes/`  
  Learning notes and project explanations.

- `experiments/hinge_door/`  
  Minimal MuJoCo hinge-door demo using one hinge joint and one actuator.

- `pipeline/static_scene_import/`  
  Phase 1 pipeline: existing SceneSmith GLB -> OBJ -> MuJoCo MJCF -> rendered PNG.

- `pipeline/native_scene_import/`  
  Improved Phase 1 pipeline: existing SceneSmith native scene files -> MuJoCo XML -> rendered complete room preview.

- `pipeline/articulated_demo_mujoco/`  
  Static MuJoCo import test for the most complex multi-articulated demo room.

- `pipeline/stretch_robot/`  
  Standalone Hello Robot Stretch loading and actuator smoke test.

## Current Status

Completed:

- MuJoCo core concept notes.
- Existing SceneSmith GLB imported as a static MuJoCo mesh.
- Static scene rendered with MuJoCo offscreen renderer.
- Existing SceneSmith native scene exported to MuJoCo with separate room and furniture meshes.
- Complete room preview rendered from multiple camera views.
- Most complex articulated demo room imported into MuJoCo as static geometry and rendered from multiple views.
- Reconstructed 8 articulated joints from the complex demo scene into MuJoCo.
- Added 8 position actuators and validated actuator-driven joint motion with `data.ctrl` and `mj_step`.
- Added a minimal geometric mobile-base smoke test inside the MuJoCo scene.
- Downloaded Hello Robot Stretch from MuJoCo Menagerie.
- Validated standalone Stretch loading and actuator motion.
- Merged real Stretch into the generated articulated room and validated movement.
- Minimal hinge-door demo with actuator control and PASS / FAIL validation.

Not yet completed:

- Contact-rich robot manipulation.
- Full robot navigation with collision-aware validation.
- Articraft articulated object import into MuJoCo.
- Robot manipulation task.
