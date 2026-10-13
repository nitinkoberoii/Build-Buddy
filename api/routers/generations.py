from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse

from api.dependencies.auth import (
    AuthContext,
    get_current_auth,
    require_modify_permission,
)
from api.models.generation import (
    CreateGenerationRequest,
    RefineGenerationRequest,
    GenerationResponse,
    GenerationEvent,
    FileNode,
    FileContentResponse,
)
from api.services.generation_service import generation_service

router = APIRouter(prefix="/generations", tags=["Generations"])


@router.post("", response_model=GenerationResponse, status_code=status.HTTP_201_CREATED)
async def create_generation(
    request: CreateGenerationRequest,
    auth: AuthContext = Depends(require_modify_permission),
):
    """Submits a project prompt and starts an asynchronous generation run under the authenticated organization."""
    run = generation_service.create_generation(
        prompt=request.prompt,
        model=request.model,
        attachments=request.attachments,
        organization_id=auth.organization.id,
        creator_id=auth.user.id,
    )
    return run


@router.post("/{generation_id}/refine", response_model=GenerationResponse)
async def refine_generation(
    generation_id: str,
    request: RefineGenerationRequest,
    auth: AuthContext = Depends(require_modify_permission),
):
    """Submits an edit/refinement prompt to an existing generation thread owned by the organization."""
    try:
        run = generation_service.refine_generation(
            generation_id=generation_id,
            prompt=request.prompt,
            organization_id=auth.organization.id,
        )
        return run
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation run not found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=List[GenerationResponse])
async def list_generations(
    auth: AuthContext = Depends(get_current_auth),
):
    """Lists all generation runs scoped to the authenticated user's organization."""
    return generation_service.list_generations(organization_id=auth.organization.id)


@router.get("/{generation_id}", response_model=GenerationResponse)
async def get_generation(
    generation_id: str,
    auth: AuthContext = Depends(get_current_auth),
):
    """Retrieves current state, plan, and errors for a generation run owned by the organization."""
    run = generation_service.get_generation(generation_id, organization_id=auth.organization.id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation run not found")
    return run


@router.get("/{generation_id}/events")
async def stream_generation_events(
    generation_id: str,
    auth: AuthContext = Depends(get_current_auth),
):
    """Streams real-time progress events for a generation run owned by the organization via SSE."""
    run = generation_service.get_generation(generation_id, organization_id=auth.organization.id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation run not found")

    return StreamingResponse(
        generation_service.subscribe_events(generation_id, organization_id=auth.organization.id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{generation_id}/files", response_model=List[FileNode])
async def get_generation_files(
    generation_id: str,
    auth: AuthContext = Depends(get_current_auth),
):
    """Lists generated project workspace files for an organization's generation."""
    try:
        return generation_service.get_file_tree(generation_id, organization_id=auth.organization.id)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation run not found")


@router.get("/{generation_id}/files/{file_path:path}", response_model=FileContentResponse)
async def get_generation_file_content(
    generation_id: str,
    file_path: str,
    auth: AuthContext = Depends(get_current_auth),
):
    """Reads single file content from the project workspace with organization boundary checks."""
    try:
        return generation_service.read_file_content(
            generation_id, file_path, organization_id=auth.organization.id
        )
    except FileNotFoundError as e:
        # Check if generation doesn't exist vs file inside generation doesn't exist
        run = generation_service.get_generation(generation_id, organization_id=auth.organization.id)
        if not run:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation run not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File '{file_path}' not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{generation_id}/download")
async def download_generation_zip(
    generation_id: str,
    auth: AuthContext = Depends(get_current_auth),
):
    """Downloads generated project workspace as a ZIP archive for authorized users."""
    try:
        zip_bytes = generation_service.create_project_zip(
            generation_id, organization_id=auth.organization.id
        )
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation run not found")

    filename = f"buildbuddy-{generation_id[:8]}.zip"
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/{generation_id}/cancel")
async def cancel_generation(
    generation_id: str,
    auth: AuthContext = Depends(require_modify_permission),
):
    """Requests cancellation of an active generation run under the authenticated organization."""
    run = generation_service.get_generation(generation_id, organization_id=auth.organization.id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation run not found")

    success = generation_service.cancel_generation(generation_id, organization_id=auth.organization.id)
    return {"id": generation_id, "cancelled": success}
