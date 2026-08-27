from __future__ import annotations

from fastapi import APIRouter, HTTPException

from viewer.api.dependencies import ViewerStoreDep
from viewer.api.photo_generate import ReferencePhotoInput, start_photo_generation
from viewer.api.schemas import GenerateFromPhotoRequest, GenerateFromPhotoResponse

router = APIRouter()


@router.post("/api/generate/from-photo", response_model=GenerateFromPhotoResponse)
async def generate_from_photo(
    payload: GenerateFromPhotoRequest,
    store: ViewerStoreDep,
) -> GenerateFromPhotoResponse:
    try:
        result = start_photo_generation(
            repo_root=store.repo.root,
            prompt=payload.prompt,
            images=[
                ReferencePhotoInput(
                    image_data=image.image_data,
                    image_filename=image.image_filename,
                    image_content_type=image.image_content_type,
                )
                for image in payload.images
            ],
            image_data=payload.image_data,
            image_filename=payload.image_filename,
            image_content_type=payload.image_content_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to start photo generation: {exc}"
        ) from exc

    enhanced = result.enhanced_prompt_path is not None
    return GenerateFromPhotoResponse(
        status="started",
        request_id=result.request_id,
        prompt_path=str(result.prompt_path),
        enhanced_prompt_path=(
            str(result.enhanced_prompt_path) if result.enhanced_prompt_path is not None else None
        ),
        prompt_memory_path=(
            str(result.prompt_memory_path) if result.prompt_memory_path is not None else None
        ),
        image_path=str(result.image_path),
        image_paths=[str(path) for path in result.image_paths],
        log_path=str(result.log_path),
        message=(
            "Photo prompt enhanced and generation started. Check Staging after the run finishes."
            if enhanced
            else "Photo generation started. Check Staging after the run finishes."
        ),
    )
