"""Reusable task-building components for the Week7 MuJoCo exercises."""

import os


# Large generated meshes can make BLAS/OpenMP over-subscribe this shared host.
# Respect explicit user settings, but use one thread by default for stable model
# compilation and deterministic validation.
for _thread_variable in (
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
):
    os.environ.setdefault(_thread_variable, "1")

from .executor import TaskExecutor, load_task_config
from .mujoco_adapter import MujocoJointMapping, MujocoStateAdapter
from .state import TaskState

__all__ = [
    "MujocoJointMapping",
    "MujocoStateAdapter",
    "TaskExecutor",
    "TaskState",
    "load_task_config",
]
