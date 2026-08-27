# 04. Inverse Kinematics and Handle Following

## 1. What Inverse Kinematics Solves

Forward kinematics asks: given seven joint angles, where is the hand?

Inverse kinematics (IK) asks: given a desired hand position and orientation, which seven joint angles place the hand there?

```text
desired hand pose
-> numerical IK solver
-> seven Panda joint angles
```

There may be several valid answers or no valid answer because of joint limits, obstacles, or reach limits.

## 2. Typical solve_arm_pose Inputs

Source: `run_level_5_sequential_open_both_doors.py:342-406`

The solver needs:

- `target_position`: desired hand x, y, z;
- `target_rotation`: desired hand orientation;
- `seed`: the initial guess for seven joint angles;
- joint lower and upper limits;
- the MuJoCo model and data used for forward kinematics.

`qpos` is an array of joint positions. It is not one angle. Panda uses seven arm values, and the complete model qpos also includes base, gripper, and object joints.

## 3. The Error Function

A numerical solver repeatedly tests candidate joint angles. For each candidate it:

1. writes the candidate angles into `data.qpos`;
2. calls `mj_forward`;
3. reads the resulting hand position and rotation;
4. compares them with the target pose;
5. returns an error vector.

Conceptually:

```python
def residual(candidate_qpos):
    current_position, current_rotation = forward_kinematics(candidate_qpos)
    position_error = current_position - target_position
    rotation_error = rotation_difference(current_rotation, target_rotation)
    return np.concatenate([position_error, rotation_error])
```

`np.concatenate` joins the three position errors and three rotation errors into one vector. The optimizer tries to make every value close to zero.

## 4. Numerical Optimization

The project uses a least-squares solver conceptually like:

```python
result = least_squares(
    residual,
    x0=seed,
    bounds=(lower_limits, upper_limits),
)
```

- `residual` tells the optimizer how wrong a candidate is.
- `x0` is the initial guess.
- `bounds` enforce joint limits.
- `result.x` contains the best joint angles found.
- `result.success` reports whether optimization converged.

The solver tries answers; it does not understand doors or grasping semantically.

## 5. Following a Moving Door Handle

The hand must move on an arc as the hinged door rotates. Keeping the arm qpos fixed would cause the handle to move away.

The script first records the hand pose relative to the door:

```text
hand pose in world
-> convert into door-local coordinates
-> save relative hand pose
```

For each new hinge angle:

1. update the door angle;
2. call `mj_forward` to update the door world pose;
3. transform the saved door-local hand pose back into world coordinates;
4. solve IK for that new hand pose;
5. use the previous solution as the next seed;
6. validate grasp and collision state.

Conceptually:

```python
previous = grasp_qpos.copy()
for door_angle in opening_angles:
    set_door_angle(door_angle)
    target_position, target_rotation = door_local_pose_to_world()
    current = solve_arm_pose(target_position, target_rotation, seed=previous)
    previous = current.copy()
```

## 6. Why the Previous Frame Is the Seed

Neighboring door angles require neighboring hand poses. Starting IK from the previous joint solution encourages a continuous branch and reduces sudden arm flips.

It does not guarantee continuity. The result still checks the maximum adjacent joint step.

## 7. Common IK Failure Causes

- The target is outside the robot workspace.
- Required orientation is impossible near a joint limit.
- The seed leads to a poor local solution.
- The solution reaches the pose but crosses an obstacle.
- Adjacent IK solutions lie on different branches and create a jump.

IK solves pose geometry, not collision avoidance. Every generated pose still requires validation.

## 8. Self-Check

1. What is the difference between forward and inverse kinematics?
2. Why does the solver need a seed?
3. Why store the hand pose relative to the door?
4. Does a successful IK result prove that the motion is collision-free?

Answers: FK maps joints to hand pose; IK maps desired hand pose to joints; a seed guides the numerical solution; the relative pose lets the hand follow door motion; IK success alone does not prove safety.
