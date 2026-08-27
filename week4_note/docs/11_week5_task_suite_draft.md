# Week 5–8 Task Suite Draft

## Status and Scope

**Future plan only. Nothing in this document has been implemented.**

Week 4 produced interactive scenes and human-operated browser controls. Week
5–8 may introduce a robot model, controller, task state, and evaluation logic.
The following tasks define possible interfaces and success conditions without
claiming robot control, grasping, planning, or physics results.

## Task 1: Open the Microwave Door

**Task name**

`open_microwave_door`

**Initial state**

- Microwave is supported by the desk.
- Microwave door joint is at `0 rad`.
- Tray is fully retracted.
- Future robot starts at a valid microwave approach position.

**Goal state**

Microwave door reaches a target angle between `1.50` and `1.75 rad`.

**Success condition**

- Door joint is within the target tolerance.
- Microwave body remains on its support.
- No new collision is reported.
- The tray remains retracted during door opening.

**Possible failure cases**

- Wrong handle or panel is selected.
- Joint is moved in the wrong direction.
- Door stops before the target angle.
- End effector loses contact.
- Robot or door collides with the desk, wall, or another object.

**Required scene version**

`stable_scene_v1_plus_microwave_v1` or
`articulated_demo_room_v1`.

**Why suitable for Week 5–8**

This is a bounded single-revolute-joint task with a clear visual target and
measurable success condition.

## Task 2: Extend the Microwave Tray

**Task name**

`extend_microwave_tray`

**Initial state**

- Microwave door is already open to at least `1.50 rad`.
- Tray is at `0 m`.
- Microwave remains supported by the desk.

**Goal state**

Tray reaches an extension between `0.20` and `0.22 m`.

**Success condition**

- Door remains at or above the safe angle.
- Tray reaches the target extension tolerance.
- No tray-door, desk, or robot collision occurs.

**Possible failure cases**

- Tray is pulled while the door is insufficiently open.
- The wrong interior part is selected.
- Tray exceeds its upper limit.
- Tray intersects the door.
- Robot loses contact or blocks the door.

**Required scene version**

`stable_scene_v1_plus_microwave_v1` or
`articulated_demo_room_v1`.

**Why suitable for Week 5–8**

This introduces a prismatic joint and an explicit cross-joint precondition. It
is a natural test for task state and safety interlocks.

## Task 3: Open the Double-Door Cabinet

**Task name**

`open_double_door_cabinet`

**Initial state**

- Both cabinet hinges are at `0 rad`.
- Cabinet is grounded against the east wall.
- Future robot starts at the cabinet operating position.

**Goal state**

Both cabinet doors reach a specified open angle, for example `1.20 rad`.

**Success condition**

- Left and right hinges both reach target tolerance.
- Cabinet frame remains fixed.
- Neither door collides with the wall, furniture, robot, or the other door.

**Possible failure cases**

- Only one door opens.
- Both doors are assigned the same rotation direction.
- A door collides with the robot while switching handles.
- Cabinet shifts because support constraints are missing.

**Required scene version**

`articulated_demo_room_v1`.

**Why suitable for Week 5–8**

The task requires two related revolute joints and tests sequential versus
coordinated interaction.

## Task 4: Open the Entry Door

**Task name**

`open_entry_door`

**Initial state**

- Entry door is closed at `0 rad`.
- Door frame is aligned with the room entrance.
- Future robot starts on a reachable approach side.

**Goal state**

Entry door reaches an angle that clears the passage, for example at least
`1.20 rad`.

**Success condition**

- Door reaches the target angle.
- The entrance passage is not blocked by the robot.
- Door, frame, walls, and robot remain collision-free under the future physics
  check.

**Possible failure cases**

- Robot approaches from the wrong swing side.
- Door pushes into the robot.
- Door opens in the wrong direction.
- Robot opens the door but blocks its own passage.

**Required scene version**

`articulated_demo_room_v1`.

**Why suitable for Week 5–8**

The task connects articulation control with navigation-side reasoning and
passage clearance.

## Task 5: Multi-Step Access and Appliance Interaction

**Task name**

`enter_room_and_access_microwave`

**Initial state**

- Entry door is closed.
- Microwave door is closed.
- Microwave tray is retracted.
- Cabinet doors are closed.
- Future robot starts outside or immediately before the entrance.

**Goal state**

1. Open the entry door.
2. Move to the microwave operating position.
3. Open the microwave door to at least `1.50 rad`.
4. Extend the tray to the target position.

**Success condition**

- Every step reaches its joint and navigation tolerance.
- Preconditions are respected.
- No accepted state exceeds URDF limits.
- No collision or loss of object support occurs in the future physics
  evaluation.
- Final tray extension is achieved with the microwave door safely open.

**Possible failure cases**

- Navigation fails after opening the entry door.
- Robot blocks the door swing or passage.
- Microwave tray is attempted before the door reaches the safe angle.
- State is lost between subtasks.
- Planning succeeds geometrically but fails under dynamics or contact.

**Required scene version**

`articulated_demo_room_v1`.

**Why suitable for Week 5–8**

This combines navigation, sequential articulation, preconditions, and
state-based evaluation. It should be attempted only after the single-object
tasks are stable.

## Proposed Progression

1. Define robot and controller interfaces.
2. Implement one single-joint task.
3. Add physics-based collision and contact checks.
4. Add the microwave door-tray precondition.
5. Add two-joint cabinet interaction.
6. Attempt the multi-step task last.

