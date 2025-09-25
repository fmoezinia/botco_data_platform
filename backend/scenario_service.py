import os
import uuid
from datetime import datetime
from typing import List, Dict
from models import Scenario, Scene, Episode
from video_utils import get_video_info

# Global storage for scenarios, scenes, episodes and annotations
scenarios_db: Dict[str, Scenario] = {}
annotations_db: List[dict] = []

def scan_video_directory():
    """Scan the videos directory and build scenarios/scenes/episodes structure"""
    # Clear existing data
    scenarios_db.clear()
    
    videos_dir = "data/videos"
    scenarios = []
    
    if not os.path.exists(videos_dir):
        print(f"Videos directory {videos_dir} not found")
        return scenarios
    
    # Step 1: Get list of scenarios
    scenario_names = []
    for item in os.listdir(videos_dir):
        item_path = os.path.join(videos_dir, item)
        if os.path.isdir(item_path):
            scenario_names.append(item)
    
    
    # Step 2: For each scenario, get list of scenes
    for scenario_name in scenario_names:
        scenario_path = os.path.join(videos_dir, scenario_name)
        scenes = []
        total_scenario_duration = 0
        total_scenario_episodes = 0
        
        # Step 3: Get scenes (subdirectories of scenario)
        for scene_item in os.listdir(scenario_path):
            scene_path = os.path.join(scenario_path, scene_item)
            if os.path.isdir(scene_path):
                # This is a scene directory (e.g., real_ur5_1, real_ur5_2, real_ur5_3)
                episodes = []
                scene_duration = 0
                
                # Step 4: Get episodes (directories in scene directory)
                scene_items = os.listdir(scene_path)
                episode_dirs = [item for item in scene_items if os.path.isdir(os.path.join(scene_path, item))]
                
                for episode_dir in episode_dirs:
                    episode_id = episode_dir  # Episode ID is the directory name (e.g., "0", "1", "2")
                    mp4_filename = f"{episode_id}.mp4"
                    mp4_path = os.path.join(scene_path, mp4_filename)
                    
                    # Check if the corresponding MP4 file exists
                    if os.path.exists(mp4_path):
                        # Get video metadata
                        video_info = get_video_info(mp4_path)
                        if video_info:
                            episode_duration = video_info['duration']
                            fps = video_info['fps']
                            width = video_info['width']
                            height = video_info['height']
                        else:
                            episode_duration = 0
                            fps = 30.0
                            width = 1920
                            height = 1080
                        
                        episode = Episode(
                            id=episode_id,
                            scene_id=scene_item,
                            name=episode_id,
                            filename=mp4_filename,
                            file_path=f"/static/videos/{scenario_name}/{scene_item}/{mp4_filename}",
                            duration=episode_duration,
                            frame_count=1,  # Each episode is one MP4 file
                            fps=fps,
                            width=width,
                            height=height,
                            created_at=datetime.now(),
                            description=f"Episode {episode_id} from scene {scene_item}"
                        )
                        episodes.append(episode)
                        scene_duration += episode_duration
                
                # Create scene if it has episodes
                if episodes:
                    scene = Scene(
                        id=scene_item,
                        scenario_id=scenario_name,
                        name=scene_item,
                        description=f"Scene {scene_item} from {scenario_name.replace('_', ' ').title()}",
                        episode_count=len(episodes),
                        total_duration=scene_duration,
                        created_at=datetime.now(),
                        episodes=episodes
                    )
                    scenes.append(scene)
                    total_scenario_duration += scene_duration
                    total_scenario_episodes += len(episodes)
        
        # Create scenario if it has scenes
        if scenes:
            scenario = Scenario(
                id=scenario_name,
                name=scenario_name.replace('_', ' ').title(),
                description=f"Dataset for {scenario_name.replace('_', ' ').title()}",
                scene_count=len(scenes),
                total_episodes=total_scenario_episodes,
                total_duration=total_scenario_duration,
                created_at=datetime.now(),
                scenes=scenes
            )
            scenarios.append(scenario)
            scenarios_db[scenario_name] = scenario
    
    return scenarios

def get_scenarios() -> List[Scenario]:
    """Get all scenarios"""
    return list(scenarios_db.values())

def get_scenario_by_id(scenario_id: str) -> Scenario:
    """Get a specific scenario by ID"""
    return scenarios_db.get(scenario_id)

def get_scenes_for_scenario(scenario_id: str) -> List[Scene]:
    """Get all scenes for a specific scenario"""
    scenario = scenarios_db.get(scenario_id)
    return scenario.scenes if scenario else []

def get_episodes_for_scene(scenario_id: str, scene_id: str) -> List[Episode]:
    """Get all episodes for a specific scene"""
    scenario = scenarios_db.get(scenario_id)
    if scenario:
        for scene in scenario.scenes:
            if scene.id == scene_id:
                return scene.episodes
    return []

def get_annotations_for_episode(episode_id: str) -> List[dict]:
    """Get all annotations for an episode"""
    return [ann for ann in annotations_db if ann["video_id"] == episode_id]

def create_annotation(annotation_data: dict):
    """Create a new annotation"""
    annotations_db.append(annotation_data)
    return annotation_data

def get_scenarios_list() -> List[str]:
    """Get list of scenario names"""
    return list(scenarios_db.keys())

def get_scenes_list(scenario_id: str) -> List[str]:
    """Get list of scene names for a scenario"""
    scenario = scenarios_db.get(scenario_id)
    if scenario:
        return [scene.id for scene in scenario.scenes]
    return []

def get_episodes_list(scenario_id: str, scene_id: str) -> List[str]:
    """Get list of episode IDs (folder names) for a scene"""
    scenario = scenarios_db.get(scenario_id)
    if scenario:
        for scene in scenario.scenes:
            if scene.id == scene_id:
                return [episode.id for episode in scene.episodes]
    return []
