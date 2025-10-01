"""
Scenario-related API routes.
"""
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
