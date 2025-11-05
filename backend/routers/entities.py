"""
Entity Discovery API Endpoints

This module implements endpoints for discovering Home Assistant entities
that can be used in pump and zone configurations.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..models.schemas import EntityResponse
from ..services.ha_client import HomeAssistantClient, HomeAssistantAPIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ha", tags=["Home Assistant"])

# Global reference to HA client (will be set by main application)
_ha_client = None


def set_ha_client(client):
    """
    Set the global Home Assistant client reference.
    
    Args:
        client: HomeAssistantClient instance
    """
    global _ha_client
    _ha_client = client


def get_ha_client():
    """
    Get the Home Assistant client instance.
    
    Returns:
        HomeAssistantClient instance or None if not initialized
    """
    return _ha_client


@router.get("/entities", response_model=List[EntityResponse])
async def get_entities(
    type: Optional[str] = Query(
        None,
        description="Entity type filter (switch, input_datetime, input_number, input_boolean)"
    )
):
    """
    Discover Home Assistant entities.
    
    Returns a list of Home Assistant entities filtered by type.
    This endpoint is used to populate entity selectors in the frontend.
    
    Supported entity types:
    - switch: Switch entities for zone control
    - input_datetime: Input datetime entities for timing settings
    - input_number: Input number entities for numeric settings
    - input_boolean: Input boolean entities for pump locks
    
    Args:
        type: Optional entity type filter
    
    Returns:
        List[EntityResponse]: List of entities with ID, friendly name, and state
    
    Raises:
        HTTPException: If entity discovery fails
    """
    try:
        ha_client = get_ha_client()
        
        if not ha_client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Home Assistant client not initialized"
            )
        
        # Validate entity type if provided
        valid_types = ['switch', 'input_datetime', 'input_number', 'input_boolean']
        if type and type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid entity type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Get entities from Home Assistant
        try:
            entities = await ha_client.get_entities(type)
            
            # Convert to response format
            entity_responses = [
                EntityResponse(
                    entity_id=entity['entity_id'],
                    friendly_name=entity.get('friendly_name', entity['entity_id']),
                    state=entity.get('state', 'unknown')
                )
                for entity in entities
            ]
            
            logger.info(
                f"Retrieved {len(entity_responses)} entities"
                f"{f' of type {type}' if type else ''}"
            )
            
            return entity_responses
        
        except HomeAssistantAPIError as e:
            logger.error(f"Home Assistant API error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to retrieve entities from Home Assistant: {str(e)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving entities: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve entities: {str(e)}"
        )
