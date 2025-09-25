from fastapi import APIRouter, HTTPException
from typing import List
from models import Scenario, Scene, Episode, Annotation
from scenario_service import (
    get_scenarios, 
    get_scenario_by_id, 
    get_scenes_for_scenario,
    get_episodes_for_scene,
    get_annotations_for_episode, 
    create_annotation,
    get_scenarios_list,
    get_scenes_list,
    get_episodes_list
)

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Botco Data Platform API"}

@router.get("/scenarios", response_model=List[Scenario])
async def get_scenarios_endpoint():
    """Get list of all scenarios with episodes"""
    return get_scenarios()

@router.get("/scenarios/{scenario_id}", response_model=Scenario)
async def get_scenario_endpoint(scenario_id: str):
    """Get a specific scenario by ID"""
    scenario = get_scenario_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario

@router.get("/annotations/{episode_id}", response_model=List[Annotation])
async def get_annotations_endpoint(episode_id: str):
    """Get all annotations for an episode"""
    return get_annotations_for_episode(episode_id)

@router.post("/annotations", response_model=Annotation)
async def create_annotation_endpoint(annotation: Annotation):
    """Create a new annotation"""
    return create_annotation(annotation.dict())

@router.get("/scenarios-list")
async def get_scenarios_list_endpoint():
    """Get list of scenario names"""
    return {"scenarios": get_scenarios_list()}

@router.get("/scenarios/{scenario_id}/scenes")
async def get_scenes_endpoint(scenario_id: str):
    """Get scenes for a specific scenario"""
    return {"scenes": get_scenes_list(scenario_id)}

@router.get("/scenarios/{scenario_id}/scenes/{scene_id}/episodes")
async def get_episodes_endpoint(scenario_id: str, scene_id: str):
    """Get episodes for a specific scene"""
    return {"episodes": get_episodes_list(scenario_id, scene_id)}

@router.get("/scenarios/{scenario_id}/scenes/{scene_id}/episodes/{episode_id}")
async def get_single_episode_endpoint(scenario_id: str, scene_id: str, episode_id: str):
    """Get a specific episode by ID"""
    episodes = get_episodes_for_scene(scenario_id, scene_id)
    episode = next((ep for ep in episodes if ep.id == episode_id), None)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode
