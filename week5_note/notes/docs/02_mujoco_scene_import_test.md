# 02. MuJoCo Scene Import Test

## Goal

Test whether an existing SceneSmith scene can be exported into MuJoCo.

This is not a robot task yet. The goal is only:

```text
SceneSmith scene
-> MuJoCo MJCF
-> MuJoCo loads the scene
-> render a preview image
```

## Source Scene

Original SceneSmith scene:

```text
/home/users/dazhi.sun-labs/projects/scenesmith/outputs/2026-06-30/17-25-40/scene_000
```

The original folder did not contain the official `combined_house/house.dmd.yaml`
layout expected by the exporter. It did contain a room-level Drake directive:

```text
room_studio/scene_states/scene_after_furniture/scene.dmd.yaml
```

So a temporary adapter folder was created:

```text
/home/users/dazhi.sun-labs/projects/scenesmith/outputs/week5_mujoco_scene_test/scene_000_adapter
```

This adapter does not modify the original scene.

## MuJoCo Environment

SceneSmith's separate MuJoCo export environment was installed:

```text
/home/users/dazhi.sun-labs/projects/scenesmith/.mujoco_venv
```

Installed MuJoCo version:

```text
mujoco==3.3.5
```

## Exported MuJoCo Scene

Output folder:

```text
/home/users/dazhi.sun-labs/projects/scenesmith/outputs/week5_mujoco_scene_test/base_scene_mujoco
```

Main MJCF file:

```text
/home/users/dazhi.sun-labs/projects/scenesmith/outputs/week5_mujoco_scene_test/base_scene_mujoco/scene.xml
```

Preview image:

```text
/home/users/dazhi.sun-labs/projects/scenesmith/outputs/week5_mujoco_scene_test/base_scene_mujoco/preview.png
```

## Validation Result

MuJoCo successfully loaded and validated the exported scene.

Model statistics:

```text
bodies = 11
joints = 0
geoms  = 536
meshes = 529
```

The current exported scene includes:

- room geometry
- floor
- walls
- windows
- study desk
- office chair
- kitchen base counter
- storage shelving unit

## Current Limitation

This first MuJoCo import is static.

It does not yet include:

- Articraft microwave articulation
- movable door/cabinet joints
- mobile robot
- robot control
- hinge manipulation task

The `joints = 0` result means this export is currently a static environment test.

## Next Step

The next practical step is:

```text
simple MuJoCo mobile robot
-> load into this scene or a smaller test scene
-> drive it on the floor
```

After that:

```text
Articraft microwave / door / cabinet
-> convert or rebuild as MJCF articulated object
-> add hinge / slide joints
-> test robot interaction
```

