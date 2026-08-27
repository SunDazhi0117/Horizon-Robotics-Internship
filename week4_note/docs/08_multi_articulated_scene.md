# Multi-Articulated Scene

## Goal

The first integrated scene proved that one Articraft microwave could preserve
its joints after being placed in a SceneSmith room. The next step was to test
whether the same workflow could manage several articulated assets at once.

The new `articulated_demo_room_v1` reuses a separate static reading-room shell
and adds:

- an entry door aligned with the existing south-wall opening;
- a double-door cabinet placed against the east wall;
- a microwave supported by the writing desk.

No Articraft asset was regenerated for this assembly.

## Articulation

| Object | Joint | Type | Range |
| --- | --- | --- | --- |
| Entry door | `frame_to_door` | Revolute | `0` to `1.5708 rad` |
| Cabinet | `left_hinge` | Revolute | `0` to `1.5708 rad` |
| Cabinet | `right_hinge` | Revolute | `0` to `1.5708 rad` |
| Microwave | Door | Revolute | `0` to `1.75 rad` |
| Microwave | Tray | Prismatic | `0` to `0.22 m` |
| Microwave | Turntable | Continuous | Continuous |
| Microwave | Upper knob | Continuous | Continuous |
| Microwave | Lower knob | Continuous | Continuous |

The Blender and GLB hierarchies use per-asset namespaces so links and joints
from different URDF files cannot overwrite one another.

## Layout

![All articulated objects closed](../assets/multi_articulated_scene_closed.png)

![All articulated objects open](../assets/multi_articulated_scene_open.png)

![Entry door open](../assets/entry_door_open.png)

![Double-door cabinet open](../assets/double_door_cabinet_open.png)

[Watch the articulated scene MP4 demo](../assets/week4_articulated_scene_demo.mp4)

The entry door opens inward. The cabinet doors open toward the room without
touching the wall, desk, or microwave. The microwave remains seated on the
writing desk.

## Validation

- articulated objects: 3;
- preserved joints: 8;
- sampled valid poses: 23;
- new self-collisions: 0;
- collisions with existing furniture: 0;
- collisions between articulated assets: 0;
- room-bound violations: 0;
- required interaction positions reachable: 4/4;
- browser controls: 8;
- browser status: `Ready`;
- Reset restores all rest poses.

The connected free-cell diagnostic is `0.862861` because inflated perimeter
furniture creates three narrow residual pockets against the walls. These
pockets are recorded but are not required operating areas.

## Known Constraint

The entry and cabinet doors can use their validated full ranges independently.
The microwave still requires a sequence constraint:

```text
open microwave door to at least 1.50 rad -> extend tray
```

The current Viewer enforces this interlock. The tray remains disabled until the
door reaches `1.50 rad`, and closing the door retracts an extended tray first.
