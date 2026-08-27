# 00. Python Basics Used by This Project

This chapter introduces only the Python features that appear repeatedly in the robot-task scripts.

## 1. Variables and Assignment

```python
phase = "grasp_left_handle"
```

`phase` is a variable name. `=` assigns the string on the right to that name. A later assignment replaces the value:

```python
phase = "open_left_door"
```

Assignment is not a mathematical equality. It means: store this value under this name.

## 2. Common Value Types

```python
name = "left_handle"   # str: text
count = 17             # int: whole number
angle = 1.5708         # float: decimal number
passed = True          # bool: True or False
```

Robot code uses strings for object names, integers for frame counts, floats for positions and angles, and booleans for checks.

## 3. None

```python
active_handle = None
```

`None` means that no value is currently assigned. It is useful when the robot is not touching a handle.

```python
if active_handle is not None:
    check_grasp(active_handle)
```

## 4. Lists

Lists keep ordered values and can grow:

```python
sequence = []
sequence.append("start")
sequence.append("grasp")
```

Now `sequence` is `['start', 'grasp']`.

Indexing starts at zero:

```python
first = sequence[0]
last = sequence[-1]
```

Slicing returns part of a list:

```python
path[:-1]  # every item except the last
path[1:]   # every item except the first
```

`append(value)` adds one item. `extend(values)` adds every item from another iterable.

## 5. Dictionaries

Dictionaries map keys to values:

```python
state = {
    "phase": "open_right_door",
    "right_hinge": 1.2,
    "passed": True,
}
```

Read or update a field with its key:

```python
angle = state["right_hinge"]
state["passed"] = False
```

Task states and JSON summaries use dictionaries because each value has a clear name.

## 6. NumPy Arrays

```python
import numpy as np

base = np.array([2.0, 1.5, 0.0], dtype=float)
```

This array stores the base x position, y position, and yaw. NumPy supports element-wise arithmetic:

```python
start = np.array([0.0, 0.0])
end = np.array([2.0, 4.0])
middle = 0.5 * start + 0.5 * end
```

`middle` becomes `[1.0, 2.0]`.

Use `.copy()` when a new independent array is required:

```python
next_qpos = current_qpos.copy()
```

Without the copy, two variables may refer to the same mutable array.

## 7. Functions

```python
def smooth(alpha: float) -> float:
    return alpha * alpha * (3.0 - 2.0 * alpha)
```

- `def` starts a function definition.
- `alpha` is an input parameter.
- `: float` is a type hint.
- `-> float` describes the expected return type.
- `return` sends a value back to the caller.

Calling the function executes it:

```python
value = smooth(0.5)
```

## 8. Type Hints

```python
def interpolate(path: list[np.ndarray]) -> list[np.ndarray]:
    ...
```

Type hints help readers and editors understand expected values. Python does not automatically enforce most hints at runtime.

## 9. for Loops

```python
for alpha in np.linspace(0.0, 1.0, 5):
    print(alpha)
```

The body executes once for each value. `np.linspace(0.0, 1.0, 5)` produces five evenly spaced samples from 0 to 1.

## 10. range, enumerate, and zip

`range` produces integer indices:

```python
for index in range(3):
    print(index)  # 0, 1, 2
```

`enumerate` gives both the index and value:

```python
for index, state in enumerate(sequence):
    validate(index, state)
```

`zip` pairs items:

```python
for start, end in zip(path[:-1], path[1:]):
    interpolate_edge(start, end)
```

For `[A, B, C]`, this creates `(A, B)` and `(B, C)`.

## 11. Conditions

```python
if door_angle >= target_angle:
    task_passed = True
else:
    task_passed = False
```

Common comparisons are `==`, `!=`, `<`, `<=`, `>`, and `>=`.

Logical operators combine conditions:

```python
passed = door_open and grasp_retained and not collision_detected
```

## 12. Classes and Objects

```python
model = mujoco.MjModel.from_xml_path(xml_path)
data = mujoco.MjData(model)
```

`MjModel` and `MjData` are classes. `model` and `data` are objects created from those classes. Attributes are accessed with a dot, such as `data.qpos` and `model.njnt`.

An actuator is not itself a Python class in this context. It is an element compiled into `mjModel`; control values are written through `data.ctrl`.

## 13. Positional and Keyword Arguments

```python
append_state(sequence, "grasp", base, arm_qpos, finger)
```

These are positional arguments, so order matters.

```python
append_state(
    sequence=sequence,
    phase="grasp",
    base=base,
    qpos=arm_qpos,
    finger=finger,
)
```

These are keyword arguments. Their names make long calls easier to read.

## 14. Imports

```python
import os
from pathlib import Path
import numpy as np
```

- `os` provides operating-system functions and environment variables.
- `Path` builds filesystem paths safely.
- `numpy` is imported under the shorter name `np`.

## 15. Paths and __file__

```python
ROOT = Path(__file__).resolve().parents[1]
XML_PATH = ROOT / "xml" / "scene.xml"
```

`__file__` is the path of the running script. `resolve()` makes it absolute. `parents[1]` moves two directory levels upward. `/` joins path components when used with `Path` objects.

## 16. Minimum Self-Check

You should now be able to explain:

1. the difference between a list and dictionary;
2. why arrays are copied before editing;
3. what a function input and return value are;
4. how a `for` loop changes `alpha` over time;
5. why `zip(path[:-1], path[1:])` creates path edges;
6. what `Path(__file__)` refers to.
