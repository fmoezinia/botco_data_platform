#!/usr/bin/env python3
"""
Initialize mock data for the Botco Data Platform
"""

from main import videos_db, annotations_db
from datetime import datetime
import uuid

def init_mock_data():
    """Initialize the database with mock video data"""
    
    # Create mock videos
    mock_videos = [
        {
            "id": str(uuid.uuid4()),
            "filename": "robot_navigation_001.mp4",
            "duration": 120.5,
            "frame_count": 3615,
            "fps": 30.0,
            "width": 1920,
            "height": 1080,
            "created_at": datetime.now()
        },
        {
            "id": str(uuid.uuid4()),
            "filename": "robot_manipulation_002.mp4", 
            "duration": 85.2,
            "frame_count": 2556,
            "fps": 30.0,
            "width": 1280,
            "height": 720,
            "created_at": datetime.now()
        },
        {
            "id": str(uuid.uuid4()),
            "filename": "robot_sensors_003.mp4",
            "duration": 200.0,
            "frame_count": 6000,
            "fps": 30.0,
            "width": 640,
            "height": 480,
            "created_at": datetime.now()
        }
    ]
    
    # Add videos to database
    for video_data in mock_videos:
        videos_db[video_data["id"]] = video_data
    
    # Create mock annotations
    mock_annotations = [
        {
            "id": str(uuid.uuid4()),
            "video_id": mock_videos[0]["id"],
            "frame_number": 150,
            "annotation_type": "bounding_box",
            "data": {
                "x": 100,
                "y": 150,
                "width": 200,
                "height": 100,
                "label": "robot_base",
                "confidence": 0.95
            },
            "timestamp": datetime.now()
        },
        {
            "id": str(uuid.uuid4()),
            "video_id": mock_videos[0]["id"],
            "frame_number": 300,
            "annotation_type": "graph",
            "data": {
                "type": "line_chart",
                "x_data": list(range(10)),
                "y_data": [1.2, 1.5, 1.8, 2.1, 2.0, 1.9, 1.7, 1.6, 1.4, 1.3],
                "title": "Velocity over time",
                "x_label": "Time (s)",
                "y_label": "Velocity (m/s)"
            },
            "timestamp": datetime.now()
        },
        {
            "id": str(uuid.uuid4()),
            "video_id": mock_videos[1]["id"],
            "frame_number": 500,
            "annotation_type": "bounding_box",
            "data": {
                "x": 300,
                "y": 200,
                "width": 150,
                "height": 80,
                "label": "gripper",
                "confidence": 0.88
            },
            "timestamp": datetime.now()
        }
    ]
    
    # Add annotations to database
    annotations_db.extend(mock_annotations)
    
    print("Initialized {} mock videos and {} mock annotations".format(len(mock_videos), len(mock_annotations)))

if __name__ == "__main__":
    init_mock_data()
    print("Mock data initialization complete!")
