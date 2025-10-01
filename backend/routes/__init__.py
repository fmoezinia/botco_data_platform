"""
API routes for the Botco Data Platform.
"""
from fastapi import APIRouter
from routes.scenarios import router as scenarios_router
from routes.ai import router as ai_router

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(scenarios_router, prefix="/scenarios", tags=["scenarios"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
