# Task 1: Stretch Navigate To Cabinet

## Goal

Create the first clear robot task inside the generated SceneSmith + Articraft MuJoCo room.

This task does not manipulate the cabinet yet. It only tests whether the real Stretch robot can move from a start pose to a target region in front of the double-door cabinet.

## Scene

Task XML:

```text
xml/articulated_demo_stretch_to_cabinet.xml
```

Base scene:

```text
xml/articulated_demo_with_stretch.xml
```

## Task Definition

Task name:

```text
stretch_navigate_to_cabinet_front
```

Initial robot position:

```text
[3.35, 2.95]
```

Target region:

```text
[4.45, 2.95]
```

Success condition:

```text
distance(robot_base_xy, target_xy) <= 0.35 m
```

Control method:

```text
Stretch forward actuator + mj_step
```

This is still a simple scripted controller, not a planner.

## Result

Final robot position:

```text
[4.1001, 2.9518]
```

Final distance to target:

```text
0.3499 m
```

Elapsed simulation time:

```text
5.59 s
```

Result:

```text
PASS
```

## Outputs

```text
outputs/navigate_cabinet_start_top.png
outputs/navigate_cabinet_start_diag.png
outputs/navigate_cabinet_final_top.png
outputs/navigate_cabinet_final_diag.png
outputs/navigate_cabinet_motion.gif
outputs/navigate_cabinet_summary.json
```

## What This Proves

This task proves:

- Stretch is loaded in the generated room;
- Stretch can be initialized at a controlled start pose;
- Stretch can move toward a semantic target region;
- the task can be evaluated numerically with PASS / FAIL.

## What This Does Not Prove Yet

This is not yet:

- collision-aware navigation;
- path planning;
- manipulation;
- cabinet opening;
- contact-rich robot-object interaction.

## Next Step

The next task should be:

```text
Stretch Navigate To Microwave
```

After that, the first manipulation task can be:

```text
Open cabinet door
```
