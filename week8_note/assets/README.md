# Assets

Accepted Week8 videos:

- `microwave_open_hold_close.gif`: fixed front view.
- `microwave_open_hold_close_top_view.gif`: fixed top view for overlap checks.

Both videos contain 201 frames and correspond to the accepted 401-state run.

Target-relative navigation variant:

- `microwave_open_hold_close_target_relative.gif`
- `microwave_open_hold_close_target_relative_top_view.gif`

These are stored separately from the baseline and also contain 201 frames.

Moved-object, same-Config validation:

- `microwave_pose_shifted_rotated_same_config.gif`
- `microwave_pose_shifted_rotated_same_config_top_view.gif`

Blocked preferred pose with candidate-route fallback:

- `microwave_candidate_fallback_blocked_preferred.gif`
- `microwave_candidate_fallback_blocked_preferred_top_view.gif`

The red cylinder marks the blocked preferred base pose. The top view is the
primary visual evidence that the selected backup route goes around it.

Automatically generated candidates:

- `microwave_auto_candidates_blocked_preferred.gif`
- `microwave_auto_candidates_blocked_preferred_top_view.gif`

The visible motion is intentionally similar to the accepted manual-candidate
run. The difference is that `auto_02` and its detour were generated from a
polar search rule rather than stored as explicit offsets.

Cross-object entry-door task:

- `entry_door_open_hold_close_generalized.gif`: fixed indoor front view.
- `entry_door_open_hold_close_generalized_top_view.gif`: fixed top view used
  to inspect the base arc, door motion, and environmental clearance.

Both accepted GIFs contain 146 frames.

Automatic hinge-orbit extension:

- `entry_door_open_hold_close_auto_orbit.gif`
- `entry_door_open_hold_close_auto_orbit_top_view.gif`

These videos repeat the accepted task after removing the manually calculated
base endpoints from the configuration. Both contain 146 frames.
