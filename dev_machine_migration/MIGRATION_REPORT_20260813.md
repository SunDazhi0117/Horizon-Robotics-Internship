# Dev Machine Migration Report

Date: 2026-08-13 15:56 CST

## Target Machine

- Host: `blj.horizon.cc`
- Port: `2222`
- SSH login user: `dazhi.sun-labs@dazhi.sun-labs@10.36.14.83`
- Remote hostname: `aidc-gpu-dev5090-064.hogpu.cc`
- Remote project root: `/home/users/dazhi.sun-labs/projects`

Do not store the SSH password in this repository.

## Synced Project Folders

The following folders were copied to the new machine:

- `articraft`
- `scenesmith`
- `week1_note`
- `week2_note`
- `week3_note`
- `week4_note`
- `week5_note`
- `week6_note`
- `week7_note`
- `week8_note`
- `.vscode`
- `dev_machine_migration`

Remote sizes after migration:

- `articraft`: 2.0G
- `scenesmith`: 12G
- `week4_note`: 16M
- `week5_note`: 253M
- `week6_note`: 71M
- `week7_note`: 61M
- `week8_note`: 241M

## Synced Python Environments

The new machine did not have `uv`, `pip`, `conda`, or `python3-venv` available by default, so the working local environments were copied as a fallback.

Copied environments:

- `scenesmith/.venv`: 7.7G
- `scenesmith/.mujoco_venv`: 663M
- `articraft/.venv`: 1.5G
- `/home/users/dazhi.sun-labs/miniconda3/envs/articraft_env`: 656M
- `/home/users/dazhi.sun-labs/.local/share/uv/python/cpython-3.11.15-linux-x86_64-gnu`

Remote interpreter checks:

- `scenesmith/.mujoco_venv`: Python 3.11.15, MuJoCo 3.3.5
- `scenesmith/.venv`: Python 3.11.15
- `articraft/.venv`: Python 3.12.13

## Validation

Command run on the new machine:

```bash
cd /home/users/dazhi.sun-labs/projects
bash dev_machine_migration/scripts/04_check_after_restore.sh
```

Result:

- Basic folders: PASS
- Week8 key artifacts: PASS
- MuJoCo import: PASS
- Week7 tests: 14/14 PASS
- Week8 tests: 14/14 PASS
- Overall restore check: PASS

## Notes

- Project `.env` files were copied as part of preserving the working state. Treat them as sensitive.
- The copied virtual environments are a practical backup for the machine transition. Later, it would be cleaner to install `uv` or system `python3-venv` on the new machine and rebuild environments from lock files.
- No stable scene assets were modified during migration.

## How To Continue On The New Machine

Open VS Code Remote SSH to:

```bash
ssh -p 2222 -l 'dazhi.sun-labs@dazhi.sun-labs@10.36.14.83' blj.horizon.cc
```

Then open:

```bash
/home/users/dazhi.sun-labs/projects
```

Useful checks:

```bash
cd /home/users/dazhi.sun-labs/projects
bash dev_machine_migration/scripts/04_check_after_restore.sh
```
