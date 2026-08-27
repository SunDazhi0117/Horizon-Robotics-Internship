# Scripts

Week8 entry points and reusable extensions:

- `01_discover_microwave_articulation.py`: inspect the real microwave model.
- `articulation_discovery.py`: reusable geom-to-joint discovery.
- `target_approach.py`: target-relative base positioning plus staged,
  collision-checked target approach and retreat. `move_near_target` accepts a
  single pose, an ordered list of named candidate routes, or a polar search
  rule that generates candidate routes automatically. It also records each
  attempted route, route length, rejection reason, and selected candidate.
- `microwave_runtime.py`: bind aliases and create non-destructive derived model
  files needed for collision checking and reachability.
- `microwave_pose_variant.py`: create an isolated scene where the complete
  microwave is translated and rotated for position-generalization testing. It
  can also add a visible blocker at the preferred robot work pose.
- `run_microwave_open_close.py`: execute YAML, validate every state, and render
  fixed front and top-view videos. CLI options select a derived task XML and a
  separate output stem without changing the YAML or replacing the baseline.
- `run_articulated_hinge_task.py`: generic YAML-driven hinge-task runner used
  by the entry-door experiment. It performs execution, per-state validation,
  structured evaluation, and fixed front/top rendering without hard-coding a
  microwave or entry-door joint name.

These scripts import the Week7 task system rather than copying a complete Level
task script.

`follow_hinge_joint()` now also accepts the reusable
`orbit_base_with_hinge` option. It uses `planar_hinge_orbit_base()` to rotate a
mobile base around a vertical hinge while preserving backward compatibility
for configurations that provide a fixed `base_target`.
