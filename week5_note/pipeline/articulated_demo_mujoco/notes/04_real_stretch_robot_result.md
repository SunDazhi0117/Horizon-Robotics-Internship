# Real Stretch Robot Integration

## Goal

Replace the placeholder blue mobile base with a real MuJoCo robot model.

Robot source:

```text
week5_note/external/mujoco_menagerie/hello_robot_stretch/
```

Model:

```text
hello_robot_stretch/stretch.xml
```

## Standalone Stretch Test

Script:

```text
week5_note/pipeline/stretch_robot/scripts/run_stretch_standalone_demo.py
```

Result:

```text
nbody = 29
njnt = 19
nu = 8
nmesh = 67
```

Stretch actuators:

```text
forward
turn
lift
arm_extend
wrist_yaw
grip
head_pan
head_tilt
```

Standalone motion result:

```text
moved_distance_xy = 0.43 m
PASS
```

## Stretch In Generated Room

Generated combined scene:

```text
xml/articulated_demo_with_stretch.xml
```

This combines:

- generated room geometry;
- 8 reconstructed articulated-object joints;
- 8 room/object position actuators;
- real Hello Robot Stretch model;
- 8 Stretch actuators.

Load result:

```text
nbody = 36
njnt = 26
nq = 32
nu = 16
nmesh = 152
```

Stretch-in-room motion result:

```text
moved_distance_xy = 0.34 m
PASS
```

Outputs:

```text
outputs/stretch_room_start_top.png
outputs/stretch_room_final_top.png
outputs/stretch_room_final_diag.png
outputs/stretch_room_motion.gif
outputs/stretch_room_demo_summary.json
```

## Debug Note

The first combined version loaded Stretch but the base barely moved.

Cause:

```text
The custom transparent collision floor did not reproduce the wheel-ground behavior from the original Stretch demo.
```

Fix:

```text
Use a standard MuJoCo plane matching the Stretch demo floor configuration.
```

After the fix, Stretch moved correctly inside the generated room.

## What This Means

This is now beyond a placeholder robot.

We have verified:

- real robot MJCF can be downloaded from MuJoCo Menagerie;
- real robot model can load by itself;
- real robot model can be merged into the generated SceneSmith + Articraft room;
- robot actuators remain available after merging;
- robot can move inside the generated room.

## Still Not Completed

This is not yet a manipulation task.

Missing pieces:

- collision-aware navigation;
- reaching/grasping/contact interaction;
- robot opening the door or microwave;
- task planner or controller;
- task success validation caused by robot-object contact.

## Next Step

The next clean milestone is:

```text
Stretch navigates near the entry door or microwave without manipulating it yet.
```

After navigation works, the first manipulation task should be:

```text
Open entry door
```
