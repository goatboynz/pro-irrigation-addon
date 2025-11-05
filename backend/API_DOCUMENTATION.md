# Pro-Irrigation Add-on API Documentation

## Overview

This document provides an overview of the REST API endpoints implemented for the Pro-Irrigation Home Assistant Add-on.

## Base URL

All endpoints are prefixed with the base URL: `http://localhost:8000`

When accessed through Home Assistant Ingress, the base URL will be proxied through Home Assistant.

## Authentication

Authentication is handled by Home Assistant Ingress. No additional authentication is required for API calls from the frontend.

## Endpoints

### System Endpoints

#### Health Check
- **GET** `/api/health`
- Returns health status of the application and database
- Response: `HealthResponse`

#### System Status
- **GET** `/api/status`
- Returns overall system status with statistics
- Response: `SystemStatusResponse`

### Pump Endpoints

#### List All Pumps
- **GET** `/api/pumps`
- Returns list of all pumps with status information
- Response: `List[PumpResponse]`

#### Create Pump
- **POST** `/api/pumps`
- Creates a new pump
- Request Body: `PumpCreate`
- Response: `PumpBasic`

#### Get Pump Details
- **GET** `/api/pumps/{pump_id}`
- Returns details for a specific pump
- Response: `PumpBasic`

#### Update Pump
- **PUT** `/api/pumps/{pump_id}`
- Updates pump configuration
- Request Body: `PumpUpdate`
- Response: `PumpBasic`

#### Delete Pump
- **DELETE** `/api/pumps/{pump_id}`
- Deletes a pump and all its zones
- Response: 204 No Content

#### Get Pump Status
- **GET** `/api/pumps/{pump_id}/status`
- Returns real-time status of a pump
- Response: `{ status, active_zone, queue_length }`

### Zone Endpoints

#### List Zones for Pump
- **GET** `/api/pumps/{pump_id}/zones`
- Returns all zones for a specific pump
- Response: `List[ZoneBasic]`

#### Create Zone
- **POST** `/api/pumps/{pump_id}/zones`
- Creates a new zone for a pump
- Request Body: `ZoneCreate`
- Response: `ZoneBasic`

#### Get Zone Details
- **GET** `/api/zones/{zone_id}`
- Returns details for a specific zone
- Response: `ZoneBasic`

#### Update Zone
- **PUT** `/api/zones/{zone_id}`
- Updates zone configuration
- Request Body: `ZoneUpdate`
- Response: `ZoneBasic`

#### Delete Zone
- **DELETE** `/api/zones/{zone_id}`
- Deletes a zone
- Response: 204 No Content

#### Get Next Run Time
- **GET** `/api/zones/{zone_id}/next-run`
- Calculates and returns the next scheduled run time
- Response: `NextRunResponse`

### Entity Discovery Endpoints

#### Get Home Assistant Entities
- **GET** `/api/ha/entities?type={entity_type}`
- Discovers Home Assistant entities by type
- Query Parameters:
  - `type` (optional): Entity type filter (switch, input_datetime, input_number, input_boolean)
- Response: `List[EntityResponse]`

### Global Settings Endpoints

#### Get Global Settings
- **GET** `/api/settings`
- Returns current global settings
- Response: `GlobalSettingsResponse`

#### Update Global Settings
- **PUT** `/api/settings`
- Updates global settings
- Request Body: `GlobalSettingsUpdate`
- Response: `GlobalSettingsResponse`

## Data Models

### PumpCreate
```json
{
  "name": "string",
  "lock_entity": "string"
}
```

### PumpUpdate
```json
{
  "name": "string (optional)",
  "lock_entity": "string (optional)"
}
```

### PumpResponse
```json
{
  "id": 1,
  "name": "string",
  "lock_entity": "string",
  "status": "idle|running|queued",
  "active_zone": "string|null",
  "queue_length": 0,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### ZoneCreate
```json
{
  "name": "string",
  "switch_entity": "string",
  "mode": "auto|manual",
  "p1_duration_sec": 120,
  "p2_event_count": 3,
  "p2_duration_sec": 60,
  "p1_manual_list": "08:30.120\n10:00.90",
  "p2_manual_list": "12:00.60\n14:00.60",
  "enabled": true
}
```

### ZoneUpdate
```json
{
  "name": "string (optional)",
  "switch_entity": "string (optional)",
  "mode": "auto|manual (optional)",
  "p1_duration_sec": 120,
  "p2_event_count": 3,
  "p2_duration_sec": 60,
  "p1_manual_list": "string (optional)",
  "p2_manual_list": "string (optional)",
  "enabled": true
}
```

### GlobalSettingsUpdate
```json
{
  "lights_on_entity": "string (optional)",
  "lights_off_entity": "string (optional)",
  "p1_delay_entity": "string (optional)",
  "p2_delay_entity": "string (optional)",
  "p2_buffer_entity": "string (optional)",
  "feed_notes": "string (optional)"
}
```

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK` - Successful GET/PUT request
- `201 Created` - Successful POST request
- `204 No Content` - Successful DELETE request
- `400 Bad Request` - Invalid request data
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error
- `502 Bad Gateway` - Home Assistant API error
- `503 Service Unavailable` - Service not initialized

Error responses include a JSON body with details:
```json
{
  "detail": "Error message"
}
```

## Interactive API Documentation

FastAPI provides automatic interactive API documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

These interfaces allow you to explore and test all API endpoints directly from your browser.
