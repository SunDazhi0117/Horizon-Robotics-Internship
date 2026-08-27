# 05. Penetration, Contact, and Validation

## 1. Apply One State to MuJoCo

Source: `run_level_5_sequential_open_both_doors.py:182-201`

A task state is written into the corresponding qpos addresses:

```python
data.qpos[base_qpos_adr : base_qpos_adr + 3] = state["base"]
data.qpos[arm_qpos_indices] = state["qpos"]
data.qpos[left_hinge_adr] = state["left_hinge"]
data.qpos[right_hinge_adr] = state["right_hinge"]
mujoco.mj_forward(model, data)
```

`mj_forward` recomputes body positions, geom positions, and contacts for the specified state. It does not advance simulation time like `mj_step`.

## 2. Why Direct qpos Assignment Can Penetrate Objects

Direct assignment places the robot at a requested state. MuJoCo does not automatically reject a state merely because two meshes overlap. If code jumps over unchecked intermediate states, an object can pass through a wall or cabinet.

The prevention strategy is:

```text
dense trajectory
-> write one state
-> mj_forward
-> inspect geometry and contacts
-> reject the trajectory on failure
```

## 3. IDs and Contact Pairs

MuJoCo represents geoms with integer IDs. A contact stores two IDs:

```python
for index in range(data.ncon):
    contact = data.contact[index]
    geom1 = int(contact.geom1)
    geom2 = int(contact.geom2)
```

Sets make membership checks convenient:

```python
robot_geoms = {1, 2, 3}
environment_geoms = {20, 21, 22}
```

Code can then ask whether one contact geom belongs to the robot and the other belongs to the environment.

## 4. Visual Overlap and OBB Checks

Contact data alone may miss some visual penetrations when imported meshes have incomplete collision geometry. The project therefore also compares oriented bounding boxes (OBBs).

An OBB contains:

- a center;
- three local axes;
- a half-size along each axis.

The separating-axis test asks whether any axis separates two boxes. If one exists, the boxes do not overlap. If none exists, they overlap according to this approximation.

Source: `level_validation_helpers.py:101-162`.

OBB checks are useful but conservative. They can report overlap even when irregular meshes do not physically touch.

## 5. Handle Contact Rules

During grasping, finger-to-handle contact is expected. Contact between the handle and the wrist or arm is not.

A phase-specific rule can express:

```python
if active_handle is not None:
    require_both_finger_contacts(active_handle)
    reject_non_finger_handle_contacts(active_handle)
```

This distinction prevents a trajectory from passing simply because some robot part touches the target.

## 6. What validate_state Checks

Source: `run_level_5_sequential_open_both_doors.py:263-335`

A complete state validator checks combinations of:

- state values are finite;
- state write/read consistency;
- base remains fixed during fixed-base phases;
- maximum arm-joint change from the previous state;
- robot/environment visual overlap;
- forbidden physical contacts;
- expected finger/handle contacts;
- hand-to-handle distance;
- door angles change only during permitted phases.

It returns structured data so the summary can report the exact phase, state, and failed condition.

## 7. Main Causes of Penetration Found in This Project

1. Too few interpolated states.
2. Straight interpolation between safe endpoints crosses an obstacle.
3. IK reaches the target without considering the environment.
4. Imported visual and collision meshes do not match.
5. A check covers only the target cabinet and misses nearby furniture.
6. The gripper approach comes through the center of the handle instead of from the side.
7. Door motion and arm motion are not synchronized.

The fixes included denser sampling, safer staging waypoints, full-environment checks, target-specific contact rules, top/side cameras, and synchronized handle following.

## 8. Remaining Limits

- OBBs approximate complex meshes.
- Very thin geometry can still require specialized checks.
- Kinematic validation does not prove dynamic stability.
- Zero forbidden contacts in sampled states does not prove safety at every continuous instant.
- A valid trajectory in one scene may fail after object randomization.

## 9. Self-Check

1. How does `mj_forward` differ from `mj_step`?
2. Why is endpoint-only checking insufficient?
3. Why distinguish finger contact from arm contact?
4. Why combine MuJoCo contacts with visual-overlap checks?

Answers: `mj_forward` recomputes one state without advancing time; intermediate motion may collide; only fingers should grasp the handle; imported collision geometry may not capture every visible penetration.
