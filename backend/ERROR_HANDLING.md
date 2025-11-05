# Error Handling and Logging Implementation

## Overview

This document describes the comprehensive error handling and logging system implemented for the Pro-Irrigation Add-on.

## Backend Error Handling

### Custom Exception Classes

Created `backend/exceptions.py` with custom exception hierarchy:

- `ProIrrigationException` - Base exception for all Pro-Irrigation errors
- `DatabaseException` - Database operation failures
- `HomeAssistantException` - Home Assistant API failures
- `ValidationException` - Input validation failures
- `SchedulerException` - Scheduler operation failures
- `QueueProcessorException` - Queue processor failures
- `ConfigurationException` - Invalid configuration

### Exception Handlers

Implemented comprehensive exception handlers in `backend/main.py`:

1. **ProIrrigationException Handler** - Handles custom exceptions with appropriate HTTP status codes
2. **HomeAssistantAPIError Handler** - Returns 502 Bad Gateway for HA communication failures
3. **SQLAlchemyError Handler** - Handles database errors with proper logging
4. **RequestValidationError Handler** - Returns detailed validation errors (422)
5. **HTTPException Handler** - Handles FastAPI HTTP exceptions
6. **Global Exception Handler** - Catches all unhandled exceptions with full traceback

### Logging Configuration

Enhanced logging system with:

- **Console Handler** - Simple format for stdout
- **File Handler** - Detailed format with rotation (10 MB, 5 backups)
- **Error File Handler** - Separate error log file
- **Log Directory** - `/data/logs/` with automatic creation
- **Log Levels** - Configurable via `LOG_LEVEL` environment variable
- **Structured Logging** - Includes filename, line number, and context

Log files:
- `/data/logs/pro-irrigation.log` - All logs
- `/data/logs/pro-irrigation-errors.log` - Errors only

### Error Response Format

All errors return structured JSON responses:

```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "details": {
    "additional": "context"
  }
}
```

## Frontend Error Handling

### API Service Enhancements

Enhanced `frontend/src/services/api.js` with:

1. **Request Interceptor** - Logs all API requests
2. **Response Interceptor** - Handles errors and emits events
3. **Retry Logic** - Automatic retries with exponential backoff
4. **Structured Error Handling** - Extracts error messages from backend responses
5. **Success Notifications** - Shows success toasts for CRUD operations
6. **Timeout Configuration** - 30-second timeout with proper error messages

### Composables

Created reusable composables for async operations:

#### `useLoading.js`
- Manages loading states
- Executes async functions with error handling
- Provides error clearing functionality

#### `useAsyncOperation.js`
- Advanced async operation management
- Automatic retry logic with exponential backoff
- Retry count tracking
- Configurable retry conditions
- Success/error/retry callbacks

### UI Components

#### `LoadingSpinner.vue`
- Reusable loading indicator
- Three sizes: small, medium, large
- Optional loading message
- Smooth animations

#### `ErrorDisplay.vue`
- Displays error messages with icons
- Three types: error, warning, info
- Optional retry button
- Styled to match Home Assistant design

### Toast Notification System

Enhanced `App.vue` with comprehensive toast system:

- **Multiple Toast Types** - Error, success, warning, info
- **Auto-dismiss** - Configurable duration
- **Click to Dismiss** - Manual dismissal
- **Smooth Animations** - Slide in/out transitions
- **Responsive Design** - Mobile-friendly
- **Event-based** - Global event system for notifications

Toast events:
- `api-error` - Error notifications
- `api-success` - Success notifications
- `api-warning` - Warning notifications
- `api-info` - Info notifications

### Store Error Handling

Updated `frontend/src/stores/irrigation.js`:

- Proper error state management
- Silent polling errors (no toast spam)
- Error logging for debugging
- Loading state tracking

## Usage Examples

### Backend

```python
from backend.exceptions import ValidationException

# Raise custom exception
raise ValidationException(
    "Invalid zone configuration",
    details={"field": "p1_duration_sec", "value": -1}
)
```

### Frontend

```javascript
// Using useLoading composable
import { useLoading } from '@/composables/useLoading'

const { loading, error, execute } = useLoading()

await execute(async () => {
  return await api.createPump(pumpData)
}, {
  errorMessage: 'Failed to create pump'
})

// Using useAsyncOperation with retry
import { useAsyncOperation } from '@/composables/useAsyncOperation'

const { loading, retrying, execute } = useAsyncOperation()

await execute(async () => {
  return await api.getPumps()
}, {
  maxRetries: 3,
  onRetry: (count, max) => {
    console.log(`Retrying... (${count}/${max})`)
  }
})

// Show custom notification
window.dispatchEvent(new CustomEvent('api-success', {
  detail: { message: 'Operation completed successfully' }
}))
```

## Testing

To test error handling:

1. **Backend Errors** - Check logs in `/data/logs/`
2. **Frontend Errors** - Check browser console and toast notifications
3. **Network Errors** - Disconnect network to test retry logic
4. **Validation Errors** - Submit invalid data to test validation

## Benefits

1. **Consistent Error Handling** - Unified approach across backend and frontend
2. **Better User Experience** - Clear error messages and loading states
3. **Improved Debugging** - Detailed logs with context
4. **Automatic Recovery** - Retry logic for transient failures
5. **Production Ready** - Proper error handling for all scenarios
