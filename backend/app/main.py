from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.db.init_db import init_db
from app.api.health import router as health_router

from app.api.user import router as user_router
from app.api.oauth import router as oauth_router

from app.api.organization import router as organization_router
from app.api.workspace import router as workspace_router
from app.api.documents import router as documents_router
from app.api.dashboard import router as dashboard_router
from app.api.ai import router as ai_router
from app.api.interview import router as interview_router
from app.api.knowledge_gap import router as knowledge_gap_router
from app.api.copilot import router as copilot_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Connecting to MongoDB...")
    try:
        await init_db()
        print("MongoDB Connected!")
    except Exception as e:
        print(f"Warning: Failed to connect to MongoDB - {str(e)}")
        print("App will continue to run but database operations may fail")
    yield
    print("Application shutting down...")


app = FastAPI(
    title="Operational Brain API",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, change to frontend origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)

app.include_router(
    user_router,
    prefix="/users",
    tags=["Users"]
)

app.include_router(
    organization_router,
    prefix="/organizations",
    tags=["Organizations"]
)

app.include_router(
    workspace_router,
    prefix="/workspaces",
    tags=["Workspaces"]
)

app.include_router(
    documents_router,
    prefix="/documents",
    tags=["Documents"]
)

app.include_router(
    oauth_router,
    prefix="/api/oauth",
    tags=["OAuth"]
)

app.include_router(
    dashboard_router,
    prefix="/dashboard",
    tags=["Dashboard"]
)

app.include_router(
    ai_router,
    prefix="/api/ai",
    tags=["AI Core"]
)

app.include_router(
    interview_router,
    prefix="/interview",
    tags=["Interview"]
)

app.include_router(
    knowledge_gap_router,
    prefix="/knowledge-gap",
    tags=["Knowledge Gap"]
)

app.include_router(
    copilot_router,
    prefix="/copilot",
    tags=["Industrial Intelligence Copilot"]
)