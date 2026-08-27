# Cabinet Handle Demo

## Overview

This project is a simple embodied AI task simulation.

A robot must move to a cabinet, grab the handle, and then open the cabinet door.

Compared with the previous version, this demo introduces an additional state variable:

```python
has_grabbed_handle
```

The robot must satisfy the precondition of grabbing the handle before it can pull the door.

---

## Task Goal

Open the cabinet door to at least 80 degrees.

Success condition:

```python
door_angle >= 80
```

---

## Observation Space

The robot observes:

* robot_position
* cabinet_position
* hinge_position
* door_angle
* has_grabbed_handle

Example:

```python
observation = {
    "robot_position": 0,
    "cabinet_position": 5,
    "hinge_position": 5,
    "door_angle": 0,
    "has_grabbed_handle": False
}
```

---

## Action Space

Available actions:

1. move_to_cabinet
2. grab_handle
3. pull_door
4. stop

---

## Policy Logic

The policy follows a simple rule-based decision process:

1. If the robot has not reached the cabinet:

   * move_to_cabinet

2. If the robot has reached the cabinet but has not grabbed the handle:

   * grab_handle

3. If the robot has grabbed the handle and the door angle is below the target:

   * pull_door

4. Otherwise:

   * stop

---

## State Transition

### move_to_cabinet

```python
robot_position += 1
```

### grab_handle

```python
has_grabbed_handle = True
```

### pull_door

```python
door_angle += 20
```

This action is only effective when:

```python
has_grabbed_handle == True
```

---

## Learning Outcome

This project introduces an important embodied AI concept:

### Action Preconditions

Some actions can only be executed when specific conditions are satisfied.

Example:

```text
Grab Handle
↓
Pull Door
```

The robot must complete the first step before performing the second.

This idea appears frequently in embodied AI tasks, task planning, and robotic manipulation.
