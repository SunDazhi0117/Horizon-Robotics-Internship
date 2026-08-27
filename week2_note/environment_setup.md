# Articraft Environment Setup

## Goal

Set up the Articraft environment and successfully run the project locally.

---

## Initial Situation

Before setup:

* Python version: 3.13.13
* Conda available
* uv not installed
* just not installed
* Articraft repository successfully cloned

According to the official documentation, Articraft supports:

* Python 3.11
* Python 3.12

Python 3.13 is currently not supported.

---

## Environment Creation

Created a dedicated conda environment:

```bash
conda create -n articraft_env python=3.12
```

Activated the environment:

```bash
conda activate articraft_env
```

Verified Python version:

```bash
python --version
```

Result:

```text
Python 3.12.x
```

---

## Installing Required Tools

### uv

Initial installation failed because the machine could not access PyPI normally.

Installed successfully using the Tsinghua mirror:

```bash
pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

### just

Installed through conda-forge:

```bash
conda install -c conda-forge just
```

Verified installation:

```bash
uv --version
just --version
```

---

## Running Project Setup

Executed:

```bash
just setup
```

The first attempts failed because several dependencies could not be downloaded.

After checking network connectivity, proxy configuration was adjusted and conflicting mirror settings were removed.

The setup process then completed successfully.

---

## Setup Result

Successfully completed:

```bash
just setup
```

Generated and configured:

* Python virtual environment (.venv)
* Project dependencies
* .env configuration file
* Git hooks
* Dataset storage
* Workbench storage

Articraft is now ready for further exploration and development.

---

## Next Step

* Explore Articraft architecture
* Analyze articulated object examples
* Understand links and joints
* Study revolute and prismatic articulations
* Run and inspect example assets

```
```
