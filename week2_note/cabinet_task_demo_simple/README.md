# Cabinet Task Demo 

## Goal

This demo simulates a simple embodied AI task:

Open a cabinet door in a living room scene.

## Observation

The robot observes:

- robot_position
- cabinet_position
- hinge_position (not included)
- door_angle

## Task Goal

Open the cabinet door to at least 80 degrees.

## Action Space

The robot can choose from four discrete actions:

- move_to_cabinet
- grab_handle (This process is not included in this version.)
- pull_door
- stop

## Evaluation

The task is successful if:

```python
door_angle >= 80