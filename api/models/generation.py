from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class GenerationState(str, Enum):
    QUEUED = "queued"
    PLANNING = "planning"
    ARCHITECTING = "architecting"
    CODING = "coding"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class CreateGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=3, max_length=5000, description="Project prompt description")
    model: Optional[str] = Field(default=None, description="Allowlisted LLM model identifier")
    attachments: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional prompt attachments metadata")

class RefineGenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=5000, description="Refinement or edit prompt for the workspace")

class ThreadMessage(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str
    status: Optional[str] = None
    files_changed: Optional[List[str]] = None

class GenerationEvent(BaseModel):
    id: str
    generation_id: str
    stage: str
    message: str
    timestamp: str
    data: Optional[Dict[str, Any]] = None

class GenerationResponse(BaseModel):
    id: str
    prompt: str
    model: str
    state: GenerationState
    created_at: str
    updated_at: str
    plan: Optional[Dict[str, Any]] = None
    task_plan: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    messages: List[ThreadMessage] = Field(default_factory=list)

class FileNode(BaseModel):
    name: str
    path: str
    type: str  # "file" or "directory"
    size: Optional[int] = None
    children: Optional[List["FileNode"]] = None

FileNode.model_rebuild()

class FileContentResponse(BaseModel):
    path: str
    content: str
    size: int
