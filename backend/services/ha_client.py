"""
Home Assistant API Client

This module provides a client for interacting with the Home Assistant API
through the supervisor proxy. It handles entity discovery, state retrieval,
and service calls with built-in error handling and retry logic.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import aiohttp


logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Represents a Home Assistant entity"""
    entity_id: str
    friendly_name: str
    state: str
    attributes: Dict[str, Any]


@dataclass
class EntityState:
    """Represents the current state of an entity"""
    entity_id: str
    state: str
    attributes: Dict[str, Any]
    last_changed: str
    last_updated: str


class HomeAssistantAPIError(Exception):
    """Raised when Home Assistant API calls fail"""
    pass


class HomeAssistantClient:
    """
    Client for interacting with Home Assistant API through the supervisor.
    
    This client provides methods for entity discovery, state retrieval,
    and service calls with automatic retry logic for transient failures.
    """
    
    def __init__(self, supervisor_token: str, base_url: str = "http://supervisor/core/api"):
        """
        Initialize the Home Assistant client.
        
        Args:
            supervisor_token: The supervisor token for authentication
            base_url: The base URL for the Home Assistant API (default: supervisor proxy)
        """
        self.base_url = base_url.rstrip('/')
        self.token = supervisor_token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self._session: Optional[aiohttp.ClientSession] = None
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=self.headers)
        return self._session
    
    async def close(self):
        """Close the aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Any:
        """
        Make an HTTP request to the Home Assistant API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            json_data: Optional JSON data for POST requests
            retry_count: Current retry attempt number
            
        Returns:
            JSON response from the API
            
        Raises:
            HomeAssistantAPIError: If the request fails after all retries
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        session = await self._get_session()
        
        try:
            async with session.request(method, url, json=json_data) as response:
                if response.status == 200 or response.status == 201:
                    return await response.json()
                elif response.status == 404:
                    logger.warning(f"Resource not found: {url}")
                    raise HomeAssistantAPIError(f"Resource not found: {endpoint}")
                else:
                    error_text = await response.text()
                    logger.error(f"API request failed: {response.status} - {error_text}")
                    raise HomeAssistantAPIError(
                        f"API request failed with status {response.status}: {error_text}"
                    )
        
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if retry_count < self.max_retries:
                delay = self.retry_delay * (2 ** retry_count)  # Exponential backoff
                logger.warning(
                    f"Request to {url} failed (attempt {retry_count + 1}/{self.max_retries}), "
                    f"retrying in {delay}s: {str(e)}"
                )
                await asyncio.sleep(delay)
                return await self._make_request(method, endpoint, json_data, retry_count + 1)
            else:
                logger.error(f"Request to {url} failed after {self.max_retries} retries: {str(e)}")
                raise HomeAssistantAPIError(
                    f"Failed to connect to Home Assistant after {self.max_retries} retries: {str(e)}"
                )
    
    async def get_entities(self, entity_type: Optional[str] = None) -> List[Entity]:
        """
        Discover entities from Home Assistant, optionally filtered by type.
        
        Args:
            entity_type: Optional entity type filter (e.g., 'switch', 'input_datetime',
                        'input_number', 'input_boolean')
        
        Returns:
            List of Entity objects
            
        Raises:
            HomeAssistantAPIError: If the API call fails
        """
        try:
            response = await self._make_request("GET", "/states")
            
            entities = []
            for state_data in response:
                entity_id = state_data.get("entity_id", "")
                
                # Filter by entity type if specified
                if entity_type:
                    if not entity_id.startswith(f"{entity_type}."):
                        continue
                
                attributes = state_data.get("attributes", {})
                entity = Entity(
                    entity_id=entity_id,
                    friendly_name=attributes.get("friendly_name", entity_id),
                    state=state_data.get("state", "unknown"),
                    attributes=attributes
                )
                entities.append(entity)
            
            logger.debug(f"Discovered {len(entities)} entities" + 
                        (f" of type '{entity_type}'" if entity_type else ""))
            return entities
        
        except HomeAssistantAPIError:
            raise
        except Exception as e:
            logger.error(f"Error parsing entities response: {str(e)}")
            raise HomeAssistantAPIError(f"Failed to parse entities: {str(e)}")
    
    async def get_state(self, entity_id: str) -> EntityState:
        """
        Retrieve the current state of a specific entity.
        
        Args:
            entity_id: The entity ID (e.g., 'switch.irrigation_zone_1')
        
        Returns:
            EntityState object with current state information
            
        Raises:
            HomeAssistantAPIError: If the entity doesn't exist or API call fails
        """
        try:
            response = await self._make_request("GET", f"/states/{entity_id}")
            
            state = EntityState(
                entity_id=response.get("entity_id", entity_id),
                state=response.get("state", "unknown"),
                attributes=response.get("attributes", {}),
                last_changed=response.get("last_changed", ""),
                last_updated=response.get("last_updated", "")
            )
            
            logger.debug(f"Retrieved state for {entity_id}: {state.state}")
            return state
        
        except HomeAssistantAPIError:
            raise
        except Exception as e:
            logger.error(f"Error parsing state response for {entity_id}: {str(e)}")
            raise HomeAssistantAPIError(f"Failed to parse state for {entity_id}: {str(e)}")
    
    async def call_service(
        self,
        domain: str,
        service: str,
        entity_id: Optional[str] = None,
        service_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Call a Home Assistant service.
        
        Args:
            domain: Service domain (e.g., 'switch', 'input_boolean')
            service: Service name (e.g., 'turn_on', 'turn_off')
            entity_id: Optional entity ID to target
            service_data: Optional additional service data
            
        Raises:
            HomeAssistantAPIError: If the service call fails
        """
        data = service_data.copy() if service_data else {}
        
        if entity_id:
            data["entity_id"] = entity_id
        
        try:
            await self._make_request("POST", f"/services/{domain}/{service}", json_data=data)
            logger.debug(f"Called service {domain}.{service}" + 
                        (f" on {entity_id}" if entity_id else ""))
        
        except HomeAssistantAPIError:
            raise
        except Exception as e:
            logger.error(f"Error calling service {domain}.{service}: {str(e)}")
            raise HomeAssistantAPIError(f"Failed to call service {domain}.{service}: {str(e)}")
    
    async def turn_on(self, entity_id: str) -> None:
        """
        Convenience method to turn on a switch or input_boolean entity.
        
        Args:
            entity_id: The entity ID to turn on
            
        Raises:
            HomeAssistantAPIError: If the service call fails
        """
        domain = entity_id.split('.')[0] if '.' in entity_id else 'switch'
        await self.call_service(domain, "turn_on", entity_id=entity_id)
        logger.info(f"Turned on {entity_id}")
    
    async def turn_off(self, entity_id: str) -> None:
        """
        Convenience method to turn off a switch or input_boolean entity.
        
        Args:
            entity_id: The entity ID to turn off
            
        Raises:
            HomeAssistantAPIError: If the service call fails
        """
        domain = entity_id.split('.')[0] if '.' in entity_id else 'switch'
        await self.call_service(domain, "turn_off", entity_id=entity_id)
        logger.info(f"Turned off {entity_id}")
