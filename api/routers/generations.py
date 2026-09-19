from typing import List, Optional
from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import StreamingResponse

from api.models.generation import (
    CreateGenerationRequest,
    GenerationResponse,
    GenerationEvent,
    FileNode,
    FileContentResponse,
)
from api.services.generation_service import generation_service

router = APIRouter(prefix="/generations", tags=["Generations"])

@router.post("", response_model=GenerationResponse, status_code=status.HTTP_201_CREATED)
async def create_generation(request: CreateGenerationRequest):
    """Submits a project prompt and starts an asynchronous generation run."""
    run = generation_service.create_generation(
        prompt=request.prompt,
        model=request.model,
        attachments=request.attachments,
    )
    return run

@router.get("", response_model=List[GenerationResponse])
async def list_generations():
    """Lists all active and historical generation runs."""
    return generation_service.list_generations()

@router.get("/{generation_id}", response_model=GenerationResponse)
async def get_generation(generation_id: str):
    """Retrieves current state, plan, and errors for a generation run."""
    run = generation_service.get_generation(generation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Generation run not found")
    return run

@router.get("/{generation_id}/events")
async def stream_generation_events(generation_id: str):
    """Streams real-time progress events for a generation run via Server-Sent Events (SSE)."""
    run = generation_service.get_generation(generation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Generation run not found")

    return StreamingResponse(
        generation_service.subscribe_events(generation_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

@router.get("/{generation_id}/files", response_model=List[FileNode])
async def get_generation_files(generation_id: str):
    """Lists safe generated project workspace files."""
    run = generation_service.get_generation(generation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Generation run not found")
    return generation_service.get_file_tree(generation_id)

@router.get("/{generation_id}/files/{file_path:path}", response_model=FileContentResponse)
async def get_generation_file_content(generation_id: str, file_path: str):
    """Reads single file content from safe project workspace."""
    run = generation_service.get_generation(generation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Generation run not found")
    try:
        return generation_service.read_file_content(generation_id, file_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File '{file_path}' not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{generation_id}/download")
async def download_generation_zip(generation_id: str):
    """Downloads generated project workspace as a ZIP archive."""
    run = generation_service.get_generation(generation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Generation run not found")

    zip_bytes = generation_service.create_project_zip(generation_id)
    filename = f"buildbuddy-{generation_id[:8]}.zip"

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

@router.post("/{generation_id}/cancel")
async def cancel_generation(generation_id: str):
    """Requests cancellation of an active generation run."""
    run = generation_service.get_generation(generation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Generation run not found")

    success = generation_service.cancel_generation(generation_id)
    return {"id": generation_id, "cancelled": success}
