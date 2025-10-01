"""
API routes for the Botco Data Platform.
"""
from fastapi import APIRouter
from routes.scenarios import router as scenarios_router

# Create main API router
api_router = APIRouter()

# Include sub-routers (AI routes are defined directly in main.py)
api_router.include_router(scenarios_router, prefix="/scenarios", tags=["scenarios"])
