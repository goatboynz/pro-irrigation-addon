"""
Home Assistant entities API router.

This module provides endpoints for discovering Home Assistant entities.
"""

from fastapi import APIRouter
from typing import List, Dict, Any
from pydantic import BaseModel

from backend.services.ha_client import get_ha_client

router = APIRouter(prefix="/api/ha", tags=["Home Assistant"])


class EntityResponse(BaseModel):
    """Schema for entity response."""
    entity_id: str
    friendly_name: str
    domain: str
    state: str


@router.get("/entities", response_model=List[EntityResponse])
async def get_entities():
    """
    Get all available Home Assistant entities.
    
    This endpoint queries Home Assistant for all entities and returns
    them in a format suitable for entity selectors in the frontend.
    
    Returns:
        List[EntityResponse]: List of all available entities
    """
    ha_client = get_ha_client()
    
    # Check if SUPERVISOR_TOKEN is available
    if not ha_client.token:
        print("WARNING: SUPERVISOR_TOKEN not available. Cannot fetch entities from Home Assistant.")
        print("This is normal in development. In production, ensure the add-on has access to the supervisor API.")
        return []
    
    try:
        # Get all entities from Home Assistant
        entities_list = await ha_client.get_entities()
        
        # Convert to response format
        entities = []
        for entity in entities_list:
            entities.append(EntityResponse(
                entity_id=entity.entity_id,
                friendly_name=entity.attributes.get('friendly_name', entity.entity_id),
                domain=entity.entity_id.split('.')[0] if '.' in entity.entity_id else '',
                state=entity.state
            ))
        
        print(f"Successfully retrieved {len(entities)} entities from Home Assistant")
        return entities
    
    except Exception as e:
        # If we can't get entities, return empty list
        print(f"Error getting entities from Home Assistant: {e}")
        import traceback
        traceback.print_exc()
        return []
