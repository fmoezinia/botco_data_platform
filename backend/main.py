"""
Botco Data Platform - Main Application

A professional robotics data visualization platform with AI-powered segmentation.
"""
import os
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import mimetypes

from config import settings
from utils.logging import logger
from exceptions import BotcoException, FileNotFoundError, ServiceUnavailableError
from models import APIResponse, HealthCheck, ProcessVideoRequest, TaskInfo
from services.storage_service import storage_manager
from services.task_manager import task_manager
from services.sam2_service import sam2_service
from services.scenario_service import scenario_service
# AI routes are defined directly in main.py, scenarios router imported separately


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Botco Data Platform...")
    logger.info(f"Version: {settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Storage mode: {settings.storage_mode}")
    
    # Initialize services
    try:
        logger.info("Initializing SAM2 AI service...")
        await sam2_service.initialize()
        logger.info("SAM2 AI service initialized successfully")
    except Exception as e:
        logger.warning(f"SAM2 service initialization failed (optional): {e}")
        logger.info("Continuing without SAM2 service - AI features will be disabled")
    
    try:
        logger.info("Scanning video directory...")
        scenarios = scenario_service.scan_video_directory()
        logger.info(f"Found {len(scenarios)} scenarios with {sum(s.total_episodes for s in scenarios)} total episodes")
    except Exception as e:
        logger.error(f"Failed to scan video directory: {e}")
        raise ServiceUnavailableError("Video directory scanning failed")
    
    logger.info("Botco Data Platform started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Botco Data Platform...")
    task_manager.shutdown()
    logger.info("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A professional robotics data visualization platform with AI-powered segmentation",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(BotcoException)
async def botco_exception_handler(request: Request, exc: BotcoException):
    """Handle custom Botco exceptions."""
    logger.error(f"Botco exception: {exc.message} (Code: {exc.error_code})")
    return APIResponse(
        success=False,
        message=exc.message,
        error=exc.error_code,
        data=exc.details
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP exception: {exc.detail} (Status: {exc.status_code})")
    return APIResponse(
        success=False,
        message=exc.detail,
        error=f"HTTP_{exc.status_code}"
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return APIResponse(
        success=False,
        message="An unexpected error occurred",
        error="INTERNAL_ERROR"
    )


# Static file serving with proper headers
@app.get("/static/{path:path}")
async def serve_static_file(path: str):
    """Serve static files with proper headers."""
    file_path = os.path.join(settings.data_dir, path)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {path}")
    
    # Determine content type
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = "application/octet-stream"
    
    # Special handling for video files
    if content_type.startswith("video/"):
        return FileResponse(
            file_path,
            media_type=content_type,
            headers={
                "Accept-Ranges": "bytes",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Cache-Control": "public, max-age=3600"
            }
        )
    else:
        return FileResponse(file_path, media_type=content_type)


# Health check endpoint
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint."""
    return HealthCheck(
        status="healthy",
        timestamp=time.time(),
        version=settings.app_version,
        uptime=time.time() - start_time
    )


# Include API routes (excluding AI routes which are defined directly in main.py)
from routes.scenarios import router as scenarios_router
app.include_router(scenarios_router, prefix="/api/v1")

# AI Processing endpoints
@app.post("/api/v1/ai/process-video")
async def process_video(request: ProcessVideoRequest):
    """Process video with SAM2."""
    try:
        from sam2hiera_service import _sam2_video_processing_task
        
        # Generate a unique task ID
        import uuid
        task_id = str(uuid.uuid4())
        
        # Create a progress callback that updates task status
        def progress_callback(progress: float):
            # Update task status in task manager
            task_manager.update_task_status(task_id, "RUNNING", progress=progress)
        
        # Start processing in background
        import asyncio
        asyncio.create_task(_process_video_background(task_id, request, progress_callback))
        
        return {
            "success": True,
            "message": "Video processing started",
            "data": {"task_id": task_id}
        }
        
    except Exception as e:
        logger.error(f"Failed to start video processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _process_video_background(task_id: str, request: ProcessVideoRequest, progress_callback):
    """Background task for video processing."""
    try:
        from sam2hiera_service import _sam2_video_processing_task
        
        # Process video
        result = _sam2_video_processing_task(
            task_id=task_id,
            progress_callback=progress_callback,
            relative_video_path=request.video_relative_path,
            prompts=request.prompts,
            mode=request.mode
        )
        
        # Mark task as completed
        task_manager.update_task_status(task_id, "COMPLETED", progress=1.0, result=result)
        logger.info(f"Video processing completed for task {task_id}")
        
    except Exception as e:
        error_msg = str(e)
        task_manager.update_task_status(task_id, "FAILED", error=error_msg)
        logger.error(f"Video processing failed for task {task_id}: {error_msg}")

@app.get("/api/v1/ai/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get task status."""
    try:
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "success": True,
            "message": "Task status retrieved",
            "data": task.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Legacy endpoints for frontend compatibility
@app.get("/scenarios-list")
async def legacy_scenarios_list():
    """Legacy endpoint for scenarios list."""
    try:
        scenarios = scenario_service.get_scenarios()
        return {
            "scenarios": [scenario.id for scenario in scenarios]
        }
    except Exception as e:
        logger.error(f"Failed to get scenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
async def test_endpoint():
    """Test endpoint."""
    return {"message": "Test endpoint working"}

@app.get("/scenarios/{scenario_id}/scenes")
async def legacy_scenes_list(scenario_id: str):
    """Legacy endpoint for scenes list."""
    try:
        scenes = scenario_service.get_scenes(scenario_id)
        return {
            "scenes": [scene.id for scene in scenes],
            "scene_details": [{
                "id": scene.id,
                "name": scene.name,
                "description": scene.description,
                "episode_count": scene.episode_count
            } for scene in scenes]
        }
    except Exception as e:
        logger.error(f"Failed to get scenes for scenario {scenario_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scenarios/{scenario_id}/scenes/{scene_id}/episodes")
async def legacy_episodes_list(scenario_id: str, scene_id: str):
    """Legacy endpoint for episodes list."""
    try:
        episodes = scenario_service.get_episodes(scenario_id, scene_id)
        return {
            "episodes": [episode.id for episode in episodes]
        }
    except Exception as e:
        logger.error(f"Failed to get episodes for scene {scenario_id}/{scene_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video/{path:path}")
async def legacy_video_serve(path: str):
    """Legacy endpoint for video serving."""
    video_path = f"videos/{path}"
    return await serve_static_file(video_path)


# Store start time for uptime calculation
start_time = time.time()


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )