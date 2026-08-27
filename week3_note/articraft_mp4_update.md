# Articraft Update: Viewer-side MP4 Export Workflow

## 1. Frontend Entry: MP4 Export Button

The AI agent Codex first added the following function in `AppHeader.tsx`:

```tsx
const handleExportMp4 = useCallback(async () => {
```

`AppHeader.tsx` is responsible for the header area of the Viewer. By adding this function, the Viewer now has an `MP4` export button in the upper-right corner.

This function contains several important steps. It checks whether a record has been selected, updates the export status, sends an export request to the backend, and finally receives the generated video URL.

---

## 2. Checking Whether a Record Has Been Selected

The first important part is:

```tsx
if (!state.selection || exportState.status === "exporting") {
  return;
}
```

This code checks whether the user has selected a record and whether an export task is already running.

If no record is selected, or if a video is already being generated, the function stops immediately. This prevents the system from starting an invalid export task or running multiple export tasks at the same time.

If a record has been selected, `state.selection` will store the information about the selected object.

---

## 3. Identifying the Selected Object

The next part is:

```tsx
const currentSelectionKey =
  state.selection.kind === "record"
    ? state.selection.recordId
    : `${state.selection.runId}:${state.selection.recordId}`;
```

This code creates a unique key for the currently selected object.

If the selected object is a normal record, the key is simply the `recordId`.

If the selected object comes from a staging run, the key combines the `runId` and `recordId`. This helps the frontend track exactly which object is being exported.

---

## 4. Updating the Export State

The next part is:

```tsx
setExportState({
  status: "exporting",
  fileUrl: null,
  error: null,
  selectionKey: currentSelectionKey,
});
```

This code updates the frontend export status.

It tells the Viewer that the video is currently being generated. It also clears the previous file URL and error message.

The export state can represent different situations, such as:

* the video is being generated;
* the export failed;
* the export succeeded;
* the generated video file is ready to view or download.

---

## 5. Showing the Loading Icon

The frontend also changes the button icon according to the export status:

```tsx
{exportState.status === "exporting" ? (
  <LoaderCircle className="size-3 animate-spin" />
) : (
  <Video className="size-3" />
)}
```

When the export is running, the button shows a spinning loading icon. This tells the user that the MP4 video is being generated.

When the export is not running, the button shows a normal video icon.

This improves the user experience because the user can clearly see whether the export process is still running.

---

## 6. Sending the Export Request to the Backend

The frontend then sends the MP4 export request to the backend:

```tsx
const result =
  state.selection.kind === "record"
    ? await exportRecordMp4(state.selection.recordId, { viewerUrl })
    : await exportStagingMp4(
        state.selection.runId,
        state.selection.recordId,
        { viewerUrl }
      );
```

This is the point where the frontend starts communicating with the backend.

The two functions used here are defined in `api.ts`:

* `exportRecordMp4`
* `exportStagingMp4`

Their purpose is to send a `POST` request for the selected record.

For example, when exporting a normal record, the request is sent to:

```text
/api/records/xxx/export-mp4
```

The request body includes `viewer_url`. This tells the backend which Viewer page should be opened during the MP4 export process.

---

## 7. Backend API Entry in `records.py`

The backend receives the export request in `records.py`:

```python
@router.post("/api/records/{record_id}/export-mp4", response_model=ExportMp4Response)
async def export_record_mp4(...):
```

This function starts working when the frontend sends an MP4 export request for the selected object.

Its responsibilities are:

* identify which `record` should be exported;
* locate the folder of that record;
* decide where the MP4 file should be saved;
* prepare the download URL;
* call the actual video generation function;
* return the video download URL to the frontend if the export succeeds;
* return an error message to the frontend if the export fails.

In other words, `records.py` acts as the backend API entry point for MP4 export.

---

## 8. Export Parameter Preparation in `video_export.py`

After the backend receives the request, `video_export.py` prepares the required export parameters.

These parameters include:

* `fps`;
* `width`;
* `height`;
* `output_path`;
* `viewer_url`;
* and other video export settings.

Then `video_export.py` uses `subprocess.run` to start the actual export script:

```text
scripts/export_viewer_mp4.py
```

This means `video_export.py` does not directly record the video itself. Instead, it organizes the export configuration and starts the script that performs the actual video generation.

---

## 9. Actual Video Generation in `export_viewer_mp4.py`

The script `export_viewer_mp4.py` performs the actual MP4 generation process.

It does the following steps:

1. Opens a hidden browser using Playwright.
2. Enters the Viewer page for the selected object.
3. Controls the object motion step by step.
4. Captures screenshots frame by frame.
5. Uses `ffmpeg` to combine the captured frames into an MP4 video.

After the MP4 file is generated, the backend returns the `file_url` to the frontend. The user can then view or download the exported video directly from the Viewer.

---

## 10. Overall Workflow Summary

The complete MP4 export workflow is:

```text
User clicks MP4 button in Viewer
        ↓
AppHeader.tsx starts handleExportMp4
        ↓
api.ts sends POST request to backend
        ↓
records.py receives the export request
        ↓
video_export.py prepares export parameters
        ↓
export_viewer_mp4.py opens Viewer using Playwright
        ↓
The script controls joints and captures frames
        ↓
ffmpeg combines frames into an MP4 file
        ↓
Backend returns file_url to frontend
        ↓
User views or downloads the exported video
```

This feature turns an interactive articulated object in the Viewer into a shareable MP4 motion demonstration.
