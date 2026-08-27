# Microwave Drake Validation

## Scope

This check uses the existing Articraft microwave URDF. It does not regenerate
the object, modify a stable scene, or introduce a robot. The purpose is to
separate what has been verified kinematically from what still needs work before
dynamic simulation.

Run:

```bash
cd week4_note
../scenesmith/.venv/bin/python scripts/validate_microwave_drake.py
```

Machine-readable output:

```text
reports/microwave_drake_validation.json
```

## Verified

- Drake parses the existing URDF.
- The model exposes five positions and five velocities.
- All five expected joints are present.
- The door is revolute with a range of `0` to `1.75 rad`.
- The tray is prismatic with a range of `0` to `0.22 m`.
- The turntable and two knobs are continuous revolute joints.
- Drake registers 47 collision geometries.
- Closed, half-open door, fully open door, and door-open tray states have no
  sampled penetrations.
- A combined state with all five controls moved has no sampled penetrations.

## Door And Tray Interlock

The deliberately invalid state that extends the tray while the door remains
closed produces collision contacts between the tray or turntable and the door.
This confirms that the browser behavior must open the door before extending
the tray. The interlock is part of correct operation, not merely a visual
animation preference.

## Dynamics Limitation

The source URDF contains no `inertial` blocks. A 0.25-second Drake gravity
simulation was attempted, but Drake correctly rejected it because the
turntable joint's internal mass matrix is not positive-definite.

Current result:

```text
KINEMATIC_PASS_DYNAMICS_BLOCKED
```

This is not a dynamic-simulation pass. Before Week 5 physics experiments, each
moving link needs physically reasonable mass, center of mass, and inertia.
After those values are added, the same script can be run with:

```bash
../scenesmith/.venv/bin/python \
  scripts/validate_microwave_drake.py \
  --require-dynamics
```
