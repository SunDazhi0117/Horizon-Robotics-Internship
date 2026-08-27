# Native SceneSmith Scene Import Into MuJoCo

## Goal

Import an existing SceneSmith scene into MuJoCo without generating a new room, new assets, robot, or task.

This version uses SceneSmith's native scene structure instead of treating the exported GLB as one merged mesh.

## Source Scene

Source SceneSmith output:

```text
/home/users/dazhi.sun-labs/projects/scenesmith/outputs/2026-07-03/19-02-49/scene_000
```

Important source files:

```text
combined_house_after_furniture/house_furniture_welded.dmd.yaml
combined_house_after_furniture/house_state.json
floor_plans/
room_geometry/
room_study/
package.xml
```

## MuJoCo Export

Generated MuJoCo scene:

```text
/home/users/dazhi.sun-labs/projects/week5_note/pipeline/native_scene_import/mujoco_export/scene.xml
```

Generated mesh directory:

```text
/home/users/dazhi.sun-labs/projects/week5_note/pipeline/native_scene_import/mujoco_export/meshes/
```

This export contains separate meshes for:

- floor
- north, south, east, and west walls
- window
- study desk
- office side chair
- bookcase

## Validation Result

MuJoCo loaded the scene successfully.

```text
nbody = 9
ngeom = 404
nmesh = 397
njnt = 0
nq = 0
```

The scene has no joints because this step only imports the existing SceneSmith room and furniture as static geometry.

## Render Outputs

Rendered preview images:

```text
outputs/native_scene_diag.png
outputs/native_scene_top.png
outputs/native_scene_front.png
outputs/native_scene_side.png
```

The top view confirms that the room is not just a floor board. It includes walls, floor, window, and furniture.

## What This Completes

Completed:

- Existing SceneSmith room loaded into MuJoCo.
- SceneSmith room structure preserved better than the earlier GLB-to-OBJ test.
- MuJoCo offscreen rendering works.
- A complete room with furniture is visible from the top camera.

Not completed:

- Robot loading.
- Robot control.
- Articulated object import.
- Task definition.
- Dynamic physics validation.

## Why This Is Better Than The Earlier GLB Test

The earlier GLB-to-OBJ pipeline proved that MuJoCo could load a mesh, but the exported OBJ behaved like one merged static object and visually looked mostly like a board.

This native export follows SceneSmith's own scene representation, so the MuJoCo XML contains separate scene components instead of one merged object.

## Next Step

The next safe step is to add a very simple robot or mobile base into this already-loaded static room, while keeping the room unchanged.
