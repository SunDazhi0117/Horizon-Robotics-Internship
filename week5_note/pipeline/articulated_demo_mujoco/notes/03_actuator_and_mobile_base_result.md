# Actuator Control And Mobile Base Smoke Test

## Goal

Move beyond direct `qpos` visualization.

This step tests:

1. whether reconstructed joints can be controlled through MuJoCo actuators;
2. whether simple PASS / FAIL task validation can be computed from `data`;
3. whether a minimal mobile base can be loaded and moved inside the scene.

## Actuator Scene

Generated file:

```text
xml/articulated_demo_with_actuators.xml
```

Result:

```text
njnt = 8
nq = 8
nu = 8
```

The 8 actuators control:

```text
frame_to_door
left_hinge
right_hinge
body_to_front_door
body_to_sliding_tray
tray_to_turntable
body_to_upper_knob
body_to_lower_knob
```

## Actuator Validation

Script:

```text
scripts/run_actuator_demo.py
```

The script uses:

```text
data.ctrl
mujoco.mj_step
data.qpos
```

It validates the following simple tasks:

```text
open_entry_door
open_left_cabinet_door
open_right_cabinet_door
open_microwave_door
extend_microwave_tray
```

Result:

```text
PASS
```

Final key values:

```text
frame_to_door        = 1.1999989 rad
left_hinge           = 1.1999989 rad
right_hinge          = 1.1999989 rad
body_to_front_door   = 1.2499989 rad
body_to_sliding_tray = 0.2121827 m
```

Outputs:

```text
outputs/actuator_demo_start.png
outputs/actuator_demo_final.png
outputs/actuator_demo_motion.gif
outputs/actuator_demo_summary.json
```

## Mobile Base Smoke Test

Generated file:

```text
xml/articulated_demo_with_mobile_base.xml
```

This adds a minimal geometric mobile base with:

```text
base_x
base_y
base_yaw
```

and three position actuators:

```text
base_x_pos
base_y_pos
base_yaw_pos
```

Result:

```text
PASS
```

The base moved from:

```text
[2.6, 2.0, 0.16]
```

to:

```text
[3.4815, 2.4114, 0.16]
```

XY distance:

```text
0.97 m
```

Outputs:

```text
outputs/mobile_base_start.png
outputs/mobile_base_final.png
outputs/mobile_base_motion.gif
outputs/mobile_base_demo_summary.json
```

## Important Limitations

This is still not a full robot task.

Current limitations:

- the mobile base is a minimal geometric placeholder, not a real robot URDF;
- scene collision is simplified;
- the robot does not yet manipulate the articulated objects;
- no planner or policy is used;
- the articulated tasks are currently actuator-driven, not robot-contact-driven.

## Next Step

The next clean step is to replace the placeholder base with a real mobile robot URDF or MJCF model, then test navigation inside the same scene.
