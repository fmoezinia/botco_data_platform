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
# Task manager import removed - using simple in-memory task_results dictionary
# SAM2 service import removed - using sam2hiera_service.py directly
from services.scenario_service import scenario_service
from sam2hiera_service import _sam2_video_processing_task
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
        # SAM2 service is initialized automatically when imported
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
    print(f"🔍 Static file request: {path}")
    print(f"   Full path: {file_path}")
    print(f"   File exists: {os.path.exists(file_path)}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
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

# Simple file-based task storage for persistence
import json
TASK_RESULTS_FILE = "task_results.json"

def load_task_results():
    """Load task results from file."""
    try:
        if os.path.exists(TASK_RESULTS_FILE):
            with open(TASK_RESULTS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading task results: {e}")
    return {}

def save_task_results():
    """Save task results to file."""
    try:
        with open(TASK_RESULTS_FILE, 'w') as f:
            json.dump(task_results, f, indent=2)
    except Exception as e:
        print(f"Error saving task results: {e}")

task_results = load_task_results()

# Original working AI endpoints (before refactor)
@app.post("/api/v1/ai/process-video")
async def process_video(request: ProcessVideoRequest):
    """Process video with SAM2 - original working version."""
    try:
        import uuid
    
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Simple progress callback that updates task status
        def progress_callback(progress: float):
            logger.info(f"Task {task_id} progress: {progress:.1%}")
            # Update task status in our persistent storage
            if task_id in task_results:
                task_results[task_id]["status"] = "RUNNING"
                task_results[task_id]["progress"] = progress
                save_task_results()
        
        # Start processing in background
        import asyncio
        asyncio.create_task(_process_video_original(task_id, request, progress_callback))
        
        return {
            "success": True,
            "message": "Video processing started",
            "data": {"task_id": task_id}
        }
        
    except Exception as e:
        logger.error(f"Failed to start video processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _process_video_original(task_id: str, request: ProcessVideoRequest, progress_callback):
    """Original video processing task."""
    try:
        import time
        
        # Store initial task status
        task_results[task_id] = {
            "task_id": task_id,
            "status": "RUNNING",
            "progress": 0.0,
            "result": None,
            "error": None,
            "started_at": time.time(),
            "completed_at": None
        }
        save_task_results()
        
        # Process video using original working function
        result = _sam2_video_processing_task(
            task_id=task_id,
            progress_callback=progress_callback,
            relative_video_path=request.video_relative_path,
            prompts=request.prompts,
            mode=request.mode
        )
        
        # Print visualization path for debugging
        print(f"🎥 Task {task_id} completed successfully!")
        print(f"📊 Result type: {type(result)}")
        if isinstance(result, dict):
            print(f"🔑 Result keys: {list(result.keys())}")
            if 'visualization' in result:
                viz_data = result['visualization']
                print(f"🎬 Visualization data: {viz_data}")
                if isinstance(viz_data, dict) and 'visualization_path' in viz_data:
                    print(f"📁 VISUALIZATION PATH: {viz_data['visualization_path']}")
                else:
                    print(f"❌ No visualization_path found in: {viz_data}")
            else:
                print(f"❌ No 'visualization' key found in result")
        else:
            print(f"❌ Result is not a dict: {result}")
        
        # Store completed task status
        task_results[task_id] = {
            "task_id": task_id,
            "status": "COMPLETED",
            "progress": 1.0,
            "result": result,
            "error": None,
            "started_at": task_results[task_id]["started_at"],
            "completed_at": time.time()
        }
        save_task_results()
        
        logger.info(f"Video processing completed for task {task_id}")
        
    except Exception as e:
        # Store failed task status
        if task_id in task_results:
            task_results[task_id]["status"] = "FAILED"
            task_results[task_id]["error"] = str(e)
            task_results[task_id]["completed_at"] = time.time()
        else:
            task_results[task_id] = {
                "task_id": task_id,
                "status": "FAILED",
                "progress": 0.0,
                "result": None,
                "error": str(e),
                "started_at": time.time(),
                "completed_at": time.time()
            }
        save_task_results()
        logger.error(f"Video processing failed for task {task_id}: {e}")

@app.get("/api/v1/ai/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get task status - original working version."""
    if task_id in task_results:
        task_data = task_results[task_id]
        print(f"📋 Task {task_id} status: {task_data.get('status')}")
        return {
            "success": True,
            "message": "Task status retrieved",
            "data": task_data
        }
    else:
        print(f"Task {task_id} not found in task_results")
        # Return pending status for unknown tasks
        return {
            "success": True,
            "message": "Task status retrieved",
            "data": {
                "task_id": task_id,
                "status": "PENDING",
                "progress": 0.0,
                "result": None,
                "error": None,
                "started_at": None,
                "completed_at": None
            }
        }

# Debug endpoint to check all tasks
@app.get("/debug/tasks")
async def debug_tasks():
    """Debug endpoint to see all tasks."""
    return {
        "task_count": len(task_results),
        "tasks": list(task_results.keys()),
        "task_data": task_results
    }

# Test endpoint to simulate task completion
@app.post("/debug/test-task/{task_id}")
async def test_task_completion(task_id: str):
    """Test endpoint to manually set a task as completed."""
    if task_id in task_results:
        task_results[task_id]["status"] = "COMPLETED"
        task_results[task_id]["progress"] = 1.0
        save_task_results()
        return {"message": f"Task {task_id} marked as completed"}
    else:
        return {"error": f"Task {task_id} not found"}

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
    video_path = os.path.join(settings.data_dir, "videos", path)
    
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail=f"Video not found: {path}")
    
    # Check if it's a video file
    if not video_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(status_code=400, detail="Invalid video format")
    
    # Return file response with proper headers
    return FileResponse(
        video_path,
        media_type="video/mp4",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Accept-Ranges": "bytes"
        }
    )


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