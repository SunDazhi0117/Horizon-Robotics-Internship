# Scene Versions Comparison

All three versions are **interactive scene development artifacts**, not a
robot task suite. They contain no robot controller, policy, planner, grasp
execution, or task benchmark.

## Summary

| Version | Purpose | Articulated objects | Joints | Viewer | Acceptance |
| --- | --- | ---: | ---: | --- | --- |
| `stable_scene_v1` | Freeze the complete static room | 0 | 0 | Ready | PASS |
| `stable_scene_v1_plus_microwave_v1` | Prove one URDF object can retain articulation | 1 | 5 | Ready | PASS |
| `articulated_demo_room_v1` | Scale the workflow to multiple Articraft assets | 3 | 8 | Ready | PASS |

## 1. `stable_scene_v1`

**Version purpose**

Create a reproducible baseline containing the SceneSmith room and all existing
static furniture in one complete scene.

**Scene contents**

- Floor.
- 4 walls.
- 4 windows.
- 7 static furniture assets: kitchen counter, office chair, bookcase, console,
  two shelving units, and study desk.

**Articulated objects:** 0

**Joint count:** 0

**Viewer status**

The complete GLB loads in the browser viewer and supports orbit, pan, and zoom.
There are no joint controls because this is the static baseline.

**Acceptance result**

- Furniture grounded: yes.
- Furniture inside room: yes.
- Lightweight furniture collision count: 0.
- Connected accessibility coverage: `0.99688`.
- Acceptance result: PASS.

**Best presentation focus**

Show the transition from separate room/furniture assets to one reproducible
complete GLB and BLEND scene.

**Robot tasks:** None.

## 2. `stable_scene_v1_plus_microwave_v1`

**Version purpose**

Prove that an existing Articraft URDF can be placed in the stable room while
preserving its articulated hierarchy and browser controls.

**Scene contents**

- All room and furniture content from `stable_scene_v1`.
- One Articraft microwave supported by the study desk.

**Articulated objects:** 1 microwave

**Joint count:** 5

- Door: revolute, range `0` to `1.75 rad`.
- Tray: prismatic, range `0` to `0.22 m`.
- Turntable: continuous.
- Upper knob: continuous.
- Lower knob: continuous.

**Viewer status**

Viewer status is `Ready`. Five controls are visible, transforms change, and
Reset restores the rest pose.

**Acceptance result**

- Closed state: PASS.
- Fully open door state: PASS.
- Valid door-then-tray sequence: PASS.
- New collisions on the accepted path: 0.
- Scene accessibility remains above the accepted threshold.
- Acceptance result: PASS.

**Best presentation focus**

Demonstrate that the result is more than a static GLB: URDF joint types, axes,
limits, hierarchy, and controls remain usable after scene integration.

**Robot tasks:** None.

## 3. `articulated_demo_room_v1`

This is the **multi-Articraft reading room scene**.

**Version purpose**

Scale the single-object integration to several URDF assets with independent
namespaces, browser controls, and multi-object validation.

**Scene contents**

- Separate static reading-room shell.
- Floor, 4 walls, 3 windows, and 1 entrance.
- 6 static furniture assets.
- Articraft entry door aligned with the entrance.
- Articraft double-door cabinet.
- Articraft microwave supported by the writing desk.

**Articulated objects:** 3

**Joint count:** 8

- Entry door: 1 revolute joint.
- Cabinet: 2 revolute joints.
- Microwave: 5 mixed joints.

**Viewer status**

Viewer status is `Ready`. Eight controls are visible, all eight transforms
change, and Reset restores all rest poses.

**Acceptance result**

- Sampled accepted poses: 23.
- New self-collisions: 0.
- Existing-furniture collisions: 0.
- Inter-asset collisions: 0.
- Room-bound violations: 0.
- Required operation regions reachable: 4/4.
- Acceptance result: PASS.

The connected free-cell diagnostic is `0.862861` because three narrow residual
pockets remain behind inflated perimeter furniture. Those pockets are recorded
but are not required operation regions.

**Best presentation focus**

Show that the pipeline scales from one URDF to multiple namespaced articulated
assets while preserving joint metadata, browser controls, and measurable
acceptance evidence.

**Robot tasks:** None.

## Scope Boundary

These versions demonstrate scene generation, scene assembly, articulation
preservation, browser interaction, and sampled lightweight validation. They do
not demonstrate autonomous robot task execution or full physics simulation.

