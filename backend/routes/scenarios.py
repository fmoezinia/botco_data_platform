"""
Scenario-related API routes.
"""
import math
import random
from typing import List
from fastapi import APIRouter, HTTPException

from models import Scenario, Scene, Episode, APIResponse
from services.scenario_service import scenario_service
from utils.logging import logger

router = APIRouter()


@router.get("/", response_model=APIResponse)
async def get_scenarios():
    """Get all scenarios."""
    try:
        scenarios = scenario_service.get_scenarios()
        return APIResponse(
            success=True,
            message=f"Found {len(scenarios)} scenarios",
            data=[scenario.model_dump() for scenario in scenarios]
        )
    except Exception as e:
        logger.error(f"Failed to get scenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{scenario_id}", response_model=APIResponse)
async def get_scenario(scenario_id: str):
    """Get specific scenario."""
    try:
        scenario = scenario_service.get_scenario(scenario_id)
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        
        return APIResponse(
            success=True,
            message="Scenario retrieved successfully",
            data=scenario.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scenario {scenario_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{scenario_id}/scenes", response_model=APIResponse)
async def get_scenes(scenario_id: str):
    """Get scenes for a scenario."""
    try:
        scenes = scenario_service.get_scenes(scenario_id)
        return APIResponse(
            success=True,
            message=f"Found {len(scenes)} scenes",
            data=[scene.model_dump() for scene in scenes]
        )
    except Exception as e:
        logger.error(f"Failed to get scenes for scenario {scenario_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{scenario_id}/scenes/{scene_id}/episodes", response_model=APIResponse)
async def get_episodes(scenario_id: str, scene_id: str):
    """Get episodes for a scene."""
    try:
        episodes = scenario_service.get_episodes(scenario_id, scene_id)
        return APIResponse(
            success=True,
            message=f"Found {len(episodes)} episodes",
            data=[episode.model_dump() for episode in episodes]
        )
    except Exception as e:
        logger.error(f"Failed to get episodes for scene {scenario_id}/{scene_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{scenario_id}/scenes/{scene_id}/episodes/{episode_id}", response_model=APIResponse)
async def get_episode(scenario_id: str, scene_id: str, episode_id: str):
    """Get specific episode."""
    try:
        episode = scenario_service.get_episode(episode_id, scenario_id, scene_id)
        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")
        
        # Get frames for this episode
        frames = scenario_service.get_episode_frames(episode.file_path)
        episode_data = episode.model_dump()
        episode_data['frames'] = frames
        
        return APIResponse(
            success=True,
            message="Episode retrieved successfully",
            data=episode_data
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get episode {scenario_id}/{scene_id}/{episode_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/episodes/{episode_path:path}/data", response_model=APIResponse)
async def get_episode_data(episode_path: str):
    """Get episode data for visualization."""
    try:
        # For now, return mock data similar to the image
        # In a real implementation, this would read from actual episode data files
        
        # Generate mock data similar to the attached image
        data_points = []
        time_points = 100  # 100 data points from 0 to 8 seconds
        
        for i in range(time_points):
            time = (i / time_points) * 8
            
            # Generate data similar to the image
            left_waist = {
                "observation_state": -0.01 + math.sin(time * 0.5) * 0.005,
                "action": -0.01 + math.sin(time * 0.5) * 0.005 + (random.random() - 0.5) * 0.002
            }
            
            left_forearm_roll = {
                "observation_state": 0 if time < 1 else -0.135 * (time - 1) / 2 if time < 3 else -0.135 if time < 6 else -0.135 + 0.065 * (time - 6) / 2,
                "action": 0 if time < 1 else -0.135 * (time - 1) / 2 if time < 3 else -0.135 if time < 6 else -0.135 + 0.065 * (time - 6) / 2
            }
            
            left_wrist_rotate = {
                "observation_state": 0.045 * time / 2 if time < 2 else 0.045 - 0.18 * (time - 2) / 4 if time < 6 else 0.045 - 0.18 + 0.155 * (time - 6) / 2,
                "action": 0.045 * time / 2 if time < 2 else 0.045 - 0.18 * (time - 2) / 4 if time < 6 else 0.045 - 0.18 + 0.155 * (time - 6) / 2
            }
            
            data_points.append({
                "time": time,
                "left_waist": left_waist,
                "left_forearm_roll": left_forearm_roll,
                "left_wrist_rotate": left_wrist_rotate
            })
        
        return APIResponse(
            success=True,
            message="Episode data retrieved successfully",
            data={
                "data_points": data_points,
                "episode_path": episode_path,
                "note": "Mock data generated for visualization"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get episode data for {episode_path}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
