# Articraft Generation and Viewer Rendering Workflow

## 1. Project Setup and Asset Hydration

The first step is to clone the Articraft project from GitHub to the Linux server. After that, I mainly operate the project through VS Code Remote.

The general workflow is:

```text
GitHub repository
        ↓
Linux server
        ↓
VS Code Remote
        ↓
Articraft environment
        ↓
Viewer
```

To view an existing articulated object in the Viewer, the corresponding record must be available locally.

However, GitHub does not directly store every large asset file as a normal file. Many records are managed through Git LFS. In this case, the local file may only be a Git LFS pointer instead of the real record payload.

A Git LFS pointer is not the actual asset. It only tells Git LFS where the real large file is stored.

For example, when I wanted to inspect the classic bottle record, I needed to hydrate the specific record by pulling its real Git LFS content:

```bash
git -c lfs.fetchexclude= lfs pull \
  --include="data/records/rec_a-classic-occ-bottle-with-articulated-cap_20260321_164200_149541_6af2da87/**" \
  --exclude=""
```

This command means:

* `git -c lfs.fetchexclude=` temporarily clears the default LFS fetch-exclude rule;
* `lfs pull` downloads the real LFS content;
* `--include="..."` specifies the exact record folder I want to hydrate;
* `--exclude=""` ensures that no additional content is excluded.

After this step, the local record is no longer just a Git LFS pointer. The real record payload is available, and the object can be loaded and inspected in the Viewer.

---

## 2. Text-based Generation Workflow

The text-based generation workflow starts from a Linux command such as:

```bash
uv run articraft generate ...
```

This command connects to the Articraft CLI entry point defined in `pyproject.toml`:

```toml
articraft = "cli.main:main"
```

This means that when the command line recognizes `articraft`, it runs the `main` function in `cli.main`.

The simplified generation pipeline is:

```text
Linux command
        ↓
Articraft CLI
        ↓
Generate command
        ↓
Agent runner
        ↓
Codex / GPT writes and edits model.py
        ↓
compile_model compiles model.py
        ↓
URDF and assets are generated
        ↓
Record is saved
        ↓
Viewer reads the materialized record
```

In this process, GPT-5.5 / Codex is the model used for generation. Its role is to think about the object design and generate code.

However, Codex does not directly control the file system by itself. Articraft provides the tools that allow the agent to read files, write files, edit files, compile the model, and save the result.

In short:

```text
Codex / GPT decides what code should be written.
Articraft provides the tools, file system access, validation, compilation, and Viewer integration.
```

---

## 3. From `uv run articraft generate` to `_run_generate`

The command:

```bash
uv run articraft generate ...
```

eventually reaches the CLI code in `main.py`.

Inside `main.py`, the `generate` command is registered with code similar to:

```python
generate = subparsers.add_parser(
    "generate",
    help="Generate a workbench record from a prompt."
)
```

This means that when the user calls:

```bash
articraft generate
```

the CLI will trigger the generation logic.

The function `_run_generate` is then responsible for organizing the generation parameters, such as:

* user prompt;
* provider;
* model;
* thinking level;
* output settings;
* and other generation options.

After preparing these parameters, `_run_generate` passes the task to the agent runner:

```python
return agent_runner.main(argv)
```

At this point, the CLI layer has finished its job. The next stage is handled by the agent runner.

---

## 4. Runner and Single-run Execution

The runner layer checks whether the generation parameters are valid.

It checks information such as:

* API mode;
* model;
* provider;
* input format;
* runtime configuration.

The important relationship is that `runner.py` imports and wraps functions from `single_run.py`, including functions such as:

```python
run_from_input
run_from_input_impl
execute_single_run
```

This means that when another part of the system calls `runner.py`'s `run_from_input`, the actual generation work is eventually delegated to `single_run.py`.

The simplified call chain is:

```text
main.py
  → _run_generate
  → agent_runner.main
  → runner_cli.py
  → runner.py
  → single_run.py
```

`runner_cli.py` is mainly responsible for validating command-line and provider settings. If everything is valid, it calls a function such as `run_from_input_func(...)`.

This function is connected to `runner.py`, and `runner.py` then passes the task to `single_run.py`.

---

## 5. What `single_run.py` Does

`single_run.py` prepares the low-level environment for one generation task.

It is responsible for:

* deciding the Articraft project root;
* preparing the staging directory;
* deciding where `model.py` should be written;
* preparing record-related metadata;
* ensuring required folders exist;
* starting the actual agent loop.

At this stage, Articraft has not yet generated the final asset. It is preparing the workspace where the model code will be created.

The key idea is:

```text
single_run.py decides where this generation should happen.
```

For example, it determines the target file:

```text
staging/model.py
```

This is the file that the agent will write and modify.

---

## 6. Harness and Agent Tool Calls

After `single_run.py` prepares the generation environment, it hands the task to `harness.py`.

The relationship can be understood like this:

```text
single_run.py:
"This is the model.py file that needs to be written."

harness.py:
"Got it. I will ask Codex what to do next and execute its tool calls."
```

`harness.py` asks Codex something like:

```text
The user wants this articulated object.
Here are the SDK instructions.
Here are the available tools.
What should you do next?
```

Codex may respond with a tool call, for example:

```text
I want to call write_file and write this code into model.py.
```

Then `harness.py` executes the tool call.

The actual workflow is:

```text
single_run.py determines the target file: staging/model.py
        ↓
harness.py stores this path as self.file_path
        ↓
Codex returns a tool call: write_file(content=...)
        ↓
harness.py executes the tool call
        ↓
write_file opens self.file_path
        ↓
Codex-generated code is written into staging/model.py
```

This is why Codex can generate `model.py`: not because it directly controls the system, but because Articraft provides controlled tools such as `write_file`.

Articraft also provides SDK documentation and examples to Codex, so the model knows the correct concepts and APIs, such as:

* `part`;
* `visual`;
* `articulation`;
* `REVOLUTE`;
* `PRISMATIC`;
* `CONTINUOUS`;
* `MotionLimits`;
* `Origin`.

---

## 7. From `model.py` to URDF

After `model.py` is created, it still needs to become something that the Viewer can render.

`model.py` is Python code. It describes how to construct an articulated object, but it is not directly a 3D asset file.

The next step is compilation.

If Codex calls the `compile_model` tool, Articraft starts compiling the current `model.py`.

The simplified process is:

```text
model.py
        ↓
Python code is executed
        ↓
An internal ArticulatedObject data structure is created
        ↓
The compiler converts this object into URDF XML
        ↓
URDF and related assets are materialized
```

The compiler function, such as `compile_object_to_urdf_xml`, converts the internal object representation into a URDF XML string.

URDF is the format that describes:

* links;
* joints;
* joint axes;
* visual geometry;
* collision geometry;
* parent-child relationships;
* motion limits.

After this step, the generated object becomes something the Viewer can load and render.

---

## 8. Record Persistence

After a successful generation and compilation, Articraft saves the result as a record.

A record may contain files such as:

* `model.py`;
* metadata;
* prompt information;
* traces;
* materialized output;
* URDF-related files.

The record makes the generation result reusable. Instead of generating everything again, the Viewer can load an existing record and display it.

The simplified idea is:

```text
Generation result
        ↓
Saved as a record
        ↓
Viewer can load this record later
```

---

## 9. Viewer Rendering Workflow

The Viewer does not simply read the prompt. It reads the generated record and its materialized files.

The simplified Viewer rendering pipeline is:

```text
Record / materialized files
        ↓
Viewer backend API
        ↓
URDF and asset files are served
        ↓
Viewer frontend receives the files
        ↓
Viewer 3D component parses and renders the object
```

A backend route such as `viewer/api/routes/files.py` is responsible for serving the necessary generated files to the frontend.

Then the frontend Viewer, especially the 3D rendering part, loads the URDF and related assets and turns them into an interactive 3D articulated object.

The Viewer can then show:

* object geometry;
* part hierarchy;
* joint sliders;
* revolute motion;
* prismatic motion;
* continuous rotation.

---

## 10. Overall Summary

The whole Articraft workflow can be summarized as:

```text
1. Clone Articraft from GitHub to the Linux server.
2. Use VS Code Remote to operate the project.
3. Hydrate required Git LFS records if existing assets are not fully downloaded.
4. Run uv run articraft generate ... to start text-based generation.
5. CLI main.py receives the generate command.
6. _run_generate organizes parameters and calls the agent runner.
7. runner_cli.py validates model, provider, and API settings.
8. runner.py wraps the generation functions.
9. single_run.py prepares the generation workspace and target files.
10. harness.py asks Codex what tool call to perform.
11. Codex writes or edits model.py through Articraft tools.
12. compile_model executes and compiles model.py.
13. The compiler converts the object into URDF and assets.
14. Articraft saves the result as a record.
15. Viewer backend serves the record and materialized files.
16. Viewer frontend renders the articulated object.
```

The key understanding is:

```text
Codex / GPT is responsible for reasoning and code generation.
Articraft is responsible for tooling, execution, compilation, persistence, and visualization.
The Viewer is responsible for loading the saved record and rendering the articulated object interactively.
```
