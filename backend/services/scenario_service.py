"""
Scenario service for managing robotics data scenarios.
"""
import os
import logging
import random
from typing import List, Dict, Any, Optional
from pathlib import Path

from config import settings
from utils.logging import logger
from models import Scenario, Scene, Episode
from exceptions import FileNotFoundError, ValidationError

# Random physical tasks for scene descriptions
PHYSICAL_TASKS = [
    "Picking up and placing a small object on a flat counter",
    "Opening and closing a drawer with precise positioning",
    "Manipulating a cylindrical object to fit into a narrow opening",
    "Stacking multiple objects in a specific order",
    "Pouring liquid from one container to another",
    "Twisting and turning a threaded object to secure it",
    "Pushing and pulling a sliding mechanism",
    "Grasping and moving objects of varying weights",
    "Aligning and fitting objects together precisely",
    "Lifting and rotating objects to inspect all sides",
    "Pressing buttons or switches in sequence",
    "Rolling objects along a surface with controlled force",
    "Balancing objects on top of each other",
    "Squeezing and releasing objects with varying pressure",
    "Sliding objects into tight spaces",
    "Rotating objects to find optimal orientation",
    "Transferring objects between different containers",
    "Adjusting the position of objects with fine motor control",
    "Combining multiple objects to create a larger structure",
    "Manipulating flexible objects without damaging them"
]


class ScenarioService:
    """Service for managing scenarios, scenes, and episodes."""
    
    def __init__(self):
        """Initialize scenario service."""
        self.videos_dir = Path(settings.videos_dir)
        self.scenarios_cache: Dict[str, Scenario] = {}
        logger.info(f"Scenario service initialized with videos directory: {self.videos_dir}")
    
    def scan_video_directory(self) -> List[Scenario]:
        """Scan video directory and build scenario hierarchy."""
        if not self.videos_dir.exists():
            logger.warning(f"Videos directory does not exist: {self.videos_dir}")
            return []
        
        scenarios = []
        logger.info("Scanning video directory for scenarios...")
        
        try:
            # Scan for scenarios (top-level directories)
            for scenario_dir in self.videos_dir.iterdir():
                if scenario_dir.is_dir() and not scenario_dir.name.startswith('.'):
                    scenario = self._build_scenario(scenario_dir)
                    if scenario:
                        scenarios.append(scenario)
                        self.scenarios_cache[scenario.id] = scenario
            
            logger.info(f"Found {len(scenarios)} scenarios")
            return scenarios
            
        except Exception as e:
            logger.error(f"Failed to scan video directory: {e}")
            raise FileNotFoundError(f"Failed to scan video directory: {str(e)}")
    
    def _build_scenario(self, scenario_dir: Path) -> Optional[Scenario]:
        """Build scenario from directory."""
        try:
            scenario_id = scenario_dir.name
            total_scenes = 0
            total_episodes = 0
            
            # Count scenes and episodes
            for item in scenario_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    total_scenes += 1
                    # Count episodes in scene
                    for episode_item in item.iterdir():
                        if episode_item.is_dir() and not episode_item.name.startswith('.'):
                            total_episodes += 1
            
            scenario = Scenario(
                id=scenario_id,
                name=scenario_id.replace('_', ' ').title(),
                description=f"Robotics scenario: {scenario_id}",
                total_scenes=total_scenes,
                total_episodes=total_episodes
            )
            
            return scenario
            
        except Exception as e:
            logger.error(f"Failed to build scenario from {scenario_dir}: {e}")
            return None
    
    def get_scenarios(self) -> List[Scenario]:
        """Get all scenarios."""
        if not self.scenarios_cache:
            self.scan_video_directory()
        return list(self.scenarios_cache.values())
    
    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """Get scenario by ID."""
        if scenario_id not in self.scenarios_cache:
            # Try to scan and find the scenario
            self.scan_video_directory()
        
        return self.scenarios_cache.get(scenario_id)
    
    def get_scenes(self, scenario_id: str) -> List[Scene]:
        """Get scenes for a scenario."""
        scenario_dir = self.videos_dir / scenario_id
        if not scenario_dir.exists():
            raise FileNotFoundError(f"Scenario not found: {scenario_id}")
        
        scenes = []
        try:
            for scene_dir in scenario_dir.iterdir():
                if scene_dir.is_dir() and not scene_dir.name.startswith('.'):
                    episode_count = 0
                    for episode_dir in scene_dir.iterdir():
                        if episode_dir.is_dir() and not episode_dir.name.startswith('.'):
                            episode_count += 1
                    
                    # Assign a random physical task description
                    task_description = random.choice(PHYSICAL_TASKS)
                    
                    scene = Scene(
                        id=scene_dir.name,
                        name=scene_dir.name.replace('_', ' ').title(),
                        scenario_id=scenario_id,
                        episode_count=episode_count,
                        description=task_description
                    )
                    scenes.append(scene)
            
            return scenes
            
        except Exception as e:
            logger.error(f"Failed to get scenes for scenario {scenario_id}: {e}")
            raise FileNotFoundError(f"Failed to get scenes: {str(e)}")
    
    def get_episodes(self, scenario_id: str, scene_id: str) -> List[Episode]:
        """Get episodes for a scene."""
        scene_dir = self.videos_dir / scenario_id / scene_id
        if not scene_dir.exists():
            raise FileNotFoundError(f"Scene not found: {scenario_id}/{scene_id}")
        
        episodes = []
        try:
            # Look for video files directly in the scene directory
            for file in scene_dir.iterdir():
                if file.is_file() and file.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv']:
                    episode_id = file.stem  # episode_0.mp4 -> episode_0
                    episode = Episode(
                        id=episode_id,
                        name=episode_id.replace('_', ' ').title(),
                        scenario_id=scenario_id,
                        scene_id=scene_id,
                        file_path=str(file.relative_to(self.videos_dir))
                    )
                    episodes.append(episode)
            
            return episodes
            
        except Exception as e:
            logger.error(f"Failed to get episodes for scene {scenario_id}/{scene_id}: {e}")
            raise FileNotFoundError(f"Failed to get episodes: {str(e)}")
    
    def get_episode(self, episode_id: str, scenario_id: str, scene_id: str) -> Optional[Episode]:
        """Get specific episode."""
        episodes = self.get_episodes(scenario_id, scene_id)
        for episode in episodes:
            if episode.id == episode_id:
                return episode
        return None
    
    def get_episode_frames(self, episode_path: str) -> List[str]:
        """Get frame files for an episode."""
        episode_dir = self.videos_dir / episode_path
        if not episode_dir.exists():
            raise FileNotFoundError(f"Episode directory not found: {episode_path}")
        
        frames = []
        try:
            for frame_file in episode_dir.iterdir():
                if frame_file.is_file() and frame_file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    frames.append(frame_file.name)
            
            frames.sort()
            return frames
            
        except Exception as e:
            logger.error(f"Failed to get frames for episode {episode_path}: {e}")
            raise FileNotFoundError(f"Failed to get frames: {str(e)}")


# Global scenario service instance
scenario_service = ScenarioService()
