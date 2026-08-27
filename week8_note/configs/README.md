# Configs

`microwave_open_hold_close.yaml` is the accepted fixed-waypoint baseline.

`microwave_open_hold_close_target_relative.yaml` replaces its absolute base
waypoint with `move_near_target`. It stores a base offset and yaw relative to
the microwave handle frame, so translating or rotating the target updates the
computed world-space base goal.

Both configs select reusable actions and supply target aliases, grasp pose,
hinge angle, IK tolerances, and timing parameters.

`microwave_open_hold_close_candidate_fallback.yaml` provides two named base
candidates. The preferred candidate is tried first. The backup candidate adds
a target-relative detour waypoint and is selected automatically when the
preferred route fails collision validation.

`microwave_open_hold_close_auto_candidates.yaml` removes the per-candidate
offsets. It provides one polar search rule: stand distance, center angle,
ordered angle offsets, and detour distance. The runtime generates all named
candidates and target-relative detour points.

`entry_door_open_hold_close.yaml` applies the same reusable action vocabulary
to the room entry door. It supplies the entry-door target, hinge alias, grasp
transform, automatic base-search rule, and synchronized door-follow base arc.

`entry_door_open_hold_close_auto_orbit.yaml` removes the manually calculated
open and close base endpoints. Its two hinge-follow actions set
`orbit_base_with_hinge: true`, allowing the runtime to compute the base arc
from the live MuJoCo hinge anchor, axis, and angle.
