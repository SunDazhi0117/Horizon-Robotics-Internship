# 04. Minimal MuJoCo Hinge Door Demo

## Goal

Build a small MuJoCo example that uses the concepts from the tutorial:

```text
body
geom
hinge joint
actuator
data.ctrl
mj_step
qpos
PASS / FAIL validation
```

This is a preparation step for future tasks such as:

- robot opens a room door
- robot opens a cabinet
- robot opens a microwave door

## Files

Demo folder:

```text
/home/users/dazhi.sun-labs/projects/week5_note/experiments/hinge_door
```

Important files:

```text
hinge_door.xml
run_hinge_door.py
hinge_door_opening.gif
hinge_door_result.json
README.md
```

## What The Model Contains

The MJCF scene contains:

- floor
- simple wall / door frame
- one door body
- one hinge joint named `door_hinge`
- one position actuator named `door_position_motor`

The hinge joint represents the same basic mechanism as:

```text
room door hinge
cabinet door hinge
microwave door hinge
```

## Validation Result

The script controls the door actuator and checks the final hinge angle.

Success condition:

```text
door_hinge qpos > 1.2 rad
```

Result:

```text
final angle = 1.409 rad
threshold   = 1.200 rad
result      = PASS
```

Model statistics:

```text
bodies    = 2
joints    = 1
geoms     = 7
actuators = 1
```

## Important Debugging Lesson

The first version failed.

Two issues appeared:

1. A visual hinge post was colliding with the door panel and blocking the hinge.
2. The XML needed `compiler angle="radian"` so that joint ranges such as `1.57`
   are interpreted as radians instead of degrees.

This is useful because future SceneSmith / Articraft conversion may have similar
issues:

- collision geometry can block articulation;
- joint range units must be checked;
- visual geometry and collision geometry should be treated separately.

## Why This Matters

This demo proves the smallest articulated-object pipeline:

```text
MJCF object
-> hinge joint
-> actuator control
-> mj_step simulation
-> qpos task validation
-> rendered GIF
```

The same structure can later be reused for:

```text
Articraft microwave door
Articraft cabinet door
SceneSmith room door
```
