# Development Machine Migration Notes

This guide explains how to synchronize the current VS Code workspace, SceneSmith, Articraft, Week 4–Week 8 notes, and key results to a new development machine.

Current workspace:

```text
/home/users/dazhi.sun-labs/projects
```

## 1. What to Synchronize

The following directories should be synchronized:

```text
articraft/
scenesmith/
week1_note/
week2_note/
week3_note/
week4_note/
week5_note/
week6_note/
week7_note/
week8_note/
.vscode/
dev_machine_migration/
```

The most important directories are:

```text
scenesmith/outputs/
scenesmith/viewer/
articraft/data/cache/
week6_note/
week7_note/
week8_note/
```

These directories contain generated scenes, assets, MuJoCo XML files, YAML configurations, GIF videos, trajectory JSON files, and validation results.

## 2. What Not to Synchronize

Do not copy the virtual environments directly:

```text
articraft/.venv/
scenesmith/.venv/
scenesmith/.mujoco_venv/
```

Reasons:

```text
Virtual environments are closely tied to machine paths, Python versions,
and system libraries. Copying them directly is likely to break them.
Recreating the environments on the new machine is more reliable.
```

The scripts exclude the following directories by default:

```text
.venv/
.mujoco_venv/
node_modules/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

## 3. Create a Resource Inventory on the Old Machine

Run the following command on the old development machine:

```bash
cd /home/users/dazhi.sun-labs/projects
bash dev_machine_migration/scripts/01_inventory.sh
```

The output is saved under:

```text
dev_machine_migration/inventory/
```

The inventory records:

```text
Project directory sizes
Python version
Key file list
Week 6–Week 8 result files
VS Code configuration
```

## 4. Synchronize from the Old Machine to the New Machine

First, confirm that the new machine is reachable through SSH. For example:

```bash
ssh user@new-dev-machine
```

Then run the following command on the old machine:

```bash
cd /home/users/dazhi.sun-labs/projects
bash dev_machine_migration/scripts/02_sync_to_new_machine.sh user@new-dev-machine /home/users/dazhi.sun-labs/projects
```

Replace `user@new-dev-machine` with the actual login address of the new machine.

If the destination path on the new machine is different, replace the second argument accordingly.

## 5. Rebuild the Environments on the New Machine

After logging in to the new machine, run:

```bash
cd /home/users/dazhi.sun-labs/projects
bash dev_machine_migration/scripts/03_restore_envs_on_new_machine.sh
```

The script attempts to:

```text
Check Python
Check uv
Restore the SceneSmith uv environment
Create scenesmith/.mujoco_venv
Install the lightweight dependencies required by the MuJoCo tasks
Restore the Articraft uv environment
```

If the company machine has no network access, `pip install` or `uv sync` may fail. If that happens, save the error output before troubleshooting further.

## 6. Verify the Migration on the New Machine

Run:

```bash
cd /home/users/dazhi.sun-labs/projects
bash dev_machine_migration/scripts/04_check_after_restore.sh
```

Check the following items carefully:

```text
Week 7 tests pass
Week 8 tests pass
Key GIF, JSON, and YAML files exist
MuJoCo can be imported
VS Code configuration exists
```

## 7. VS Code Considerations

The current VS Code configuration is stored at:

```text
.vscode/settings.json
```

Automatic port forwarding is already configured for:

```text
8902: SceneSmith Viewer
```

Install or confirm the following VS Code extensions on the new machine:

```text
Python
Pylance
Jupyter
Remote - SSH
GitLens
YAML
XML
```

## 8. Minimum Post-Migration Acceptance Criteria

The new machine must support at least the following:

```text
1. Open /home/users/dazhi.sun-labs/projects
2. Access week6_note, week7_note, and week8_note
3. Run the Week 7 and Week 8 tests
4. Open the saved GIF and result JSON files
5. Import mujoco
6. Continue running configuration-driven tasks
```

## 9. Current Resource Size

Approximate sizes of the main directories:

```text
articraft: 2.3G
scenesmith: 12G
week4_note: 16M
week5_note: 254M
week6_note: 71M
week7_note: 61M
week8_note: 241M
```

The total size is manageable, but `scenesmith/outputs` and some generated assets are relatively large. Use `rsync` instead of dragging files manually.
