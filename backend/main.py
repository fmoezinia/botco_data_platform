from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import time
import uuid
from routes import router
from scenario_service import scan_video_directory
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

# Mount static files
app.mount("/static", StaticFiles(directory="data"), name="static")

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
class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: float = 0.0
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

class ProcessVideoRequest(BaseModel):
    video_relative_path: str
    prompts: Optional[List[Dict[str, Any]]] = None

# Simple in-memory task storage
ai_tasks: Dict[str, TaskStatus] = {}

# SAM2 AI Endpoints
@app.post("/ai/process-video")
async def process_video_ai(request: ProcessVideoRequest):
    """Start AI processing for a video"""
    task_id = str(uuid.uuid4())
    ai_tasks[task_id] = TaskStatus(
        task_id=task_id, 
        status="PENDING", 
        progress=0.0,
        started_at=time.time()
    )
    
    # For now, just simulate processing
    # In a real implementation, this would start the SAM2 processing
    print(f"AI processing started for video: {request.video_relative_path}")
    
    return {"message": "SAM2 processing started", "task_id": task_id}

@app.get("/ai/task-status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """Get AI task status"""
    task = ai_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Simulate progress for demo
    if task.status == "PENDING":
        task.status = "RUNNING"
        task.progress = 0.3
    elif task.status == "RUNNING" and task.progress < 0.9:
        task.progress += 0.1
    elif task.status == "RUNNING":
        task.status = "COMPLETED"
        task.progress = 1.0
        task.completed_at = time.time()
    
    return task

@app.get("/ai/tasks", response_model=List[TaskStatus])
async def list_tasks():
    """List all AI tasks"""
    return list(ai_tasks.values())

# Initialize data on startup
@app.on_event("startup")
async def startup_event():
    print("Scanning video directory...")
    scenarios = scan_video_directory()
    print(f"Found {len(scenarios)} scenarios with total episodes: {sum(s.total_episodes for s in scenarios)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)