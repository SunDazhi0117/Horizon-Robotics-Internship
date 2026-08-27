# Bug Log

## 1. MP4 Export Stuck at Opening Viewer

### Problem

During MP4 export, the process became stuck at:

```text
[1/5] Opening Viewer
```

The Viewer itself was running, but the MP4 export process did not continue to the next steps.

### Investigation

At first, I checked whether the Viewer server was running:

```bash
curl -I http://127.0.0.1:8765
```

The response was:

```text
HTTP/1.1 405 Method Not Allowed
allow: GET
```

This showed that the server was alive. The `405` response happened because `curl -I` sends a `HEAD` request, while the Viewer endpoint only allows `GET`.

Then I searched the code related to MP4 export and Viewer loading:

```bash
grep -R --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=data/cache \
"Opening Viewer\|networkidle\|wait_until" -n .
```

The important result was:

```text
./scripts/export_viewer_mp4.py:75:
await page.goto(viewer_url, wait_until="networkidle", timeout=60_000)
```

### Cause

The export script used Playwright with:

```python
wait_until="networkidle"
```

This caused the script to wait until the Viewer page had no network activity.

However, the Viewer may keep active connections or background requests. As a result, Playwright could keep waiting forever and never continue to the frame capture stage.

### Solution

I changed the loading condition from:

```python
await page.goto(viewer_url, wait_until="networkidle", timeout=60_000)
```

to:

```python
await page.goto(viewer_url, wait_until="domcontentloaded", timeout=60_000)
await page.wait_for_timeout(3000)

try:
    await page.wait_for_selector("canvas", timeout=30_000)
except Exception:
    print("Warning: canvas not found after 30s; continuing anyway")
```

### Result

After restarting the Viewer and testing again, the MP4 export no longer got stuck at `Opening Viewer`.

The video could be generated and viewed successfully.

### Key Lesson

For Viewer pages with continuous network activity, `networkidle` is not always a reliable loading condition. It is safer to wait for `domcontentloaded` and then explicitly wait for the rendering canvas.

---

## 2. Multiple Joints Moving at the Same Time

### Problem

The first version of the MP4 export logic moved all joints at the same time.

For complex objects, this made the video hard to understand. For example, if a lid, side tray, and drawer all moved together, it was difficult to tell which part was connected to which joint.

### Cause

The export logic applied motion to all sliders together instead of animating one joint at a time.

This worked for simple objects, but it was not suitable for complex articulated objects.

### Solution

The motion logic was changed to sequential joint motion.

Instead of moving all joints together, the script now animates joints one by one.

For example:

```text
1. Open the top lid.
2. Keep the top lid open.
3. Open the left tray.
4. Keep the left tray open.
5. Open the right tray.
6. Keep the right tray open.
7. Slide out the upper drawer.
8. Keep the upper drawer extended.
9. Slide out the lower drawer.
```

### Result

The exported MP4 became much easier to understand.

The viewer can now clearly see the motion of each joint and how each part is connected to the main object.

### Key Lesson

For articulated object demonstration, sequential motion is usually clearer than moving all joints together.

---

## 3. Earlier Moving Parts Blocking Later Parts

### Problem

In some exported videos, earlier moving parts returned to their original position after their animation ended.

This caused later moving parts to be blocked or hidden.

For example, if a door closed again before a drawer moved, the drawer might be partially hidden by the door.

### Cause

The initial motion design treated each joint animation independently and did not preserve the final state of previous joints.

### Solution

The export logic was improved so that previous parts remain open or extended after their animation finishes.

For example:

```text
The lid opens and stays open.
The side tray opens and stays open.
The drawer slides out while the previous parts remain open.
```

### Result

Later moving parts became more visible in the exported MP4.

This made the video more suitable for demonstration and debugging.

### Key Lesson

For MP4 export, motion is not only about moving joints. It also needs to preserve useful visual states so that later motions remain visible.

---

## 4. Codex CLI Not Found

### Problem

When running Articraft generation with:

```bash
uv run articraft generate \
  --provider codex-cli \
  --model gpt-5.5 \
  --thinking-level high \
  "$PROMPT"
```

the system reported:

```text
Codex CLI provider requires the `codex` executable.
Command 'codex' not found
```

### Cause

The `codex` executable existed on the server, but it was not included in the current terminal `PATH`.

This means the generation had worked before, but the current shell environment could not find the Codex CLI executable.

### Investigation

I searched for the Codex executable:

```bash
find /home/users/dazhi.sun-labs -type f -name codex 2>/dev/null | head -30
```

The command found Codex under paths such as:

```text
/home/users/dazhi.sun-labs/miniconda3/envs/articraft_env/lib/node_modules/@openai/codex/...
```

### Solution

The path can be provided directly to Articraft using:

```bash
export ARTICRAFT_CODEX_CLI_BIN="/path/to/codex"
```

Then Articraft can use this executable when running the `codex-cli` provider.

### Key Lesson

A tool may already be installed, but the terminal may still not find it if its location is not included in `PATH`.

---

## 5. Node.js Version Too Old for Viewer Frontend

### Problem

When starting the Viewer, the frontend build failed with a JavaScript syntax error:

```text
SyntaxError: Unexpected token ?
```

The error came from newer JavaScript syntax such as:

```js
startIndex ?? 0
```

### Cause

The installed Node.js version was too old:

```text
node v12.4.0
npm 6.9.0
```

The Viewer frontend uses TypeScript and Vite, which require a newer Node.js version.

### Solution

The solution was to upgrade Node.js to a newer version, such as Node.js 18 or 20, and then rebuild the Viewer frontend.

### Key Lesson

Frontend build tools often require a modern Node.js version. When TypeScript or Vite fails with unexpected syntax errors, checking `node -v` should be one of the first debugging steps.

---

## 6. Photo Generation Depends on API Access

### Problem

The Photo-based generation entry was added, but full testing depends on valid API access.

### Cause

Image-guided generation requires a model provider that supports image input. This usually needs a valid API key or an already configured backend provider.

### Current Status

The frontend entry for Photo-based generation has been added, and the workflow direction is clear.

However, full end-to-end testing still depends on API access.

### Next Step

Once API access is available, the Photo workflow should be tested with simple objects such as:

* cabinet door;
* drawer;
* bottle cap;
* folding toolbox.

### Key Lesson

Feature entry and UI integration can be prepared first, but full validation of image-based generation requires working model access.
