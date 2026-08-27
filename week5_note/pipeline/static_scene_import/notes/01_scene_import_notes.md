# 01. Scene Import Notes

## Goal

Phase 1 only tests whether an existing SceneSmith scene can be used as a static
mesh inside MuJoCo and rendered successfully.

This phase does not:

- generate a new SceneSmith scene
- generate new assets
- add a robot
- run a manipulation task
- preserve articulated joints

## Source Scene

Selected source GLB:

```text
/home/users/dazhi.sun-labs/projects/scenesmith/outputs/2026-07-03/19-02-49/scene_000/simple_study_room.glb
```

This was chosen because it is the requested preferred source for a simple MuJoCo
static scene import test.

## Why GLB Is Not Equal To A MuJoCo Simulation Scene

GLB is good for visual display, browser viewing, and quick inspection. However,
a robot simulator usually needs more than visual mesh data:

- collision geometry
- mass and inertia
- joint types and limits
- actuator definitions
- contact/friction settings
- semantic names for robot and object state queries

For Phase 1, the GLB is used only as a static visual mesh. It is not treated as a
complete robot-ready simulation scene.

## Why Convert GLB To OBJ

MuJoCo can load mesh assets from files referenced in MJCF. OBJ is a simple mesh
format that MuJoCo can reference directly from:

```text
<asset>
  <mesh file="..."/>
</asset>
```

The conversion path is:

```text
SceneSmith GLB
-> Blender or trimesh import
-> OBJ export
-> MuJoCo MJCF mesh asset
```

## Current Output

Converted mesh:

```text
/home/users/dazhi.sun-labs/projects/week5_note/pipeline/static_scene_import/assets/simple_study_room.obj
```

MJCF file:

```text
/home/users/dazhi.sun-labs/projects/week5_note/pipeline/static_scene_import/xml/scene_only.xml
```

Render script:

```text
/home/users/dazhi.sun-labs/projects/week5_note/pipeline/static_scene_import/scripts/01_render_scene.py
```

Expected render output:

```text
/home/users/dazhi.sun-labs/projects/week5_note/pipeline/static_scene_import/outputs/scene_render.png
```

Actual render summary:

```text
XML loaded: yes
OBJ mesh loaded: yes
render image generated: yes
render image non-empty: yes
```

Model statistics:

```text
bodies = 1
joints = 0
geoms  = 2
meshes = 1
actuators = 0
```

Converted OBJ:

```text
mesh_count = 14
vertices   = 360090
faces      = 120168
file size  = 15 MB
```

Rendered image:

```text
image size = 800 x 600
file size  = 143 KB
```

Commands used:

```bash
cd /home/users/dazhi.sun-labs/projects/scenesmith
source .mujoco_venv/bin/activate
python /home/users/dazhi.sun-labs/projects/week5_note/pipeline/static_scene_import/scripts/convert_glb_to_obj_trimesh.py
python /home/users/dazhi.sun-labs/projects/week5_note/pipeline/static_scene_import/scripts/01_render_scene.py
```

## Current Completion Criteria

Phase 1 is considered successful if:

- `scene_only.xml` loads with `mujoco.MjModel.from_xml_path`
- the OBJ mesh path resolves correctly
- `mujoco.Renderer` writes `outputs/scene_render.png`
- the image is not blank

Current status:

```text
PASS
```

## Not Completed Yet

This phase does not yet include:

- mobile robot loading
- robot control
- articulated microwave / door / cabinet
- hinge or slide manipulation
- task success logic
- physical collision simplification

## Next Step

After static scene rendering works, the next phase should add a simple mobile
robot in a separate test scene first. Only after the robot can move in a simple
MuJoCo world should it be placed into the imported SceneSmith room.
