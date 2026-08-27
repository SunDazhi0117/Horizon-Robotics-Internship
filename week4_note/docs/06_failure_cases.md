# Failure Cases and Debugging

This document records the failures that changed the implementation. It avoids
presenting the final successful scene as if it worked on the first attempt.

## 1. Floor-Plan-Only Runs Started Unrelated Services

**Symptom:** A floor-plan-only run failed because SAM3D, ArtVIP, HSSD,
Objaverse, or material data was unavailable.

**Cause:** Heavy generation and retrieval services were initialized before the
pipeline considered that both the start and stop stages were `floor_plan`.

**Fix:** Add stage-aware startup logic. A floor-plan-only run skips all
geometry, asset, articulated, and material services; other stage ranges keep
their original behavior.

**Lesson:** Pipeline boundaries should control dependency initialization.

## 2. A Manual Patch Broke Python Indentation

**Symptom:** SceneSmith stopped at import time with an `IndentationError`.

**Cause:** An experimental manual edit changed indentation near a conditional
block.

**Fix:** Restore the tracked file, verify it with `py_compile`, and then apply a
minimal conditional patch.

**Lesson:** Restore a known baseline before debugging behavior, and run syntax
checks immediately after editing.

## 3. Viewer Opened but the Scene Was Black or Inaccessible

**Symptom:** The browser showed viewer text but no visible model, or the URL
returned a connection/404 error.

**Investigation:** Check the HTTP server root, model URL, Three.js dependency
paths, GLB response, and camera framing separately.

**Fix:** Serve the scene directory from a known port, use model-relative URLs,
provide local Three.js dependencies, and frame the exported model bounds.

**Lesson:** A working HTML page does not prove that its model and JavaScript
dependencies are reachable.

## 4. Individual Furniture Files Were Not a Complete Scene

**Symptom:** Furniture GLBs could be inspected individually, but there was no
single file containing the room and all furniture.

**Cause:** Geometry generation and scene assembly are separate stages.
Furniture assets do not contain their final world placement.

**Fix:** Read `scene_state.json`, import the existing GLBs, apply saved
transforms, and export one combined BLEND and GLB.

**Lesson:** Scene state is a first-class artifact, not incidental metadata.

## 5. Python Environments Were Mixed

**Symptom:** SceneSmith commands used the Articraft virtual environment and
reported missing packages such as `pip`, `torch`, or `pydrake`.

**Cause:** The active shell Python did not match the project being executed.

**Fix:** Keep SceneSmith and Articraft environments separate and invoke the
intended interpreter explicitly.

**Lesson:** Environment identity should be checked before installing more
dependencies.

## 6. Valid Joint Limits Still Produced an Invalid Motion Sequence

**Symptom:** The door and tray each moved within their URDF limits, but the tray
intersected the closed door after approximately `0.11 m`.

**Cause:** Per-joint limits do not encode cross-joint task constraints.

**Initial fix:** Define the validated sequence as opening the door to at least
`1.50 rad` before extending the tray.

**Viewer resolution:** The tray slider is now disabled below `1.50 rad`. If the
tray is extended and the door moves below the safe angle, the Viewer retracts
the tray before allowing the closing pose.

**Lesson:** Physical validity must be checked over joint combinations and
trajectories, not only one joint at a time.

## 7. Generated Furniture Had Proportion Warnings

The static scene passed grounding, room-bound, collision, and accessibility
checks, but three generated assets still had questionable dimensions:

- kitchen counter height: `1.187 m`;
- thin shelving depth: `0.127 m`;
- study desk height: `0.947 m`.

**Lesson:** Collision-free geometry can still be semantically unrealistic.
Future validation should include category-specific dimension ranges.

## 8. System Firefox Could Not Run Headless

**Symptom:** The installed Firefox package could not create its Snap user-data
directory during automated screenshots.

**Fix:** Use the existing Playwright Chromium binary and record browser status,
failed requests, joint controls, and screenshots.

**Lesson:** Keep browser automation independent from the desktop browser
installation.

## 9. Raw Free-Cell Coverage Misrepresented Useful Accessibility

**Symptom:** The multi-articulated scene had no new collision, but a raw
free-cell coverage metric reported only `0.862861`.

**Cause:** Inflating perimeter furniture by the robot radius created three
narrow residual pockets between furniture and walls. Those cells were counted
as free but were not useful operating positions.

**Fix:** Keep raw coverage as a diagnostic, then separately verify central
circulation, microwave, cabinet, and reading-area targets. All four are
reachable from the open entrance.

**Lesson:** Accessibility should reflect task-relevant goals while still
exposing disconnected residual geometry.
