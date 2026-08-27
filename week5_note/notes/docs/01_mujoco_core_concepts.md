# 01. MuJoCo Core Concepts

This note explains the MuJoCo tutorial concepts that are most useful for our
current Week5 goal:

```text
learn MuJoCo
-> load a mobile robot
-> drive it in a simple environment
-> later import SceneSmith / Articraft assets
-> manipulate hinged objects
```

## Must Understand

### 1. `mjModel` vs `mjData`

MuJoCo separates the model into two main Python objects:

```python
model = mujoco.MjModel.from_xml_string(xml)
data = mujoco.MjData(model)
```

`mjModel` is the static description.

It stores things that usually do not change during simulation:

- body names
- geom names
- geom colors
- geom sizes
- joint types
- joint limits
- mass and inertia
- timestep
- actuator definitions

Example:

```python
model.ngeom
model.geom("green_sphere").rgba
model.joint("door_hinge").range
```

`mjData` is the current simulation state.

It stores things that change every timestep:

- current simulation time
- joint positions
- joint velocities
- body poses
- geom world positions
- contacts
- actuator controls

Example:

```python
data.time
data.qpos
data.qvel
data.geom("green_sphere").xpos
data.ctrl
```

Project meaning:

```text
model tells us what exists.
data tells us what is happening now.
```

For a future microwave task:

- the microwave door joint limit belongs to `model`;
- the current microwave door angle belongs to `data`;
- task success is checked from `data`.

### 2. MJCF: `body`, `geom`, `joint`, `actuator`

MJCF is MuJoCo's native XML model format.

#### `body`

A `body` is a rigid object or a rigid part in a hierarchy.

Example:

```xml
<body name="door" pos="0 0 1">
  ...
</body>
```

For our project:

- a room wall can be a static body;
- a microwave body can be one body;
- a microwave door can be another body;
- a robot link can be a body.

#### `geom`

A `geom` describes geometry.

It can be used for:

- visual appearance
- collision
- mass/inertia estimation

Example:

```xml
<geom name="door_panel" type="box" size="0.02 0.4 0.8" rgba="0.6 0.4 0.2 1"/>
```

Important attributes:

- `type`: box, sphere, cylinder, capsule, mesh, plane
- `size`: dimensions
- `pos`: local position
- `rgba`: color
- `contype` / `conaffinity`: collision matching

For our project:

```text
visual mesh can look nice,
collision geom should usually be simpler.
```

#### `joint`

A `joint` gives a body degrees of freedom.

Without a joint, a body is fixed relative to its parent.

Common joint types:

| Joint type | Meaning | Project example |
| --- | --- | --- |
| `hinge` | rotates around one axis | door, cabinet door, microwave door |
| `slide` | moves along one axis | drawer, microwave tray |
| `free` / `freejoint` | 6-DoF floating body | falling object, mobile base if not constrained |

Example:

```xml
<joint name="door_hinge" type="hinge" axis="0 0 1" range="0 1.57"/>
```

This means:

```text
the door can rotate around the z axis from 0 to 1.57 radians.
```

#### `actuator`

An `actuator` is how we control a joint.

Example:

```xml
<actuator>
  <motor name="door_motor" joint="door_hinge" gear="1"/>
</actuator>
```

Then Python can control it with:

```python
data.ctrl[0] = 0.5
```

For our project:

- robot wheels need actuators;
- robot arm joints need actuators;
- for early tests, a door hinge can also have an actuator.

### 3. `qpos`, `qvel`, `ctrl`

These are the most important runtime arrays.

#### `qpos`

`qpos` means generalized positions.

For a hinge joint, `qpos` is the joint angle.

For a slide joint, `qpos` is the joint displacement.

For a free joint, `qpos` contains position plus orientation.

Example:

```python
data.joint("door_hinge").qpos
```

Project meaning:

```text
microwave door open angle = qpos of the microwave door hinge
```

#### `qvel`

`qvel` means generalized velocities.

For a hinge joint, it is angular velocity.

Example:

```python
data.joint("door_hinge").qvel
```

Project meaning:

```text
qvel tells us whether a door is still moving or has stopped.
```

#### `ctrl`

`ctrl` is the actuator control input.

Example:

```python
data.ctrl[0] = 1.0
```

The meaning depends on the actuator type.

For our future robot:

- wheel velocity commands may go into `ctrl`;
- arm joint commands may go into `ctrl`;
- gripper open/close commands may go into `ctrl`.

### 4. `mj_step`

`mj_step` advances the simulation.

Example:

```python
while data.time < 5.0:
    data.ctrl[0] = 1.0
    mujoco.mj_step(model, data)
```

Every call updates:

- time
- positions
- velocities
- contacts
- forces
- derived body/geom poses

Project meaning:

```text
robot task execution = repeatedly set ctrl and call mj_step.
```

### 5. Renderer And Saving Videos

The renderer turns the current MuJoCo state into pixels.

Example:

```python
with mujoco.Renderer(model) as renderer:
    renderer.update_scene(data)
    pixels = renderer.render()
```

To save or show a video, render frames during simulation:

```python
frames = []
while data.time < duration:
    mujoco.mj_step(model, data)
    if len(frames) < data.time * framerate:
        renderer.update_scene(data)
        frames.append(renderer.render())
```

Important point:

```text
simulation timestep can be much faster than video framerate.
```

Example:

- simulation timestep: 0.002 s, about 500 Hz
- video framerate: 30 or 60 fps

So we do not need to render every physics step.

Project meaning:

```text
use videos to show the robot approaching or opening an object.
use data logs to prove whether the task succeeded.
```

### 6. Hinge Joint For Doors, Cabinets, And Microwaves

A hinge joint is the key concept for articulated household objects.

Example:

```xml
<body name="microwave_door">
  <joint name="microwave_door_hinge" type="hinge" axis="0 0 1" range="0 1.75"/>
  <geom name="door_panel" type="box" size="0.02 0.3 0.25"/>
</body>
```

This says:

```text
the microwave door is a body.
the door rotates around one hinge axis.
the valid open range is 0 to 1.75 radians.
```

Task success can be simple:

```python
door_angle = data.joint("microwave_door_hinge").qpos[0]
success = door_angle > 1.2
```

Project mapping:

| Object | MuJoCo joint type |
| --- | --- |
| room door | hinge |
| cabinet door | hinge |
| microwave door | hinge |
| drawer | slide |
| microwave tray | slide |
| rotating knob | hinge |

### 7. Reading `data` For Task Success

For robot tasks, the final answer should not only be visual.

We need a script that says PASS or FAIL.

Possible checks:

```python
door_angle = data.joint("door_hinge").qpos[0]
robot_x = data.qpos[0]
num_contacts = data.ncon
```

Examples:

```text
Open microwave:
PASS if microwave_door_angle > 1.2 rad

Open cabinet:
PASS if left_cabinet_door_angle > 1.0 rad

Reach object:
PASS if end-effector is within 5 cm of handle

Avoid collision:
PASS if no forbidden contact happens
```

This is the bridge from "nice demo" to "robot task".

## Can Learn Later

These concepts appeared in the tutorial, but they are not the first priority.

### RK4 Integrator

RK4 is a numerical integration method.

It can be more accurate than the default Euler integrator for some dynamics.

For now:

```text
know it exists.
do not spend time tuning it yet.
```

Current priority:

```text
make simple scenes load and move correctly.
```

### Chaotic Pendulum

The chaotic pendulum example shows that small changes in initial state can create
large differences later.

It is useful for learning physics simulation, but it is not directly needed for
our door/microwave task.

For now:

```text
understand that simulation can be sensitive.
skip the math details.
```

### Energy Conservation

Energy plots are useful for checking physics accuracy.

For our current project, task-level checks matter more:

- Did the door open?
- Did the robot collide?
- Did the object stay stable?

Energy analysis can wait.

### Quaternion Details

A quaternion is a 4-number representation of 3D rotation.

You will see it in free-joint `qpos`.

For now:

```text
know that free body orientation uses 4 numbers.
do not manually derive quaternion math yet.
```

For most early tasks, hinge joint angles are easier and more important.

### MuJoCo C Header Files

The tutorial mentions `mjmodel.h`.

This is useful if you need every low-level field definition.

For now:

```text
use Python named access first:
model.geom("name")
data.joint("name")
```

Only inspect header files when Python docs or examples are not enough.

### Advanced Contact Solver Parameters

Examples:

- `solimp`
- `solref`
- contact solver tuning

These affect how contacts behave.

For now:

```text
use defaults.
learn contact detection first.
```

Later, if objects jitter, bounce strangely, or pass through each other, then tune
contact parameters.

### EGL / Colab GPU Rendering

The tutorial configures EGL for GPU rendering in Colab.

That is mostly environment setup.

For our local project:

```text
do not treat EGL as MuJoCo physics knowledge.
```

It matters only if rendering fails or runs too slowly.

## Minimal Exercise To Do Next

The best next exercise is:

```text
floor + wall + hinge door + actuator
```

Required pieces:

- `worldbody`
- static floor geom
- static wall geom
- `body name="door"`
- `joint type="hinge"`
- `actuator` controlling the hinge
- Python script setting `data.ctrl`
- loop with `mj_step`
- render video
- read `data.joint("door_hinge").qpos` and decide if the door opened

This small exercise directly prepares us for:

```text
robot opens door
robot opens cabinet
robot opens microwave
```

