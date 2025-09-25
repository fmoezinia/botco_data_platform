import uuid
import time
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional, List, Tuple
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import cv2
import torch
import numpy as np
from sam2.sam2_video_predictor import SAM2VideoPredictor
from starlette.middleware.cors import CORSMiddleware

# --- Configuration ---
# Path to the directory where video files are stored on the server
# This should match the base directory used by your main backend for video assets.
VIDEO_BASE_DIR = "data/videos" 

# --- SAM2 Model ---
class Sam2HieraTinyModel:
    """
    Real SAM2-Hiera-Tiny model implementation using the official SAM2 library.
    """
    def __init__(self):
        print("Loading SAM2-Hiera-Tiny model...")
        try:
            self.predictor = SAM2VideoPredictor.from_pretrained("facebook/sam2-hiera-tiny")
            print("SAM2-Hiera-Tiny model loaded successfully.")
        except Exception as e:
            print(f"Error loading SAM2 model: {e}")
            raise e

    def process_video(self, video_path: str, prompts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process an entire video with SAM2 model.
        
        Args:
            video_path: Path to the video file
            prompts: List of prompts for segmentation (points, boxes, etc.)
        
        Returns:
            Dictionary containing segmentation results for the entire video
        """
        try:
            # Load video frames
            cap = cv2.VideoCapture(video_path)
            frames = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frames.append(frame)
            cap.release()
            
            if not frames:
                raise ValueError("No frames found in video")
            
            # Convert frames to the format expected by SAM2
            video_frames = np.array(frames)
            
            # Initialize SAM2 state with the video
            with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
                state = self.predictor.init_state(video_frames)
                
                # Process prompts
                segmentation_results = []
                object_tracking = {}
                
                # Add initial prompts
                for prompt in prompts:
                    frame_idx = prompt.get('frame_idx', 0)
                    prompt_data = prompt.get('prompts', [])
                    
                    if prompt_data:
                        frame_idx, object_ids, masks = self.predictor.add_new_points_or_box(
                            state, prompt_data
                        )
                        
                        # Store initial results
                        for obj_id, mask in zip(object_ids, masks):
                            object_tracking[obj_id] = {
                                'first_frame': frame_idx,
                                'initial_mask': mask.tolist()
                            }
                
                # Propagate through the video
                for frame_idx, object_ids, masks in self.predictor.propagate_in_video(state):
                    frame_results = {
                        'frame_idx': frame_idx,
                        'object_ids': object_ids.tolist() if hasattr(object_ids, 'tolist') else object_ids,
                        'masks': [mask.tolist() for mask in masks] if hasattr(masks[0], 'tolist') else masks,
                        'timestamp': time.time()
                    }
                    segmentation_results.append(frame_results)
                
                return {
                    'video_path': video_path,
                    'total_frames': len(frames),
                    'segmentation_results': segmentation_results,
                    'object_tracking': object_tracking,
                    'processing_time': time.time()
                }
                
        except Exception as e:
            print(f"Error processing video with SAM2: {e}")
            raise e

    def process_frame_with_prompts(self, video_path: str, frame_idx: int, prompts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a specific frame with prompts using SAM2.
        
        Args:
            video_path: Path to the video file
            frame_idx: Index of the frame to process
            prompts: List of prompts for segmentation
        
        Returns:
            Dictionary containing segmentation results for the frame
        """
        try:
            # Load video frames
            cap = cv2.VideoCapture(video_path)
            frames = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frames.append(frame)
            cap.release()
            
            if frame_idx >= len(frames):
                raise ValueError(f"Frame index {frame_idx} out of range (video has {len(frames)} frames)")
            
            # Convert frames to the format expected by SAM2
            video_frames = np.array(frames)
            
            # Initialize SAM2 state
            with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
                state = self.predictor.init_state(video_frames)
                
                # Process prompts for the specific frame
                frame_idx_result, object_ids, masks = self.predictor.add_new_points_or_box(
                    state, prompts
                )
                
                return {
                    'frame_idx': frame_idx_result,
                    'object_ids': object_ids.tolist() if hasattr(object_ids, 'tolist') else object_ids,
                    'masks': [mask.tolist() for mask in masks] if hasattr(masks[0], 'tolist') else masks,
                    'timestamp': time.time()
                }
                
        except Exception as e:
            print(f"Error processing frame with SAM2: {e}")
            raise e

# Global model instance. 
# For ThreadPoolExecutor, a single instance is generally fine if the model's
# inference method is thread-safe (which is often the case for deep learning libraries
# that release the GIL during computation).
# If using ProcessPoolExecutor, each process would load its own model instance.
ai_model: Optional[Sam2HieraTinyModel] = None
try:
    ai_model = Sam2HieraTinyModel()
except Exception as e:
    print(f"ERROR: Failed to load AI model at startup: {e}")
    print("AI processing tasks will fail until the model is successfully loaded.")

# --- Task Management ---
class TaskStatus(BaseModel):
    task_id: str
    status: str # "PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"
    progress: float = 0.0 # 0.0 to 1.0
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

# In-memory storage for tasks. 
# In a production system, this would be a persistent store like a database or Redis
# to survive service restarts and allow for more robust task management.
tasks: Dict[str, TaskStatus] = {}

# Thread pool for background processing.
# Adjust max_workers based on CPU cores, GPU availability, and model's resource usage.
# For purely CPU-bound tasks, `ProcessPoolExecutor` might be more suitable to bypass GIL.
executor = ThreadPoolExecutor(max_workers=os.cpu_count() or 4) 

# --- FastAPI Application ---
app = FastAPI(
    title="AI Video Processing Service",
    description="Service to asynchronously process videos using SAM2-Hiera-Tiny model.",
    version="1.0.0"
)

# Add CORS middleware to allow requests from your frontend (e.g., React app on localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust this to your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Function to run in the background thread
def _run_ai_processing_task(task_id: str, relative_video_path: str, prompts: List[Dict[str, Any]] = None):
    """
    Internal function executed by the ThreadPoolExecutor.
    Processes a video using the SAM2 model with optional prompts.
    """
    global ai_model # Ensure we can access the global model instance

    if ai_model is None:
        tasks[task_id].status = "FAILED"
        tasks[task_id].error = "AI model failed to load at startup or is not available."
        tasks[task_id].completed_at = time.time()
        print(f"Task {task_id}: Failed because AI model is not loaded.")
        return

    tasks[task_id].status = "RUNNING"
    tasks[task_id].started_at = time.time()
    print(f"Task {task_id}: Starting SAM2 processing for {relative_video_path}")

    full_video_path = os.path.join(VIDEO_BASE_DIR, relative_video_path)
    if not os.path.exists(full_video_path):
        tasks[task_id].status = "FAILED"
        tasks[task_id].error = f"Video file not found: {full_video_path}"
        tasks[task_id].completed_at = time.time()
        print(f"Task {task_id}: Failed - Video file not found.")
        return

    try:
        # Use default prompts if none provided
        if prompts is None:
            prompts = [
                {
                    'frame_idx': 0,
                    'prompts': [
                        # Example: point prompt at center of frame
                        {'type': 'point', 'coordinates': [320, 240], 'label': 1}
                    ]
                }
            ]
        
        # Process video with SAM2
        tasks[task_id].progress = 0.1  # Started processing
        
        result = ai_model.process_video(full_video_path, prompts)
        
        tasks[task_id].progress = 1.0
        tasks[task_id].status = "COMPLETED"
        tasks[task_id].result = result
        tasks[task_id].completed_at = time.time()
        print(f"Task {task_id}: Completed SAM2 processing for {relative_video_path}")

    except Exception as e:
        tasks[task_id].status = "FAILED"
        tasks[task_id].error = str(e)
        tasks[task_id].completed_at = time.time()
        print(f"Task {task_id}: Failed with error: {e}")

class ProcessVideoRequest(BaseModel):
    video_relative_path: str
    prompts: Optional[List[Dict[str, Any]]] = None

@app.post("/ai/process-video")
async def process_video_ai(request: ProcessVideoRequest):
    """
    Kicks off an asynchronous AI processing task for a given video with SAM2.
    The `video_relative_path` should be relative to the `VIDEO_BASE_DIR`
    (e.g., "scenario_name/scene_name/episode_name/video.mp4").
    Optional `prompts` can be provided for specific segmentation requests.
    Returns a task ID to poll for results.
    """
    if ai_model is None:
        raise HTTPException(status_code=503, detail="AI model is not loaded. Service unavailable.")

    task_id = str(uuid.uuid4())
    tasks[task_id] = TaskStatus(task_id=task_id, status="PENDING", progress=0.0)

    # Submit the task to the thread pool
    executor.submit(_run_ai_processing_task, task_id, request.video_relative_path, request.prompts)

    return {"message": "SAM2 processing started", "task_id": task_id}

@app.post("/ai/process-frame")
async def process_frame_ai(video_relative_path: str, frame_idx: int, prompts: List[Dict[str, Any]]):
    """
    Process a specific frame with SAM2 model and return immediate results.
    """
    if ai_model is None:
        raise HTTPException(status_code=503, detail="AI model is not loaded. Service unavailable.")

    full_video_path = os.path.join(VIDEO_BASE_DIR, video_relative_path)
    if not os.path.exists(full_video_path):
        raise HTTPException(status_code=404, detail=f"Video file not found: {full_video_path}")

    try:
        result = ai_model.process_frame_with_prompts(full_video_path, frame_idx, prompts)
        return {"message": "Frame processed successfully", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing frame: {str(e)}")

@app.get("/ai/task-status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    Retrieves the current status and results of an AI processing task.
    """
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.get("/ai/tasks", response_model=List[TaskStatus])
async def list_tasks():
    """
    Lists all known AI processing tasks (active, completed, failed).
    """
    return list(tasks.values())

# To run this service:
# 1. Save this code as `sam2hiera_service.py` in your backend directory.
# 2. Install dependencies: `pip install fastapi uvicorn opencv-python pydantic`
#    (Note: `opencv-python` might require system-level dependencies for video codecs)
# 3. Ensure your `data/videos` directory exists and contains video files.
# 4. Run from terminal: `uvicorn sam2hiera_service:app --host 0.0.0.0 --port 8001`
#    (It's recommended to use a different port than your main backend, e.g., 8001 vs 8000)
