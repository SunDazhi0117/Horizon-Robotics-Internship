# Week 3 Articraft Work Summary

## 1. Overview

This week, I continued working on the Articraft articulated object generation workflow. The main focus shifted from simply generating articulated objects to improving the viewer-side workflow, motion visualization, video export, and image-guided generation entry.

The key goal was to make generated objects easier to inspect, demonstrate, and present. Instead of only viewing articulated objects interactively in the Viewer, I worked on making the Viewer capable of automatically exporting motion demonstration videos.

The main areas of work included:

1. Adding Viewer-side MP4 export.
2. Improving the motion logic for exported videos.
3. Adding a Photo-based generation entry.
4. Making motion input optional so that possible motion can be inferred from an uploaded image.
5. Debugging and fixing an MP4 export issue related to Viewer loading.

---

## 2. Main Features Implemented

### 2.1 Viewer-side MP4 Export

I added an MP4 export feature to the Articraft Viewer. This allows users to generate a motion demonstration video directly from the Viewer without manually recording the screen.

The intended workflow is:

1. The user opens a generated articulated object in the Viewer.
2. The user clicks the MP4 export button.
3. The system automatically opens the Viewer page in the background.
4. The script drives the object joints.
5. Frames are captured automatically.
6. The frames are combined into an MP4 video.
7. The generated video can be viewed from the Viewer.

This makes the generated articulated objects easier to share, review, and present.

---

### 2.2 Sequential Joint Motion

The first version of the export logic moved all joints at the same time. This made the video difficult to understand, especially for complex objects with multiple moving parts.

I improved the motion logic so that joints move one by one.

For example, in a folding toolbox:

1. The top lid opens first and remains open.
2. The left tray opens and remains open.
3. The right tray opens and remains open.
4. The upper drawer slides out and remains extended.
5. The lower drawer slides out last.

This makes the exported motion clearer. It also prevents later moving parts from being hidden by earlier parts returning to the closed position.

---

### 2.3 Photo-based Generation Entry

I added a Photo feature entry to the interface. The goal is to allow users to upload a real-world photo and combine it with a text prompt to generate an articulated object.

The intended workflow is:

1. The user uploads an image.
2. The user optionally enters a text prompt.
3. The frontend sends the image and prompt to the backend.
4. The backend prepares the generation request.
5. The model uses the image as visual reference.
6. Articraft generates a corresponding articulated object.

This extends the generation workflow from text-only generation to image-guided articulated object generation.

---

### 2.4 Optional Motion Input

The Photo feature was further upgraded so that motion input can be optional.

This means the user can upload only a photo, and the system can attempt to infer the possible motion automatically from the object appearance.

Example motion assumptions include:

* A cabinet door may imply a revolute joint.
* A drawer may imply a prismatic joint.
* A bottle cap may imply a continuous or revolute joint.
* A folding toolbox may imply multiple revolute and prismatic joints.

This makes the workflow more flexible and closer to real-world object understanding.

---

## 3. MP4 Export Workflow

The MP4 export pipeline connects the frontend, backend, Viewer, Playwright automation, and ffmpeg.

The workflow is:

1. The user clicks the Export MP4 button in the Viewer.
2. The frontend sends an export request to the backend.
3. The backend locates the current generated record.
4. The video export module starts the export task.
5. A Playwright script opens the Viewer page.
6. The script drives joint sliders sequentially.
7. Screenshots are captured frame by frame.
8. ffmpeg combines the captured frames into an MP4 file.
9. The Viewer returns the generated video for the user to inspect.

This workflow turns an interactive articulated object into a shareable video demonstration.

---

## 4. Key Files Involved

The main files involved in this work include:

### `AppHeader.tsx`

This file provides the frontend entry point for the MP4 export button and related user interaction.

### `records.py`

This file helps manage and locate generated records. It connects the Viewer or backend logic with the correct record data.

### `video_export.py`

This file organizes the backend-side MP4 export workflow. It connects the current record with the video export script.

### `scripts/export_viewer_mp4.py`

This script performs the actual video export process. It uses Playwright to open the Viewer, drive motion controls, capture frames, and call ffmpeg to generate the final MP4.

### Photo-related frontend and backend files

These files support image upload and photo-based generation. They help pass image input and prompt information from the frontend to the backend generation workflow.

---

## 5. Important Bug Fix

### 5.1 MP4 Export Stuck at Opening Viewer

During testing, the MP4 export process became stuck at:

```text
[1/5] Opening Viewer
```

After investigation, I found that the export script used:

```python
wait_until="networkidle"
```

This caused a problem because the Viewer page may keep active network connections. As a result, Playwright could keep waiting for the page to become fully network-idle and never continue to the next export step.

The fix was to change the page loading condition to:

```python
wait_until="domcontentloaded"
```

and then explicitly wait for the rendering canvas:

```python
await page.wait_for_selector("canvas", timeout=30_000)
```

After this fix, the MP4 export process continued successfully and the generated video could be viewed.

This was an important debugging step because the Viewer backend was running correctly, but the export automation was blocked by an inappropriate page-loading condition.

---

## 6. Demo Results

The MP4 export feature can now be tested on complex articulated objects.

Example demo objects include:

### Demo 1: Folding Toolbox

Motion sequence:

1. Top lid opens.
2. Left tray opens.
3. Right tray opens.
4. Upper drawer slides out.
5. Lower drawer slides out.

This object is useful for testing sequential motion and whether previous parts remain open during later motion.

### Demo 2: Microwave

Motion sequence may include:

1. Front door opens.
2. Tray slides out.
3. Turntable rotates.
4. Knobs rotate.

This object is useful for testing mixed revolute, prismatic, and continuous joints.

### Demo 3: Dishwasher or Printer

These objects are useful for testing more complex layouts with multiple moving parts, drawer-like motions, hinged panels, and internal moving components.

For each demo, the key evaluation points are:

* Whether the MP4 exports successfully.
* Whether the video can be played normally.
* Whether the motion sequence is clear.
* Whether moving parts remain visible.
* Whether there are obvious geometry intersections or occlusion issues.

---

## 7. Current Limitations

Although the main workflow is working, there are still several limitations:

1. Photo-based generation still depends on valid API access or a working backend model provider.
2. Motion inference from image input needs more testing.
3. Some generated objects may still have geometry issues or incorrect joint axes.
4. The MP4 export camera angle may need further improvement for different object shapes.
5. Sequential motion currently depends on joint ordering and may benefit from better motion metadata.
6. More object categories should be tested to make the export workflow more robust.

---

## 8. Next Steps

The next steps are:

1. Test MP4 export on more generated records.
2. Collect several successful MP4 demo videos.
3. Improve camera framing for exported videos.
4. Add clearer error messages when API keys or required dependencies are missing.
5. Test photo-based generation once API access is available.
6. Document common motion bugs and debugging methods.
7. Save stable changes using clear Git commits.
8. Prepare a short demo package for presentation.

---

## 9. Summary

This week, the work moved beyond basic object generation and focused more on improving the Articraft Viewer workflow.

The MP4 export feature makes generated articulated objects easier to demonstrate and share. The sequential motion logic improves the clarity of exported videos. The Photo entry and optional motion input move the system toward image-guided articulated object generation.

Overall, the work improved both the usability and presentation quality of the Articraft pipeline.
