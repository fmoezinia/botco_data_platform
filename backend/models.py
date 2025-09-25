from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Episode(BaseModel):
    id: str
    scene_id: str
    name: str
    filename: str
    file_path: str
    duration: float
    frame_count: int
    fps: float
    width: int
    height: int
    created_at: datetime
    description: Optional[str] = None

class Scene(BaseModel):
    id: str
    scenario_id: str
    name: str
    description: str
    episode_count: int
    total_duration: float
    created_at: datetime
    episodes: List[Episode]

class Scenario(BaseModel):
    id: str
    name: str
    description: str
    scene_count: int
    total_episodes: int
    total_duration: float
    created_at: datetime
    scenes: List[Scene]

class VideoMetadata(BaseModel):
    id: str
    filename: str
    duration: float
    frame_count: int
    fps: float
    width: int
    height: int
    file_path: str
    created_at: datetime

class Annotation(BaseModel):
    id: str
    video_id: str  # This refers to episode_id
    frame_number: int
    annotation_type: str
    coordinates: dict
    label: str
    confidence: float
    created_at: datetime
