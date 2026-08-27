# Automatic Robot-Base Orbit Around a Hinge

## Why This Step Was Needed

The first accepted entry-door configuration reused the action framework, but
it still stored two entry-door-specific base endpoints:

    open base target  = [3.7643954907, 0.7499606856, -1.1046934942]
    close base target = [4.5221971039, 0.7321858629, -2.1046934942]

Those coordinates worked for one hinge position. Moving the door would require
calculating them again. This was therefore a remaining obstacle to stronger
position generalization.

## New Configuration Interface

The new configuration replaces both endpoints with:

    orbit_base_with_hinge: true

`follow_hinge_joint()` now reads the actual MuJoCo hinge anchor and world-space
axis. For a vertical hinge, it rotates the grasp-time robot base around the
anchor by the same signed angle as the door and updates the base yaw by that
angle.

For hinge position `p_h`, starting base position `p_b`, and joint change
`theta`, the planar position is:

    p_b(theta) = p_h + R(theta) * (p_b - p_h)

The implementation is isolated in `planar_hinge_orbit_base()`, so its geometry
can be tested without loading the full scene.

## Safety and Compatibility

The new option is disabled by default. Existing Week7 and microwave configs
continue using their previous behavior. The function rejects:

- simultaneous use of `base_target` and `orbit_base_with_hinge`;
- a missing or non-hinge joint;
- a hinge axis that is not nearly vertical.

All generated states still pass through the existing IK, joint-step, grasp,
visual-overlap, and forbidden-contact checks.

## Accepted Result

The automatic-orbit version completed the same entry-door task:

- 11 actions and 578 states;
- door opened from `0.0` to `1.0` rad and returned to `0.0` rad;
- 99 environment geoms checked per state;
- 0 visual-overlap failures;
- 0 forbidden target-contact failures;
- 0 grasp-loss failures;
- maximum adjacent arm-joint step: `0.0298841` rad;
- structured result: `PASS`.

Front and top-view keyframes were inspected. The base follows the hinge in the
correct direction, the gripper remains on the handle, and the door returns to
its closed pose.

## Evidence

- Config: `configs/entry_door_open_hold_close_auto_orbit.yaml`
- Front view: `assets/entry_door_open_hold_close_auto_orbit.gif`
- Top view: `assets/entry_door_open_hold_close_auto_orbit_top_view.gif`
- Summary: `results/entry_door_open_hold_close_auto_orbit_summary.json`
- Trajectory: `results/entry_door_open_hold_close_auto_orbit_trajectory.json`

## Current Boundary

This feature handles a planar mobile base following a near-vertical hinge. It
does not yet generate base motion for horizontal hinges, arbitrary 3D mobile
platforms, or force-controlled door dynamics.
