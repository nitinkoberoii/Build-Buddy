from fastapi import APIRouter
from api.config import PROJECT_NAME, API_VERSION

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    """Health check endpoint for deployment & monitoring."""
    return {
        "status": "ok",
        "service": PROJECT_NAME,
        "version": API_VERSION,
    }
