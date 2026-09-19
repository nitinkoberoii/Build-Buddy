from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import PROJECT_NAME, API_VERSION, CORS_ORIGINS
from api.routers import health, generations

app = FastAPI(
    title=PROJECT_NAME,
    version=API_VERSION,
    description="BuildBuddy Agentic AI Project Generator API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware for local Vite frontend dev server and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach routers under /api prefix and root
app.include_router(health.router, prefix="/api")
app.include_router(generations.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "name": PROJECT_NAME,
        "version": API_VERSION,
        "docs": "/docs",
        "status": "online",
    }
