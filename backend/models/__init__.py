"""
Data models for the Botco Data Platform.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ProcessingMode(str, Enum):
    """SAM2 processing mode enumeration."""
    AUTOMATIC_MASK_GENERATOR = "automatic_mask_generator"
    VIDEO_PREDICTOR = "video_predictor"


class Scenario(BaseModel):
    """Scenario data model."""
    id: str = Field(..., description="Unique scenario identifier")
    name: str = Field(..., description="Scenario name")
    description: Optional[str] = Field(None, description="Scenario description")
    total_scenes: int = Field(0, description="Total number of scenes")
    total_episodes: int = Field(0, description="Total number of episodes")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Scene(BaseModel):
    """Scene data model."""
    id: str = Field(..., description="Unique scene identifier")
    name: str = Field(..., description="Scene name")
    scenario_id: str = Field(..., description="Parent scenario ID")
    episode_count: int = Field(0, description="Number of episodes in this scene")
    description: str = Field("", description="Physical task description for this scene")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Episode(BaseModel):
    """Episode data model."""
    id: str = Field(..., description="Unique episode identifier")
    name: str = Field(..., description="Episode name")
    scenario_id: str = Field(..., description="Parent scenario ID")
    scene_id: str = Field(..., description="Parent scene ID")
    file_path: str = Field(..., description="Path to video file")
    duration: Optional[float] = Field(None, description="Video duration in seconds")
    frame_count: Optional[int] = Field(None, description="Total number of frames")
    width: Optional[int] = Field(None, description="Video width in pixels")
    height: Optional[int] = Field(None, description="Video height in pixels")
    fps: Optional[float] = Field(None, description="Frames per second")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PromptPoint(BaseModel):
    """Prompt point for SAM2 processing."""
    type: str = Field(..., description="Type of prompt (point, box)")
    coordinates: List[float] = Field(..., description="Coordinates [x, y] or [x1, y1, x2, y2]")
    label: int = Field(..., description="Label for the prompt (1 for foreground, 0 for background)")


class Prompt(BaseModel):
    """Prompt for SAM2 processing."""
    frame_idx: int = Field(..., description="Frame index for the prompt")
    prompts: List[PromptPoint] = Field(..., description="List of prompt points")


class ProcessVideoRequest(BaseModel):
    """Request model for video processing."""
    video_relative_path: str = Field(..., description="Relative path to video file")
    prompts: Optional[List[Prompt]] = Field(None, description="Prompts for SAM2 processing")
    mode: ProcessingMode = Field(ProcessingMode.AUTOMATIC_MASK_GENERATOR, description="Processing mode")
    
    class Config:
        use_enum_values = True


class MaskData(BaseModel):
    """Mask data from SAM2 processing."""
    segmentation: List[List[bool]] = Field(..., description="Segmentation mask as 2D boolean array")
    area: int = Field(..., description="Area of the mask in pixels")
    bbox: List[float] = Field(..., description="Bounding box [x, y, width, height]")
    predicted_iou: float = Field(..., description="Predicted IoU score")
    point_coords: List[List[float]] = Field(..., description="Input point coordinates")
    stability_score: float = Field(..., description="Stability score")
    crop_box: List[float] = Field(..., description="Crop box [x, y, width, height]")


class SegmentationResult(BaseModel):
    """Segmentation result for a single frame."""
    frame_idx: int = Field(..., description="Frame index")
    object_ids: List[int] = Field(..., description="List of object IDs")
    masks: List[MaskData] = Field(..., description="List of mask data")
    timestamp: float = Field(..., description="Processing timestamp")


class ObjectTracking(BaseModel):
    """Object tracking information."""
    first_frame: int = Field(..., description="First frame where object appears")
    initial_mask: List[List[bool]] = Field(..., description="Initial mask for the object")


class ProcessingResult(BaseModel):
    """Result of SAM2 processing."""
    video_path: str = Field(..., description="Path to processed video")
    total_frames: int = Field(..., description="Total number of frames")
    segmentation_results: List[SegmentationResult] = Field(..., description="Segmentation results")
    object_tracking: Dict[int, ObjectTracking] = Field(..., description="Object tracking data")
    processing_time: float = Field(..., description="Processing completion timestamp")
    note: str = Field(..., description="Processing note or status")


class VisualizationResult(BaseModel):
    """Result of visualization generation."""
    visualization_path: str = Field(..., description="Path to visualization video")
    local_path: str = Field(..., description="Local file path")
    original_video: str = Field(..., description="Path to original video")
    total_frames: int = Field(..., description="Total number of frames")
    processed_frames: int = Field(..., description="Number of processed frames")
    segmentation_results: int = Field(..., description="Number of segmentation results")
    sam2_task_id: str = Field(..., description="SAM2 task ID")


class TaskInfo(BaseModel):
    """Task information model."""
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Task progress (0.0 to 1.0)")
    result: Optional[Any] = Field(None, description="Task result data")
    error: Optional[str] = Field(None, description="Error message if task failed")
    started_at: Optional[datetime] = Field(None, description="Task start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Task completion timestamp")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class APIResponse(BaseModel):
    """Standard API response model."""
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if any")


class HealthCheck(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }