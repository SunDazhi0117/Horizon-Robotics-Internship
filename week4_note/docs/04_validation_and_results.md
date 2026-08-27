# Validation and Results

## Stable Static Scene

The static room was frozen as `stable_scene_v1`.

| Measurement | Result |
| --- | --- |
| Floor | Present |
| Walls | 4 |
| Windows | 4 |
| Furniture assets | 7 |
| Furniture grounded | Yes |
| Furniture inside room | Yes |
| Lightweight furniture collisions | 0 |
| Accessibility coverage | 0.99688 |
| Acceptance threshold | 0.99 |
| Historical SceneSmith reachability | 1.00 |

The seven furniture assets include a kitchen counter, office chair, bookcase,
console, two shelving units, and a study desk.

## Articulated Microwave

The second stable version adds an existing Articraft microwave without
modifying the base version.

| Joint | Type | Axis | Range |
| --- | --- | --- | --- |
| Door | Revolute | `[0, 0, 1]` | `0` to `1.75 rad` |
| Tray | Prismatic | `[0, -1, 0]` | `0` to `0.22 m` |
| Turntable | Continuous | `[0, 0, 1]` | Continuous |
| Upper knob | Continuous | `[0, 1, 0]` | Continuous |
| Lower knob | Continuous | `[0, 1, 0]` | Continuous |

### Placement

- Support object: study desk.
- Base clearance: `0.000000 m`.
- Closed footprint inside support surface: yes.
- Door opens away from the wall and toward the room.
- Door range: `100.27 degrees`.

### Motion Sampling

The validation sampled:

- eight door poses from `0` to `1.75 rad`;
- five tray poses from `0` to `0.22 m`;
- the tray path with the door open to `1.50 rad`.

Validated normal path:

```text
open door to at least 1.50 rad -> extend tray
```

Results:

- unexpected self-collisions: 0;
- wall collisions: 0;
- furniture collisions: 0;
- robot passage affected: no.

Known invalid sequence:

```text
keep door closed -> extend tray beyond approximately 0.11 m
```

This sequence intersects the tray with the door and should be prevented by a
future joint interlock.

## Browser Test

The browser smoke test confirmed:

- HTTP response: 200;
- viewer status: `Ready`;
- GLB canvas: nonblank;
- joint control count: 5;
- door transform changes: yes;
- tray transform changes: yes;
- Reset restores the rest pose: yes;
- failed requests: 0.

## Version Integrity

Both stable versions have SHA-256 manifests. The base version was verified
before and after creating the microwave version, confirming that the original
files were not modified.

## Multi-Articulated Demo Room

The next iteration reused a separate static reading-room scene and combined:

- one Articraft entry door with 1 revolute joint;
- one Articraft double-door cabinet with 2 revolute joints;
- one Articraft microwave with 5 mixed joints.

| Measurement | Result |
| --- | --- |
| Articulated objects | 3 |
| Total joints | 8 |
| Sampled poses | 23 |
| New self-collisions | 0 |
| Existing-furniture collisions | 0 |
| Inter-asset collisions | 0 |
| Room-bound violations | 0 |
| Required interaction targets | 4/4 reachable |
| Browser controls | 8/8 changed |
| Browser reset | Pass |

The 2D occupancy diagnostic found three narrow residual pockets behind
perimeter furniture, giving a connected free-cell coverage of `0.862861`.
These pockets are not interaction targets. The entrance, central circulation,
microwave operating position, cabinet operating position, and reading area
remain connected.
