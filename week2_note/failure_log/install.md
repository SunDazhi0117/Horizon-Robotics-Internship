# Failure Log

## Case 001 - uv Installation Failure

### Problem

Failed to install uv using the default PyPI source.

### Error Message

```text
Connection reset by peer
```

### Root Cause

The development machine could not reliably access the default PyPI server.

### Solution

Use the Tsinghua mirror:

```bash
pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Result

uv installed successfully.

---

## Case 002 - Articraft Setup Failure

### Problem

The command:

```bash
just setup
```

failed during dependency installation.

### Error Message

```text
Connection reset by peer
```

and later:

```text
tunnel error: unsuccessful
```

### Root Cause

Network connectivity issues while downloading dependencies from Python package repositories.

Additional conflicts were introduced by temporary mirror configurations.

### Solution

1. Check connectivity to package servers.
2. Verify proxy settings.
3. Remove conflicting mirror environment variables.
4. Retry setup.

### Result

The setup process completed successfully.

---

## Lessons Learned

* Always verify the supported Python version before installing a project.
* Network issues are often the root cause of package installation failures.
* Proxy and mirror configurations can affect dependency resolution.
* Check connectivity before repeatedly retrying installation commands.

```
```
