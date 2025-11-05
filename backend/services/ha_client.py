"""
Home Assistant API client for irrigation system.

This module provides integration with Home Assistant's REST API for:
- Entity discovery (switches, input_datetime, input_boolean, sensors)
- Entity state reading
- Service calls (switch control, lock control)

Uses SUPERVISOR_TOKEN from environment for authentication.
"""

import os
import aiohttp
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Represents a Home Assistant entity."""
    entity_id: str
    state: str
    attributes: Dict[str, Any]
    last_changed: str
    last_updated: str


@dataclass
class EntityState:
    """Represents the current state of an entity."""
    entity_id: str
    state: str
    attributes: Dict[str, Any]


class HomeAssistantClient:
    """
    Client for interacting with Home Assistant API.
    
    This client uses the supervisor API endpoint which is available
    within Home Assistant add-ons. Authentication is handled via
    the SUPERVISOR_TOKEN environment variable.
    """
    
    def __init__(self, base_url: str = "http://supervisor/core/api", token: Optional[str] = None):
        """
        Initialize the Home Assistant client.
        
        Args:
            base_url: Base URL for Home Assistant API (default: supervisor endpoint)
            token: Authentication token (default: from SUPERVISOR_TOKEN env var)
        """
        self.base_url = base_url
        self.token = token or os.getenv("SUPERVISOR_TOKEN")
        
        if not self.token:
            logger.warning("SUPERVISOR_TOKEN not found in environment. HA API calls may fail.")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    async def get_entities(self, entity_type: Optional[str] = None) -> List[Entity]:
        """
        Discover entities from Home Assistant.
        
        Args:
            entity_type: Filter by entity domain (e.g., 'switch', 'input_datetime', 'sensor')
                        If None, returns all entities.
        
        Returns:
            List of Entity objects matching the filter
        
        Raises:
            aiohttp.ClientError: If the API request fails
        """
        url = f"{self.base_url}/states"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    response.raise_for_status()
                    states = await response.json()
                    
                    entities = []
                    for state_data in states:
                        entity_id = state_data.get("entity_id", "")
                        
                        # Filter by entity type if specified
                        if entity_type:
                            domain = entity_id.split(".")[0] if "." in entity_id else ""
                            if domain != entity_type:
                                continue
                        
                        entity = Entity(
                            entity_id=entity_id,
                            state=state_data.get("state", ""),
                            attributes=state_data.get("attributes", {}),
                            last_changed=state_data.get("last_changed", ""),
                            last_updated=state_data.get("last_updated", "")
                        )
                        entities.append(entity)
                    
                    logger.info(f"Retrieved {len(entities)} entities" + 
                              (f" of type '{entity_type}'" if entity_type else ""))
                    return entities
                    
        except aiohttp.ClientError as e:
            logger.error(f"Failed to get entities from Home Assistant: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting entities: {e}")
            raise
    
    async def get_state(self, entity_id: str) -> EntityState:
        """
        Get the current state of a specific entity.
        
        Args:
            entity_id: The entity ID to query (e.g., 'switch.irrigation_zone_1')
        
        Returns:
            EntityState object with current state and attributes
        
        Raises:
            aiohttp.ClientError: If the API request fails
            ValueError: If the entity is not found
        """
        url = f"{self.base_url}/states/{entity_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 404:
                        raise ValueError(f"Entity '{entity_id}' not found in Home Assistant")
                    
                    response.raise_for_status()
                    state_data = await response.json()
                    
                    entity_state = EntityState(
                        entity_id=state_data.get("entity_id", entity_id),
                        state=state_data.get("state", ""),
                        attributes=state_data.get("attributes", {})
                    )
                    
                    logger.debug(f"Retrieved state for {entity_id}: {entity_state.state}")
                    return entity_state
                    
        except aiohttp.ClientError as e:
            logger.error(f"Failed to get state for {entity_id}: {e}")
            raise
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting state for {entity_id}: {e}")
            raise
    
    async def call_service(self, domain: str, service: str, entity_id: str, 
                          service_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Call a Home Assistant service.
        
        Args:
            domain: Service domain (e.g., 'switch', 'input_boolean')
            service: Service name (e.g., 'turn_on', 'turn_off')
            entity_id: Target entity ID
            service_data: Optional additional service data
        
        Raises:
            aiohttp.ClientError: If the API request fails
        """
        url = f"{self.base_url}/services/{domain}/{service}"
        
        payload = {
            "entity_id": entity_id
        }
        
        if service_data:
            payload.update(service_data)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self.headers, json=payload) as response:
                    response.raise_for_status()
                    logger.info(f"Called service {domain}.{service} on {entity_id}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"Failed to call service {domain}.{service} on {entity_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling service: {e}")
            raise
    
    async def turn_on(self, entity_id: str) -> None:
        """
        Turn on a switch or input_boolean entity.
        
        Args:
            entity_id: Entity to turn on (e.g., 'switch.pump_1', 'input_boolean.pump_lock')
        
        Raises:
            aiohttp.ClientError: If the API request fails
        """
        domain = entity_id.split(".")[0] if "." in entity_id else "switch"
        await self.call_service(domain, "turn_on", entity_id)
    
    async def turn_off(self, entity_id: str) -> None:
        """
        Turn off a switch or input_boolean entity.
        
        Args:
            entity_id: Entity to turn off (e.g., 'switch.pump_1', 'input_boolean.pump_lock')
        
        Raises:
            aiohttp.ClientError: If the API request fails
        """
        domain = entity_id.split(".")[0] if "." in entity_id else "switch"
        await self.call_service(domain, "turn_off", entity_id)
    
    async def is_entity_on(self, entity_id: str) -> bool:
        """
        Check if an entity is in the 'on' state.
        
        Args:
            entity_id: Entity to check
        
        Returns:
            True if entity state is 'on', False otherwise
        
        Raises:
            aiohttp.ClientError: If the API request fails
        """
        state = await self.get_state(entity_id)
        return state.state.lower() == "on"
    
    async def is_entity_off(self, entity_id: str) -> bool:
        """
        Check if an entity is in the 'off' state.
        
        Args:
            entity_id: Entity to check
        
        Returns:
            True if entity state is 'off', False otherwise
        
        Raises:
            aiohttp.ClientError: If the API request fails
        """
        state = await self.get_state(entity_id)
        return state.state.lower() == "off"


# Singleton instance for use throughout the application
_ha_client_instance: Optional[HomeAssistantClient] = None


def get_ha_client() -> HomeAssistantClient:
    """
    Get the singleton Home Assistant client instance.
    
    Returns:
        HomeAssistantClient instance
    """
    global _ha_client_instance
    if _ha_client_instance is None:
        _ha_client_instance = HomeAssistantClient()
    return _ha_client_instance


# ============================================================================
# Entity Validation Helpers
# ============================================================================

async def validate_entity_exists(entity_id: str, client: Optional[HomeAssistantClient] = None) -> bool:
    """
    Validate that an entity exists in Home Assistant.
    
    This helper should be called before saving entity references to the database
    to ensure the entity is valid and accessible.
    
    Args:
        entity_id: The entity ID to validate (e.g., 'switch.zone_1')
        client: Optional HomeAssistantClient instance (uses singleton if not provided)
    
    Returns:
        True if entity exists and is accessible, False otherwise
    
    Example:
        >>> if await validate_entity_exists('switch.zone_1'):
        ...     # Save to database
        ...     pass
        ... else:
        ...     raise ValueError("Entity not found")
    """
    if not entity_id:
        logger.warning("Empty entity_id provided for validation")
        return False
    
    ha_client = client or get_ha_client()
    
    try:
        await ha_client.get_state(entity_id)
        logger.debug(f"Entity validation successful: {entity_id}")
        return True
    except ValueError as e:
        # Entity not found (404)
        logger.warning(f"Entity validation failed: {e}")
        return False
    except aiohttp.ClientError as e:
        # API error - log but don't fail validation
        # (entity might exist but API is temporarily unavailable)
        logger.error(f"Could not validate entity {entity_id} due to API error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error validating entity {entity_id}: {e}")
        return False


async def validate_entity_domain(entity_id: str, expected_domain: str, 
                                client: Optional[HomeAssistantClient] = None) -> bool:
    """
    Validate that an entity exists and belongs to the expected domain.
    
    Args:
        entity_id: The entity ID to validate
        expected_domain: Expected domain (e.g., 'switch', 'input_boolean', 'sensor')
        client: Optional HomeAssistantClient instance
    
    Returns:
        True if entity exists and has the correct domain, False otherwise
    
    Example:
        >>> if await validate_entity_domain('switch.zone_1', 'switch'):
        ...     # Entity is a valid switch
        ...     pass
    """
    if not entity_id or "." not in entity_id:
        logger.warning(f"Invalid entity_id format: {entity_id}")
        return False
    
    # Check domain from entity_id
    actual_domain = entity_id.split(".")[0]
    if actual_domain != expected_domain:
        logger.warning(f"Entity {entity_id} has domain '{actual_domain}', expected '{expected_domain}'")
        return False
    
    # Verify entity exists
    return await validate_entity_exists(entity_id, client)


async def validate_switch_entity(entity_id: str, client: Optional[HomeAssistantClient] = None) -> bool:
    """
    Validate that an entity is a valid switch.
    
    Args:
        entity_id: The entity ID to validate
        client: Optional HomeAssistantClient instance
    
    Returns:
        True if entity is a valid switch, False otherwise
    """
    return await validate_entity_domain(entity_id, "switch", client)


async def validate_input_boolean_entity(entity_id: str, client: Optional[HomeAssistantClient] = None) -> bool:
    """
    Validate that an entity is a valid input_boolean.
    
    Args:
        entity_id: The entity ID to validate
        client: Optional HomeAssistantClient instance
    
    Returns:
        True if entity is a valid input_boolean, False otherwise
    """
    return await validate_entity_domain(entity_id, "input_boolean", client)


async def validate_input_datetime_entity(entity_id: str, client: Optional[HomeAssistantClient] = None) -> bool:
    """
    Validate that an entity is a valid input_datetime.
    
    Args:
        entity_id: The entity ID to validate
        client: Optional HomeAssistantClient instance
    
    Returns:
        True if entity is a valid input_datetime, False otherwise
    """
    return await validate_entity_domain(entity_id, "input_datetime", client)


async def validate_sensor_entity(entity_id: str, client: Optional[HomeAssistantClient] = None) -> bool:
    """
    Validate that an entity is a valid sensor.
    
    Args:
        entity_id: The entity ID to validate
        client: Optional HomeAssistantClient instance
    
    Returns:
        True if entity is a valid sensor, False otherwise
    """
    return await validate_entity_domain(entity_id, "sensor", client)


async def get_entity_friendly_name(entity_id: str, client: Optional[HomeAssistantClient] = None) -> Optional[str]:
    """
    Get the friendly name of an entity from its attributes.
    
    Args:
        entity_id: The entity ID to query
        client: Optional HomeAssistantClient instance
    
    Returns:
        Friendly name if available, None otherwise
    """
    ha_client = client or get_ha_client()
    
    try:
        state = await ha_client.get_state(entity_id)
        return state.attributes.get("friendly_name")
    except Exception as e:
        logger.error(f"Could not get friendly name for {entity_id}: {e}")
        return None
