# Agent-Assisted Workflow Prompts

These are sanitized prompt patterns, not raw private transcripts. Local user
names, internal paths, tokens, and environment-specific identifiers have been
removed.

## Prompt Design Principles

A useful engineering prompt should state:

1. the current stable input;
2. the exact target artifact;
3. actions that are forbidden;
4. acceptance criteria;
5. evidence required in the final report.

The agent can inspect, implement, and run checks, but successful tool execution
is not accepted as proof by itself. File outputs and measured validation
results are required.

## 1. Isolate the Floor-Plan Stage

```text
Run only floor_plan -> floor_plan.

Do not install or download SAM3D, ArtVIP, HSSD, Objaverse, or materials.
When start_stage == stop_stage == "floor_plan", skip all heavy asset and
retrieval servers. Preserve existing behavior for every other stage range.

Restore the source file if needed, make the smallest patch, run py_compile,
execute the floor-plan-only test, and report the real error if it still fails.
```

Why it worked: the prompt constrained scope and required both syntax and runtime
evidence.

## 2. Assemble Existing Room and Furniture

```text
Do not generate a new room or new furniture.

Read the existing room BLEND, seven furniture GLBs, and scene_state.json.
Write a stable script that applies the saved transforms and exports one
complete GLB and BLEND file.

Verify room structure, furniture count, grounding, wall intersections,
collisions, accessibility, file sizes, and browser loading.
```

Why it worked: it separated asset reuse from scene assembly and defined a
concrete output contract.

## 3. Freeze a Stable Version

```text
Treat the current accepted scene as immutable.

Create a new version directory without overwriting the source. Copy only the
validated artifacts, write a human-readable report and machine-readable JSON,
generate SHA-256 checksums, and verify the original version again afterward.
```

Why it worked: it made version integrity an acceptance requirement rather than
an informal promise.

## 4. Integrate an Articulated URDF Object

```text
Do not regenerate the room, furniture, or articulated object.

Parse the existing microwave URDF, preserve link/joint hierarchy and metadata,
place it on the selected support surface, export a new GLB and BLEND file, and
add browser joint controls.

Sample closed, open, and transition states. Check support contact, joint axes,
limits, wall/furniture/self collision, accessibility, and browser Reset.
```

Why it worked: it required articulation preservation and motion validation, not
only a visually plausible import.

## 5. Produce an Acceptance Report

```text
Report exact source references, output sizes, joint types, axes and ranges,
closed/open checks, sampled collision results, accessibility, viewer status,
and known limitations.

Do not hide a failed check behind a general PASS. Distinguish validated normal
operation from invalid user-controlled joint combinations.
```

Why it worked: it forced the report to include the tray-door collision
condition instead of claiming universal collision freedom.

## 6. Scale to Multiple Articulated Objects

```text
Reuse the existing static room and successful URDF assets.

Add an entry door, a double-door cabinet, and a microwave. Give each asset a
separate namespace, preserve every joint in GLB, and expose all controls in the
browser.

Sample valid motion paths and check self-collision, static furniture,
inter-asset collision, room bounds, support, and required interaction-target
reachability. Do not accept the scene only because the GLB exports.
```

Why it worked: it treated multi-object identity, motion, and validation as
first-class requirements rather than repeating a visual import three times.

## Human and Agent Responsibilities

The agent handled repository inspection, scripts, file conversion, browser
automation, and repeatable checks. Human judgment remained necessary for:

- choosing project scope;
- deciding which generated result was worth preserving;
- visually judging geometry and proportions;
- deciding whether limitations were acceptable;
- approving what could be published.

This is better described as **agent-assisted engineering** than fully
autonomous generation.
