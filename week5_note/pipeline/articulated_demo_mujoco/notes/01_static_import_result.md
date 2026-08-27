# Articulated Demo Room MuJoCo Static Import

## Goal

Test whether the most complex SceneSmith / Articraft demo scene can be loaded and rendered by MuJoCo.

Source scene:

```text
/home/users/dazhi.sun-labs/projects/scenesmith/outputs/2026-07-01/articulated_demo_room_v1/articulated_demo_room_v1.glb
```

## What Was Converted

The GLB scene was converted into separate OBJ mesh files, then referenced from a MuJoCo MJCF file.

Generated MuJoCo scene:

```text
/home/users/dazhi.sun-labs/projects/week5_note/pipeline/articulated_demo_mujoco/xml/articulated_demo_static.xml
```

Generated mesh folder:

```text
/home/users/dazhi.sun-labs/projects/week5_note/pipeline/articulated_demo_mujoco/assets/meshes/
```

## Result

MuJoCo successfully loaded the converted scene.

```text
nbody = 2
ngeom = 86
nmesh = 85
njnt = 0
nq = 0
```

The visual render confirms that the complex room geometry is present, including:

- room shell
- floor
- walls
- entry door geometry
- cabinet geometry
- microwave geometry
- static furniture

Preview outputs:

```text
outputs/articulated_demo_top.png
outputs/articulated_demo_diag.png
outputs/articulated_demo_side.png
outputs/articulated_demo_front.png
outputs/articulated_demo_static_turntable.gif
```

## Important Limitation

This is a static scene import.

The original viewer scene reports:

```text
3 articulated objects
8 joints
```

But after GLB-to-MJCF static conversion, MuJoCo reports:

```text
njnt = 0
nq = 0
```

That means the geometry can be displayed in MuJoCo, but the door, cabinet, and microwave joints have not yet been recreated as MuJoCo joints.

## Why This Matters

This test proves that the most complex existing demo scene can enter MuJoCo as static geometry.

The next step is not another scene import. The next step is to rebuild or convert the articulation layer:

- entry door hinge
- cabinet left and right hinges
- microwave door hinge
- microwave tray slider
- microwave turntable / knobs

Only after those joints exist in MJCF can MuJoCo simulate the same interactions that the custom viewer demonstrates.
