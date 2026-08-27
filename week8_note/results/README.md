# Results

Accepted Week8 results:

- `microwave_articulation_discovery.json`: discovered body, joint, axis, range,
  and target position.
- `microwave_open_hold_close_trajectory.json`: all 401 commanded states.
- `microwave_open_hold_close_summary.json`: PASS result and validation counts.

The task was marked successful only after numerical checks and two-view visual
inspection passed.

Target-relative extension results:

- `microwave_open_hold_close_target_relative_trajectory.json`: 401 states.
- `microwave_open_hold_close_target_relative_summary.json`: PASS, with zero
  overlap, forbidden-contact, and grasp-loss failures.

Moved-object validation:

- `microwave_pose_shifted_rotated_scene.json`: recorded translation, rotation,
  center, and transformed component counts.
- `microwave_pose_shifted_rotated_same_config_trajectory.json`: 401 states
  generated from the unchanged target-relative Config.
- `microwave_pose_shifted_rotated_same_config_summary.json`: end-to-end PASS.

Candidate-route fallback:

- `microwave_preferred_base_blocked_scene.json`: obstacle placement and both
  target-relative base offsets.
- `microwave_candidate_fallback_blocked_preferred_trajectory.json`: 504 states
  using the selected `backup_right` route.
- `microwave_candidate_fallback_blocked_preferred_summary.json`: complete
  open-close task PASS with zero overlap, forbidden-contact, and grasp-loss
  failures.

Automatic candidate generation:

- `microwave_auto_candidates_blocked_preferred_trajectory.json`: 504 states
  produced after selecting generated candidate `auto_02`.
- `microwave_auto_candidates_blocked_preferred_summary.json`: end-to-end PASS
  using a Config with no manually listed candidate offsets. Its
`base_candidate_selection` field contains the complete decision trace.

Entry-door cross-object generalization:

- `entry_door_open_hold_close_generalized_trajectory.json`: all 578 states.
- `entry_door_open_hold_close_generalized_summary.json`: end-to-end PASS after
  opening to `1.0 rad` and returning to `0.0 rad`, with zero overlap,
  forbidden-contact, and grasp-loss failures.

Automatic hinge-orbit extension:

- `entry_door_open_hold_close_auto_orbit_trajectory.json`: all 578 states.
- `entry_door_open_hold_close_auto_orbit_summary.json`: PASS using a Config
  that contains no manually calculated open or close base endpoint.
