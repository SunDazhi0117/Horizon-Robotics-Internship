from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from viewer.api.dependencies import ViewerStoreDep
from viewer.api.feedback_memory import append_feedback_memory, load_feedback_memory
from viewer.api.schemas import (
    FeedbackMemoryEntryResponse,
    FeedbackMemoryRequest,
    FeedbackMemoryResponse,
)

router = APIRouter()


def _to_response(entry) -> FeedbackMemoryEntryResponse:
    return FeedbackMemoryEntryResponse(
        feedback_id=entry.feedback_id,
        created_at=entry.created_at,
        record_id=entry.record_id,
        object_type=entry.object_type,
        issue_types=entry.issue_types,
        problem=entry.problem,
        fix=entry.fix,
        tags=entry.tags,
    )


@router.post("/api/feedback-memory", response_model=FeedbackMemoryResponse)
async def create_feedback_memory(
    payload: FeedbackMemoryRequest,
    store: ViewerStoreDep,
) -> FeedbackMemoryResponse:
    try:
        entry = append_feedback_memory(
            repo_root=store.repo.root,
            record_id=payload.record_id,
            object_type=payload.object_type,
            issue_types=payload.issue_types,
            problem=payload.problem,
            fix=payload.fix,
            tags=payload.tags,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {exc}") from exc
    return FeedbackMemoryResponse(status="saved", feedback=_to_response(entry))


@router.get("/api/feedback-memory", response_model=list[FeedbackMemoryEntryResponse])
async def list_feedback_memory(
    store: ViewerStoreDep,
    limit: int = Query(default=50, ge=1, le=500),
) -> list[FeedbackMemoryEntryResponse]:
    entries = load_feedback_memory(store.repo.root, limit=limit)
    return [_to_response(entry) for entry in reversed(entries[-limit:])]
