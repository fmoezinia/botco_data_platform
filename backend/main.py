from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import time
import uuid
from routes import router
from scenario_service import scan_video_directory
from sam2visualizations import create_simple_visualization
from typing import Dict, Any, Optional, List
from pydantic import BaseModel

# Create FastAPI app
app = FastAPI(title="Botco Data Platform API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files with custom handler for videos
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import mimetypes

@app.get("/static/{path:path}")
async def serve_static_file(path: str):
    """Serve static files with proper headers"""
    file_path = os.path.join("data", path)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
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

# Custom video endpoint with proper headers
@app.get("/video/{path:path}")
@app.head("/video/{path:path}")
async def serve_video(path: str):
    """Serve video files with proper Content-Type and CORS headers"""
    video_path = os.path.join("data", "videos", path)
    
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")
    
    if not video_path.endswith('.mp4'):
        raise HTTPException(status_code=400, detail="Only MP4 files are supported")
    
    return FileResponse(
        video_path,
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Type": "video/mp4",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Cache-Control": "public, max-age=3600"
        }
    )

# Include routes
app.include_router(router)

# SAM2 AI Models and Data
from task_manager import TaskStatus, task_manager

class ProcessVideoRequest(BaseModel):
    video_relative_path: str
    prompts: Optional[List[Dict[str, Any]]] = None
    mode: Optional[str] = "automatic_mask_generator"  # "automatic_mask_generator" or "video_predictor"

# Import and initialize SAM2 model
try:
    from sam2hiera_service import Sam2HieraTinyModel, _sam2_video_processing_task
    
    # Initialize SAM2 model
    print("Initializing SAM2-Hiera-Tiny model...")
    ai_model = Sam2HieraTinyModel()
    SAM2_AVAILABLE = ai_model.model_available if hasattr(ai_model, 'model_available') else True
    print(f"SAM2 model initialization completed. Available: {SAM2_AVAILABLE}")
except Exception as e:
    print(f"SAM2 model initialization failed: {e}")
    ai_model = None
    SAM2_AVAILABLE = False

# SAM2 AI Endpoints
@app.post("/ai/process-video")
async def process_video_ai(request: ProcessVideoRequest):
    """Start AI processing for a video"""
    if not SAM2_AVAILABLE:
        raise HTTPException(status_code=503, detail="SAM2 AI service is not available")
    
    # Create task using the task manager
    task_id = task_manager.create_task(
        _sam2_video_processing_task,
        request.video_relative_path,
        request.prompts,
        request.mode
    )
    
    print(f"Real SAM2 processing started for video: {request.video_relative_path}")
    return {"message": "SAM2 processing started", "task_id": task_id}

@app.get("/ai/task-status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get AI task status"""
    task = task_manager.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task

@app.get("/ai/tasks", response_model=List[TaskStatus])
async def list_tasks():
    """List all AI tasks"""
    return task_manager.list_tasks()

@app.post("/ai/kill-task/{task_id}")
async def kill_task(task_id: str):
    """Manually kill a running task"""
    success = task_manager.kill_task(task_id)
    if success:
        return {"message": f"Task {task_id} killed successfully"}
    else:
        raise HTTPException(status_code=404, detail="Task not found")

@app.post("/ai/generate-visualization/{task_id}")
async def generate_visualization(task_id: str):
    """Generate a visualization video from completed SAM2 results"""
    task = task_manager.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Task not completed yet")
    
    try:
        # Generate visualization using the new module
        result = create_simple_visualization(task_id, task.result)
        return {"message": "Visualization generated successfully", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Visualization generation failed: {str(e)}")

# Initialize data on startup
@app.on_event("startup")
async def startup_event():
    print("Scanning video directory...")
    scenarios = scan_video_directory()
    print(f"Found {len(scenarios)} scenarios with total episodes: {sum(s.total_episodes for s in scenarios)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)