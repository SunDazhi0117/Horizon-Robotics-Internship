"""Convert the selected SceneSmith GLB into a MuJoCo-friendly OBJ.

Run with Blender:
  blender --background --python scripts/convert_glb_to_obj.py
"""

from __future__ import annotations

import bpy

from pathlib import Path


ROOT = Path("/home/users/dazhi.sun-labs/projects/week5_note/pipeline/static_scene_import")
SOURCE_GLB = Path(
    "/home/users/dazhi.sun-labs/projects/scenesmith/"
    "outputs/2026-07-03/19-02-49/scene_000/simple_study_room.glb"
)
OUTPUT_OBJ = ROOT / "assets/simple_study_room.obj"


def main() -> None:
    if not SOURCE_GLB.is_file():
        raise FileNotFoundError(SOURCE_GLB)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    bpy.ops.import_scene.gltf(filepath=str(SOURCE_GLB))

    # Keep only mesh objects and apply transforms so MuJoCo receives geometry in
    # the same world pose as the GLB scene.
    for obj in bpy.context.scene.objects:
        obj.select_set(obj.type == "MESH")
    bpy.context.view_layer.objects.active = next(
        obj for obj in bpy.context.scene.objects if obj.type == "MESH"
    )
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    OUTPUT_OBJ.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.obj_export(
        filepath=str(OUTPUT_OBJ),
        export_selected_objects=True,
        export_materials=True,
        forward_axis="Y",
        up_axis="Z",
    )
    print(f"source_glb={SOURCE_GLB}")
    print(f"output_obj={OUTPUT_OBJ}")


if __name__ == "__main__":
    main()
