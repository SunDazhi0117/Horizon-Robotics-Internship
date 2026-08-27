# 00. Prerequisite Simulator Notes

This file keeps the useful background from the earlier Week5 notes in a compact form.
The current Week5 main track is now MuJoCo learning, mobile robot loading, and future
SceneSmith/Articraft-to-MuJoCo conversion.

## Viewer vs Simulator

Our Week4 viewer scenes are good for visual inspection:

```text
SceneSmith / Articraft assets
-> Blender / GLB
-> Three.js viewer
-> human inspection
```

This is not the same as robot simulation.

A robot simulator also needs:

- collision geometry
- joints and joint limits
- mass and inertia
- contact behavior
- actuator/control interfaces
- queryable simulation state

So a final `.glb` is useful for demo and screenshots, but it is not enough by itself
for robot tasks.

## Current Scene Sources

Current fixed visual scene:

```text
/home/users/dazhi.sun-labs/projects/scenesmith/outputs/2026-06-30/17-25-40/scene_000/stable_scene_v1_plus_microwave_v1
```

Useful viewer/demo files:

- `stable_scene_v1_plus_microwave_v1.glb`
- `stable_scene_v1_plus_microwave_v1.blend`
- `scene_viewer.html`
- screenshots and acceptance reports

Useful simulator/conversion source files in the parent `scene_000` folder:

- `room_studio/scene_states/scene_after_furniture/scene.dmd.yaml`
- `room_studio/scene_states/scene_after_furniture/scene_state.json`
- `room_geometry/room_geometry_studio.sdf`
- `room_studio/generated_assets/furniture/sdf/...`
- `package.xml`

Useful Articraft source object:

```text
/home/users/dazhi.sun-labs/projects/articraft/data/cache/record_materialization/rec_create-a-complex-articulated-microwave-oven-as-a_20260622_093428_040254_ec41899c/model.urdf
```

## Format Summary

| Format | Main use | Robot-simulation value |
| --- | --- | --- |
| GLB / glTF | Browser viewing and visual demo | Good visual reference, weak physics source |
| BLEND | Blender assembly and inspection | Useful for export/inspection, not simulator-native |
| URDF | Robot or articulated object description | Useful for links, joints, collision, inertial data |
| SDF | Richer robot/object/world description | Useful for Drake/Gazebo-style simulation assets |
| DMD YAML | Drake model directives | Useful for composing a full Drake scene |
| MJCF XML | MuJoCo native model format | Best target for MuJoCo simulation |
| USD | Isaac Sim / Omniverse scene format | Possible later path, not current priority |

## SceneSmith Path

SceneSmith's useful simulation-oriented path is:

```text
natural language prompt
-> SceneSmith stages
-> floor / walls / windows / furniture
-> SDF assets + scene_state.json
-> Drake directives (.dmd.yaml)
-> simulator or exporter
```

Our Week4 demo path was:

```text
SceneSmith / Articraft output
-> Blender assembly
-> GLB
-> browser viewer
```

The demo path is easier to inspect, but the simulator path is the one needed for robot
tasks.

## Drake Notes

Drake is the closest match to SceneSmith's native representation because SceneSmith
stores full scenes through:

```text
.dmd.yaml + .sdf + package.xml + mesh assets
```

We already tested:

- loading the base SceneSmith room and furniture into Drake
- adding the Articraft microwave URDF
- adding a Panda-shaped test robot
- visualizing the result in MeshCat
- sampling Panda animation collisions

This was useful for understanding robot loading, but it is no longer the main Friday
plan.

## MuJoCo Notes

MuJoCo's clean native target is:

```text
MJCF XML
```

It can load some URDF models, but URDF often needs cleanup:

- mesh paths
- actuator definitions
- contact/collision settings
- inertial values
- joint naming and limits

For our future MuJoCo path, the expected conversion is:

```text
SceneSmith room/furniture
-> simplified collision + MJCF world

Articraft microwave / door / cabinet
-> URDF or converted MJCF
-> preserve hinge / slider joints

mobile robot
-> URDF or MJCF
-> actuator control
```

## Current Project Boundary

Completed:

- SceneSmith room generation
- stable static room + furniture demo
- Articraft microwave integration
- multi-articulated interactive demo
- viewer validation
- initial Drake robot-loading experiment

Not completed:

- MuJoCo import of our generated scene
- mobile robot loading in MuJoCo
- robot control
- motion planning
- physical manipulation of hinges
- benchmark/task suite

## Current Week5 Direction

The current useful path is:

```text
1. Learn MuJoCo tutorial basics.
2. Build a minimal hinge-door MJCF.
3. Load a simple existing mobile robot URDF/MJCF.
4. Drive the robot in a simple environment.
5. Convert or rebuild our generated scene into MuJoCo.
6. Let the robot interact with a hinge object.
```

