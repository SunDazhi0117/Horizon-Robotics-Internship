import { useCallback, useMemo, useRef, useState, type JSX } from "react";
import { useIsFetching, useQueryClient } from "@tanstack/react-query";
import {
  ChevronLeft,
  ChevronRight,
  Download,
  ImagePlus,
  LoaderCircle,
  MessageSquare,
  RefreshCw,
  Video,
  X,
} from "lucide-react";

import { exportRecordMp4, exportStagingMp4, generateFromPhoto, saveFeedbackMemory } from "@/lib/api";
import { DASHBOARD_REFRESH_EVENT } from "@/lib/dashboard-events";
import { useRoute } from "@/lib/useRoute";
import { navigateTo } from "@/lib/router";
import { viewerQueryKeys } from "@/lib/viewer-queries";
import { useViewer } from "@/lib/viewer-context";
import { findStagingEntryInBootstrap } from "@/lib/record-summary";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tooltip, TooltipTrigger, TooltipContent } from "@/components/ui/tooltip";

const TRAILING_PUNCTUATION = /[\s,.;:!?)]*$/;
const MAX_REFERENCE_IMAGE_BYTES = 12 * 1024 * 1024;
const MAX_REFERENCE_PHOTOS = 8;

function truncateWithEllipsis(value: string, maxLength = 88): string {
  const normalized = value.replace(/\s+/g, " ").trim();
  if (!normalized) return "";

  const withoutExistingEllipsis = normalized.replace(/\.\.\.$/, "").trimEnd();
  if (withoutExistingEllipsis.length <= maxLength) {
    return withoutExistingEllipsis;
  }

  const truncated = withoutExistingEllipsis.slice(0, maxLength).trimEnd();
  return `${truncated.replace(TRAILING_PUNCTUATION, "")}...`;
}

async function readFileAsBase64(file: File): Promise<string> {
  if (file.size > MAX_REFERENCE_IMAGE_BYTES) {
    throw new Error("Reference image is too large. Use an image smaller than 12 MB.");
  }

  const bytes = new Uint8Array(await file.arrayBuffer());
  let binary = "";
  const chunkSize = 0x8000;

  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    const chunk = bytes.subarray(offset, offset + chunkSize);
    binary += String.fromCharCode(...chunk);
  }

  return window.btoa(binary);
}

function ViewerHeaderContents(): JSX.Element {
  const state = useViewer();
  const queryClient = useQueryClient();
  const activeFetchCount = useIsFetching({ queryKey: viewerQueryKeys.root() });
  const [feedbackDialogOpen, setFeedbackDialogOpen] = useState(false);
  const [feedbackProblem, setFeedbackProblem] = useState("");
  const [feedbackFix, setFeedbackFix] = useState("");
  const [feedbackObjectType, setFeedbackObjectType] = useState("");
  const [feedbackIssueTypes, setFeedbackIssueTypes] = useState("shape, detail");
  const [feedbackTags, setFeedbackTags] = useState("");
  const [feedbackStatus, setFeedbackStatus] = useState<{
    status: "idle" | "saving" | "saved" | "error";
    message: string | null;
  }>({ status: "idle", message: null });
  const [exportState, setExportState] = useState<{
    status: "idle" | "exporting" | "ready" | "error";
    fileUrl: string | null;
    error: string | null;
    selectionKey: string | null;
  }>({
    status: "idle",
    fileUrl: null,
    error: null,
    selectionKey: null,
  });

  const isStagingSelection = state.selection?.kind === "staging";
  const stagingEntry = isStagingSelection && state.selection?.kind === "staging"
    ? findStagingEntryInBootstrap(state.bootstrap, state.selection.runId, state.selection.recordId)
    : null;

  const titleSource = isStagingSelection
    ? stagingEntry?.title ?? null
    : state.selectedRecordSummary?.title ?? null;
  const selectedRecordTitleFull = titleSource;
  const selectedRecordTitle = titleSource ? truncateWithEllipsis(titleSource, 72) : null;
  const selectionKey = state.selection
    ? state.selection.kind === "record"
      ? state.selection.recordId
      : `${state.selection.runId}:${state.selection.recordId}`
    : null;
  const selectedFeedbackRecordId =
    state.selection?.kind === "record" ? state.selection.recordId : null;
  const exportFileUrl =
    exportState.status === "ready" && exportState.selectionKey === selectionKey
      ? exportState.fileUrl
      : null;
  const exportError =
    exportState.status === "error" && exportState.selectionKey === selectionKey
      ? exportState.error
      : null;
  const canExportMp4 = Boolean(state.selection);
  const viewerUrl = useMemo(() => {
    if (typeof window === "undefined" || !state.selection) {
      return null;
    }
    const url = new URL("/viewer", window.location.origin);
    if (state.selection.kind === "record") {
      url.searchParams.set("record", state.selection.recordId);
    } else {
      url.searchParams.set("staging", `${state.selection.runId}:${state.selection.recordId}`);
      url.searchParams.set("browser", "staging");
      url.searchParams.set("run", state.selection.runId);
    }
    return url.toString();
  }, [state.selection]);

  const handleRefresh = async () => {
    await queryClient.invalidateQueries({ queryKey: viewerQueryKeys.root() });
  };

  const handleExportMp4 = useCallback(async () => {
    if (!state.selection || exportState.status === "exporting") {
      return;
    }

    const currentSelectionKey =
      state.selection.kind === "record"
        ? state.selection.recordId
        : `${state.selection.runId}:${state.selection.recordId}`;

    setExportState({
      status: "exporting",
      fileUrl: null,
      error: null,
      selectionKey: currentSelectionKey,
    });

    try {
      const result =
        state.selection.kind === "record"
          ? await exportRecordMp4(state.selection.recordId, { viewerUrl })
          : await exportStagingMp4(state.selection.runId, state.selection.recordId, { viewerUrl });
      setExportState({
        status: "ready",
        fileUrl: result.file_url,
        error: null,
        selectionKey: currentSelectionKey,
      });
    } catch (error) {
      setExportState({
        status: "error",
        fileUrl: null,
        error: error instanceof Error ? error.message : "MP4 export failed.",
        selectionKey: currentSelectionKey,
      });
    }
  }, [exportState.status, state.selection, viewerUrl]);

  const resetFeedbackForm = useCallback(() => {
    setFeedbackProblem("");
    setFeedbackFix("");
    setFeedbackObjectType("");
    setFeedbackIssueTypes("shape, detail");
    setFeedbackTags("");
    setFeedbackStatus({ status: "idle", message: null });
  }, []);

  const handleFeedbackDialogOpenChange = useCallback((open: boolean) => {
    setFeedbackDialogOpen(open);
    if (!open) {
      resetFeedbackForm();
    } else if (!feedbackObjectType.trim() && selectedRecordTitleFull) {
      setFeedbackObjectType(truncateWithEllipsis(selectedRecordTitleFull, 80));
    }
  }, [feedbackObjectType, resetFeedbackForm, selectedRecordTitleFull]);

  const parseFeedbackList = useCallback((value: string): string[] => {
    return value
      .split(/[,\n]/)
      .map((item) => item.trim())
      .filter(Boolean)
      .slice(0, 16);
  }, []);

  const handleSaveFeedback = useCallback(async () => {
    if (!feedbackProblem.trim() || feedbackStatus.status === "saving") {
      return;
    }
    setFeedbackStatus({ status: "saving", message: null });
    try {
      await saveFeedbackMemory({
        recordId: selectedFeedbackRecordId,
        objectType: feedbackObjectType,
        issueTypes: parseFeedbackList(feedbackIssueTypes).slice(0, 8),
        problem: feedbackProblem,
        fix: feedbackFix,
        tags: parseFeedbackList(feedbackTags),
      });
      setFeedbackStatus({
        status: "saved",
        message: "Feedback saved. Future photo generations can reuse this lesson.",
      });
    } catch (error) {
      setFeedbackStatus({
        status: "error",
        message: error instanceof Error ? error.message : "Failed to save feedback.",
      });
    }
  }, [
    feedbackFix,
    feedbackIssueTypes,
    feedbackObjectType,
    feedbackProblem,
    feedbackStatus.status,
    feedbackTags,
    parseFeedbackList,
    selectedFeedbackRecordId,
  ]);

  return (
    <>
      <header className="flex h-11 shrink-0 items-center gap-3 border-b border-[var(--border-default)] bg-[var(--surface-0)] px-4">
        <div className="flex items-center gap-2 text-[12px]">
          <span className="font-semibold tracking-[-0.02em] text-[var(--text-primary)]">Articraft</span>
          <span className="text-[var(--border-strong)]">/</span>
          <span className="text-[var(--text-tertiary)]">Viewer</span>
        </div>

        <div className="mx-1 flex min-w-0 flex-1 items-center justify-center gap-2">
          {selectedRecordTitle ? (
            <>
              {isStagingSelection ? <Badge variant="success">STAGING</Badge> : null}
              <p
                className="max-w-full truncate text-[12px] text-[var(--text-secondary)]"
                title={selectedRecordTitleFull ?? undefined}
              >
                {selectedRecordTitle}
              </p>
            </>
          ) : (
            <p className="text-[12px] text-[var(--text-quaternary)]">No record selected</p>
          )}
        </div>

        <div className="flex items-center gap-1">
          {exportError ? (
            <p className="max-w-[260px] truncate text-[11px] text-red-500" title={exportError}>
              {exportError}
            </p>
          ) : null}
          {exportFileUrl ? (
            <a
              href={exportFileUrl}
              download
              className="inline-flex h-7 items-center justify-center gap-1 rounded-md px-2 text-[11px] font-medium text-[var(--text-tertiary)] transition-all duration-150 hover:bg-[var(--surface-2)] hover:text-[var(--text-secondary)]"
            >
              <Download className="size-3" />
              Download MP4
            </a>
          ) : null}
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setFeedbackDialogOpen(true)}
                disabled={!selectedFeedbackRecordId}
                className="h-7 gap-1 rounded-md px-2 text-[11px] text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
              >
                <MessageSquare className="size-3" />
                Feedback
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom">Save generation feedback memory</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleExportMp4}
                disabled={!canExportMp4 || exportState.status === "exporting"}
                className="h-7 gap-1 rounded-md px-2 text-[11px] text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
              >
                {exportState.status === "exporting" ? (
                  <LoaderCircle className="size-3 animate-spin" />
                ) : (
                  <Video className="size-3" />
                )}
                MP4
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom">Export animated MP4</TooltipContent>
          </Tooltip>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigateTo({ page: "dashboard" })}
            className="h-7 gap-1 rounded-md px-2 text-[11px] text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
          >
            <ChevronLeft className="size-3" />
            Dashboard
          </Button>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRefresh}
                disabled={activeFetchCount > 0}
                className="h-7 w-7 rounded-md p-0 text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
              >
                <RefreshCw
                  className={`size-3.5 ${activeFetchCount > 0 ? "animate-spin" : ""}`}
                />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom">Refresh</TooltipContent>
          </Tooltip>
        </div>
      </header>

      <Dialog open={feedbackDialogOpen} onOpenChange={handleFeedbackDialogOpenChange}>
        <DialogContent className="w-[min(560px,calc(100vw-32px))] p-4">
          <div className="flex items-start justify-between gap-3">
            <DialogHeader>
              <DialogTitle>Save Feedback Memory</DialogTitle>
              <DialogDescription>Record what went wrong and how future generations should avoid it.</DialogDescription>
            </DialogHeader>
            <DialogClose />
          </div>

          <div className="mt-4 grid gap-3">
            <div className="grid gap-1.5">
              <Label htmlFor="feedback-object" className="text-[12px] text-[var(--text-secondary)]">
                Object Type
              </Label>
              <Input
                id="feedback-object"
                value={feedbackObjectType}
                disabled={feedbackStatus.status === "saving"}
                onChange={(event) => setFeedbackObjectType(event.target.value)}
                placeholder="earbud charging case"
                className="h-8 text-[12px]"
              />
            </div>

            <div className="grid gap-1.5">
              <Label htmlFor="feedback-problem" className="text-[12px] text-[var(--text-secondary)]">
                Problem
              </Label>
              <textarea
                id="feedback-problem"
                value={feedbackProblem}
                disabled={feedbackStatus.status === "saving"}
                onChange={(event) => {
                  setFeedbackProblem(event.target.value);
                  setFeedbackStatus({ status: "idle", message: null });
                }}
                placeholder="Example: earbuds clip through the charging wells when lifted out."
                className="min-h-20 w-full resize-y rounded-md border border-[var(--border-default)] bg-[var(--surface-0)] px-2.5 py-2 text-[12px] text-[var(--text-primary)] outline-none transition-all duration-150 placeholder:text-[var(--text-quaternary)] focus-visible:border-[var(--accent)] focus-visible:ring-2 focus-visible:ring-[var(--accent-soft)] disabled:opacity-40"
              />
            </div>

            <div className="grid gap-1.5">
              <Label htmlFor="feedback-fix" className="text-[12px] text-[var(--text-secondary)]">
                Correction Pattern
              </Label>
              <textarea
                id="feedback-fix"
                value={feedbackFix}
                disabled={feedbackStatus.status === "saving"}
                onChange={(event) => {
                  setFeedbackFix(event.target.value);
                  setFeedbackStatus({ status: "idle", message: null });
                }}
                placeholder="Example: use an upward-outward-forward prismatic path with clearance, not a pure vertical lift."
                className="min-h-20 w-full resize-y rounded-md border border-[var(--border-default)] bg-[var(--surface-0)] px-2.5 py-2 text-[12px] text-[var(--text-primary)] outline-none transition-all duration-150 placeholder:text-[var(--text-quaternary)] focus-visible:border-[var(--accent)] focus-visible:ring-2 focus-visible:ring-[var(--accent-soft)] disabled:opacity-40"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div className="grid gap-1.5">
                <Label htmlFor="feedback-issues" className="text-[12px] text-[var(--text-secondary)]">
                  Issue Types
                </Label>
                <Input
                  id="feedback-issues"
                  value={feedbackIssueTypes}
                  disabled={feedbackStatus.status === "saving"}
                  onChange={(event) => setFeedbackIssueTypes(event.target.value)}
                  placeholder="shape, motion, collision"
                  className="h-8 text-[12px]"
                />
              </div>
              <div className="grid gap-1.5">
                <Label htmlFor="feedback-tags" className="text-[12px] text-[var(--text-secondary)]">
                  Tags
                </Label>
                <Input
                  id="feedback-tags"
                  value={feedbackTags}
                  disabled={feedbackStatus.status === "saving"}
                  onChange={(event) => setFeedbackTags(event.target.value)}
                  placeholder="airpods, hinge, earbuds"
                  className="h-8 text-[12px]"
                />
              </div>
            </div>

            {feedbackStatus.message ? (
              <div
                className={`rounded-md border px-3 py-2 text-[11px] ${
                  feedbackStatus.status === "error"
                    ? "border-red-500/30 bg-red-500/5 text-red-500"
                    : "border-[var(--border-default)] bg-[var(--surface-1)] text-[var(--text-secondary)]"
                }`}
              >
                {feedbackStatus.message}
              </div>
            ) : null}

            <div className="flex justify-end gap-2 pt-1">
              <Button
                variant="ghost"
                size="sm"
                className="h-8 px-3 text-[12px]"
                disabled={feedbackStatus.status === "saving"}
                onClick={() => setFeedbackDialogOpen(false)}
              >
                Close
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={handleSaveFeedback}
                disabled={!feedbackProblem.trim() || feedbackStatus.status === "saving"}
                className="h-8 gap-1 px-3 text-[12px]"
              >
                {feedbackStatus.status === "saving" ? (
                  <LoaderCircle className="size-3 animate-spin" />
                ) : (
                  <MessageSquare className="size-3" />
                )}
                Save
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

function DashboardHeaderContents(): JSX.Element {
  const queryClient = useQueryClient();
  const photoInputRef = useRef<HTMLInputElement | null>(null);
  const [photoDialogOpen, setPhotoDialogOpen] = useState(false);
  const [photoFiles, setPhotoFiles] = useState<File[]>([]);
  const [photoPrompt, setPhotoPrompt] = useState("");
  const [photoStatus, setPhotoStatus] = useState<{
    status: "idle" | "starting" | "started" | "error";
    message: string | null;
    requestId: string | null;
    logPath: string | null;
  }>({
    status: "idle",
    message: null,
    requestId: null,
    logPath: null,
  });

  const handlePhotoGenerate = useCallback(async () => {
    const trimmedPrompt = photoPrompt.trim();
    if (photoFiles.length === 0 || photoStatus.status === "starting") {
      return;
    }

    setPhotoStatus({
      status: "starting",
      message: "Enhancing prompt from photos and starting generation...",
      requestId: null,
      logPath: null,
    });

    try {
      if (photoFiles.length > MAX_REFERENCE_PHOTOS) {
        throw new Error(`Use at most ${MAX_REFERENCE_PHOTOS} reference photos.`);
      }
      const images = await Promise.all(
        photoFiles.map(async (photoFile) => ({
          imageData: await readFileAsBase64(photoFile),
          imageFilename: photoFile.name,
          imageContentType: photoFile.type || "application/octet-stream",
        })),
      );
      const result = await generateFromPhoto({
        prompt: trimmedPrompt,
        images,
      });
      setPhotoStatus({
        status: "started",
        message: result.message,
        requestId: result.request_id,
        logPath: result.log_path,
      });
      await queryClient.invalidateQueries({ queryKey: viewerQueryKeys.root() });
    } catch (error) {
      setPhotoStatus({
        status: "error",
        message: error instanceof Error ? error.message : "Failed to start photo generation.",
        requestId: null,
        logPath: null,
      });
    }
  }, [photoFiles, photoPrompt, photoStatus.status, queryClient]);

  const handlePhotoDialogOpenChange = useCallback((open: boolean) => {
    setPhotoDialogOpen(open);
    if (!open) {
      setPhotoStatus({
        status: "idle",
        message: null,
        requestId: null,
        logPath: null,
      });
    }
  }, []);

  const resetPhotoStatus = useCallback(() => {
    setPhotoStatus({
      status: "idle",
      message: null,
      requestId: null,
      logPath: null,
    });
  }, []);

  const handlePhotoFilesSelected = useCallback((files: FileList | null) => {
    const selectedFiles = Array.from(files ?? []);
    if (selectedFiles.length === 0) {
      return;
    }

    setPhotoFiles((currentFiles) => {
      const nextFiles = [...currentFiles];
      const existingKeys = new Set(
        currentFiles.map((file) => `${file.name}:${file.size}:${file.lastModified}`),
      );

      for (const file of selectedFiles) {
        if (nextFiles.length >= MAX_REFERENCE_PHOTOS) {
          break;
        }

        const fileKey = `${file.name}:${file.size}:${file.lastModified}`;
        if (!existingKeys.has(fileKey)) {
          nextFiles.push(file);
          existingKeys.add(fileKey);
        }
      }

      return nextFiles;
    });
    resetPhotoStatus();
  }, [resetPhotoStatus]);

  const removePhotoFile = useCallback((index: number) => {
    setPhotoFiles((currentFiles) => currentFiles.filter((_, fileIndex) => fileIndex !== index));
    resetPhotoStatus();
  }, [resetPhotoStatus]);

  return (
    <>
      <header className="flex h-11 shrink-0 items-center gap-3 border-b border-[var(--border-default)] bg-[var(--surface-0)] px-4">
        <div className="flex items-center gap-2 text-[12px]">
          <span className="font-semibold tracking-[-0.02em] text-[var(--text-primary)]">Articraft</span>
          <span className="text-[var(--border-strong)]">/</span>
          <span className="text-[var(--text-tertiary)]">Dashboard</span>
        </div>

        <div className="mx-1 flex min-w-0 flex-1 items-center justify-center gap-2" />

        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setPhotoDialogOpen(true)}
            className="h-7 gap-1 rounded-md px-2 text-[11px] text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
          >
            <ImagePlus className="size-3" />
            Photo
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigateTo({ page: "viewer" })}
            className="h-7 gap-1 rounded-md px-2 text-[11px] text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
          >
            Viewer
            <ChevronRight className="size-3" />
          </Button>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => window.dispatchEvent(new Event(DASHBOARD_REFRESH_EVENT))}
                className="h-7 w-7 rounded-md p-0 text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
              >
                <RefreshCw className="size-3.5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom">Refresh</TooltipContent>
          </Tooltip>
        </div>
      </header>

      <Dialog open={photoDialogOpen} onOpenChange={handlePhotoDialogOpenChange}>
        <DialogContent className="w-[min(520px,calc(100vw-32px))] p-4">
          <div className="flex items-start justify-between gap-3">
            <DialogHeader>
              <DialogTitle>Create From Photo</DialogTitle>
              <DialogDescription>Use one or more real photos as references for a new articulated object.</DialogDescription>
            </DialogHeader>
            <DialogClose />
          </div>

          <div className="mt-4 grid gap-3">
            <div className="grid gap-1.5">
              <Label htmlFor="photo-reference" className="text-[12px] text-[var(--text-secondary)]">
                Reference Photos
              </Label>
              <div className="flex items-center gap-2">
                <Input
                  ref={photoInputRef}
                  id="photo-reference"
                  type="file"
                  multiple
                  accept="image/png,image/jpeg,image/webp"
                  disabled={photoStatus.status === "starting"}
                  className="hidden"
                  onChange={(event) => {
                    handlePhotoFilesSelected(event.target.files);
                    event.target.value = "";
                  }}
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={photoStatus.status === "starting" || photoFiles.length >= MAX_REFERENCE_PHOTOS}
                  onClick={() => photoInputRef.current?.click()}
                  className="h-8 gap-1 px-3 text-[12px]"
                >
                  <ImagePlus className="size-3" />
                  Add photos
                </Button>
                {photoFiles.length > 0 ? (
                  <span className="text-[11px] text-[var(--text-tertiary)]">
                    {photoFiles.length}/{MAX_REFERENCE_PHOTOS} selected
                  </span>
                ) : null}
              </div>
              {photoFiles.length > 0 ? (
                <div className="grid max-h-28 gap-1 overflow-y-auto rounded-md border border-[var(--border-default)] bg-[var(--surface-1)] p-1">
                  {photoFiles.map((file, index) => (
                    <div
                      key={`${file.name}:${file.size}:${file.lastModified}`}
                      className="flex min-h-7 items-center gap-2 rounded px-2 text-[11px] text-[var(--text-secondary)]"
                    >
                      <span className="w-5 shrink-0 text-[var(--text-tertiary)]">{index + 1}</span>
                      <span className="min-w-0 flex-1 truncate" title={file.name}>
                        {file.name}
                      </span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        disabled={photoStatus.status === "starting"}
                        onClick={() => removePhotoFile(index)}
                        className="h-6 w-6 shrink-0 rounded p-0 text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
                      >
                        <X className="size-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[11px] text-[var(--text-tertiary)]">
                  Add up to {MAX_REFERENCE_PHOTOS} photos. You can add them one at a time.
                </p>
              )}
            </div>

            <div className="grid gap-1.5">
              <Label htmlFor="photo-prompt" className="text-[12px] text-[var(--text-secondary)]">
                Brief Prompt
              </Label>
              <textarea
                id="photo-prompt"
                value={photoPrompt}
                disabled={photoStatus.status === "starting"}
                onChange={(event) => {
                  setPhotoPrompt(event.target.value);
                  setPhotoStatus({
                    status: "idle",
                    message: null,
                    requestId: null,
                    logPath: null,
                  });
                }}
                placeholder="A short note is enough, e.g. make the hinge open from closed to fully open."
                className="min-h-24 w-full resize-y rounded-md border border-[var(--border-default)] bg-[var(--surface-0)] px-2.5 py-2 text-[12px] text-[var(--text-primary)] outline-none transition-all duration-150 placeholder:text-[var(--text-quaternary)] focus-visible:border-[var(--accent)] focus-visible:ring-2 focus-visible:ring-[var(--accent-soft)] disabled:opacity-40"
              />
            </div>

            {photoStatus.message ? (
              <div
                className={`rounded-md border px-3 py-2 text-[11px] ${
                  photoStatus.status === "error"
                    ? "border-red-500/30 bg-red-500/5 text-red-500"
                    : "border-[var(--border-default)] bg-[var(--surface-1)] text-[var(--text-secondary)]"
                }`}
              >
                <p>{photoStatus.message}</p>
                {photoStatus.requestId ? (
                  <p className="mt-1 font-mono text-[10px] text-[var(--text-tertiary)]">
                    {photoStatus.requestId}
                  </p>
                ) : null}
                {photoStatus.logPath ? (
                  <p className="mt-1 truncate font-mono text-[10px] text-[var(--text-quaternary)]" title={photoStatus.logPath}>
                    {photoStatus.logPath}
                  </p>
                ) : null}
              </div>
            ) : null}

            <div className="flex justify-end gap-2 pt-1">
              <Button
                variant="ghost"
                size="sm"
                className="h-8 px-3 text-[12px]"
                disabled={photoStatus.status === "starting"}
                onClick={() => setPhotoDialogOpen(false)}
              >
                Close
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={handlePhotoGenerate}
                disabled={photoFiles.length === 0 || photoStatus.status === "starting"}
                className="h-8 gap-1 px-3 text-[12px]"
              >
                {photoStatus.status === "starting" ? (
                  <LoaderCircle className="size-3 animate-spin" />
                ) : (
                  <ImagePlus className="size-3" />
                )}
                Start
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

export function AppHeader(): JSX.Element {
  const route = useRoute();
  return route.page === "dashboard" ? <DashboardHeaderContents /> : <ViewerHeaderContents />;
}
