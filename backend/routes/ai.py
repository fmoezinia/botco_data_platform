"""
AI processing API routes.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any

from models import ProcessVideoRequest, TaskInfo, APIResponse
from services.sam2_service import sam2_service
from services.task_manager import task_manager
from utils.logging import logger

router = APIRouter()


@router.post("/process-video", response_model=APIResponse)
async def process_video(request: ProcessVideoRequest, background_tasks: BackgroundTasks):
    """Process video with SAM2 segmentation."""
    try:
        # Create task
        task_id = task_manager.create_task("video_processing")
        
        # Start processing in background
        background_tasks.add_task(
            _process_video_task,
            task_id,
            request.video_relative_path,
            request.prompts,
            request.mode
        )
        
        return APIResponse(
            success=True,
            message="Video processing started",
            data={"task_id": task_id}
        )
        
    except Exception as e:
        logger.error(f"Failed to start video processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _process_video_task(task_id: str, video_path: str, prompts: list, mode: str):
    """Background task for video processing."""
    try:
        task_manager.update_task_status(task_id, "RUNNING", progress=0.1)
        
        # Process video with SAM2
        result = await sam2_service.process_video(video_path, prompts, mode)
        
        task_manager.update_task_status(task_id, "COMPLETED", progress=1.0, result=result.dict())
        logger.info(f"Video processing completed for task {task_id}")
        
    except Exception as e:
        error_msg = str(e)
        task_manager.update_task_status(task_id, "FAILED", error=error_msg)
        logger.error(f"Video processing failed for task {task_id}: {error_msg}")


@router.get("/tasks/{task_id}", response_model=APIResponse)
async def get_task_status(task_id: str):
    """Get task status."""
    try:
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return APIResponse(
            success=True,
            message="Task status retrieved",
            data=task.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-visualization/{task_id}", response_model=APIResponse)
async def generate_visualization(task_id: str, background_tasks: BackgroundTasks):
    """Generate visualization for a completed SAM2 task."""
    try:
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task.status != "COMPLETED":
            raise HTTPException(status_code=400, detail="Task must be completed to generate visualization")
        
        # Create visualization task
        viz_task_id = task_manager.create_task("visualization_generation")
        
        # Start visualization generation in background
        background_tasks.add_task(
            _generate_visualization_task,
            viz_task_id,
            task_id,
            task.result
        )
        
        return APIResponse(
            success=True,
            message="Visualization generation started",
            data={"task_id": viz_task_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start visualization generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _generate_visualization_task(viz_task_id: str, sam2_task_id: str, sam2_result: Dict[str, Any]):
    """Background task for visualization generation."""
    try:
        task_manager.update_task_status(viz_task_id, "RUNNING", progress=0.1)
        
        # Import visualization function
        from sam2visualizations import create_simple_visualization
        
        # Generate visualization
        viz_result = create_simple_visualization(sam2_task_id, sam2_result)
        
        task_manager.update_task_status(viz_task_id, "COMPLETED", progress=1.0, result=viz_result)
        logger.info(f"Visualization generation completed for task {viz_task_id}")
        
    except Exception as e:
        error_msg = str(e)
        task_manager.update_task_status(viz_task_id, "FAILED", error=error_msg)
        logger.error(f"Visualization generation failed for task {viz_task_id}: {error_msg}")


@router.get("/tasks", response_model=APIResponse)
async def get_all_tasks():
    """Get all tasks."""
    try:
        tasks = task_manager.get_all_tasks()
        return APIResponse(
            success=True,
            message=f"Found {len(tasks)} tasks",
            data={task_id: task.dict() for task_id, task in tasks.items()}
        )
        
    except Exception as e:
        logger.error(f"Failed to get tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
