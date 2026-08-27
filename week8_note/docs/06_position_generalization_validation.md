# End-to-End Target-Pose Generalization Validation

## Validation Question

This experiment does not merely rerun the original scene. It asks whether the same task can be completed after translating and rotating the entire microwave, without modifying either the Python action functions or the target-relative YAML.

## Scene Transformation

The test script creates an independent scene from the Week 8 derived XML and does not modify the baseline scene. Around the automatically calculated microwave center, it applies the following transform to 11 static shell meshes and 5 articulated bodies:

    translation: [+0.15, -0.05, 0.0] m
    yaw rotation: +10 degrees

The moved articulated parts include the door, tray, turntable, and two knobs. MuJoCo compiles the derived XML immediately after it is saved, preventing partial transforms or invalid model output.

## Configuration Reuse

The configuration is unchanged. Both target poses use:

    configs/microwave_open_hold_close_target_relative.yaml

The file still contains only the handle name, target-local base offset, yaw offset, and subsequent action parameters.

## Automatically Computed Work Poses

    original base goal: [3.52167, 3.33753, 0.05]
    moved-object goal:  [3.83123890, 3.20665270, 0.22453293]

The robot no longer travels to the old world coordinate. It recomputes its work position and heading from the moved handle pose.

## Complete-Task Result

- Result: PASS
- States: 401
- Actions: 11
- Maximum microwave-hinge angle: `1.0 rad`
- Final microwave-hinge angle: `0.0 rad`
- Environment visual-overlap failures: 0
- Forbidden target-contact failures: 0
- Grasp-loss failures: 0
- Front-view video frames: 201
- Top-view video frames: 201

Both videos were inspected manually. At the new pose, the robot navigates, approaches, grasps, opens, holds, closes, releases, and retreats without the arm passing through the microwave body.

## Conclusion and Boundary

This experiment validates a first version of pose generalization using the same reusable actions, the same YAML, and a different target pose.

It is not global motion planning. `move_near_target` computes a relative work pose and validates the generated route, but it does not search many complex paths around obstacles. The base offset is also still supplied by the configuration.
