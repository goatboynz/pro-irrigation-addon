import axios from 'axios'

/**
 * IrrigationAPI - Client for Pro-Irrigation backend API
 * Handles all HTTP communication with the FastAPI backend
 */
class IrrigationAPI {
  constructor() {
    // Use relative paths for production (Ingress compatibility)
    // In development, Vite proxy will forward /api requests to backend
    this.client = axios.create({
      baseURL: '/api',
      timeout: 30000, // 30 seconds
      headers: {
        'Content-Type': 'application/json'
      }
    })

    // Request interceptor for logging
    this.client.interceptors.request.use(
      config => {
        console.debug(`API Request: ${config.method.toUpperCase()} ${config.url}`)
        return config
      },
      error => {
        console.error('API Request Error:', error)
        return Promise.reject(error)
      }
    )

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      response => {
        console.debug(`API Response: ${response.config.method.toUpperCase()} ${response.config.url} - ${response.status}`)
        return response
      },
      error => {
        this.handleError(error)
        return Promise.reject(error)
      }
    )

    // Retry configuration
    this.maxRetries = 3
    this.retryDelay = 1000 // 1 second
  }

  /**
   * Handle API errors with user-friendly notifications
   */
  handleError(error) {
    let message = 'An unexpected error occurred'
    let details = {}
    
    if (error.response) {
      // Server responded with error status
      const status = error.response.status
      const data = error.response.data
      
      // Extract error message from structured response
      if (data && data.message) {
        message = data.message
        details = data.details || {}
      } else if (data && data.detail) {
        message = data.detail
      } else {
        // Fallback to status-based messages
        switch (status) {
          case 400:
            message = 'Invalid request. Please check your input.'
            break
          case 401:
            message = 'Authentication required'
            break
          case 403:
            message = 'Access denied'
            break
          case 404:
            message = 'Resource not found'
            break
          case 422:
            message = 'Validation error. Please check your input.'
            if (data && data.details && data.details.errors) {
              details = { errors: data.details.errors }
            }
            break
          case 500:
            message = 'Server error occurred. Please try again.'
            break
          case 502:
            message = 'Unable to communicate with Home Assistant'
            break
          case 503:
            message = 'Service temporarily unavailable'
            break
          default:
            message = `Error: ${status}`
        }
      }
    } else if (error.request) {
      // Request made but no response
      if (error.code === 'ECONNABORTED') {
        message = 'Request timeout. Please check your connection.'
      } else if (error.code === 'ERR_NETWORK') {
        message = 'Network error. Unable to connect to server.'
      } else {
        message = 'Unable to connect to server. Please check your connection.'
      }
    } else {
      // Something else happened
      message = error.message || 'An unexpected error occurred'
    }

    // Log error details for debugging
    console.error('API Error:', {
      message,
      details,
      status: error.response?.status,
      url: error.config?.url,
      method: error.config?.method,
      error
    })
    
    // Emit custom event for toast notifications
    window.dispatchEvent(new CustomEvent('api-error', { 
      detail: { message, details } 
    }))
  }

  /**
   * Retry a failed request with exponential backoff
   */
  async retryRequest(requestFn, retries = this.maxRetries) {
    for (let i = 0; i < retries; i++) {
      try {
        return await requestFn()
      } catch (error) {
        // Don't retry on client errors (4xx) except 408 (timeout)
        if (error.response && error.response.status >= 400 && error.response.status < 500 && error.response.status !== 408) {
          throw error
        }

        // Last attempt, throw error
        if (i === retries - 1) {
          throw error
        }

        // Wait before retrying with exponential backoff
        const delay = this.retryDelay * Math.pow(2, i)
        console.warn(`Request failed, retrying in ${delay}ms (attempt ${i + 1}/${retries})`)
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }
  }

  /**
   * Show success notification
   */
  showSuccess(message) {
    window.dispatchEvent(new CustomEvent('api-success', { 
      detail: { message } 
    }))
  }

  // ==================== Pump Operations ====================

  /**
   * Get all pumps with status (with retry)
   */
  async getPumps() {
    return await this.retryRequest(async () => {
      const response = await this.client.get('/pumps')
      return response.data
    })
  }

  /**
   * Create a new pump
   */
  async createPump(pumpData) {
    const response = await this.client.post('/pumps', pumpData)
    this.showSuccess('Pump created successfully')
    return response.data
  }

  /**
   * Get pump details by ID
   */
  async getPump(pumpId) {
    const response = await this.client.get(`/pumps/${pumpId}`)
    return response.data
  }

  /**
   * Update pump configuration
   */
  async updatePump(pumpId, pumpData) {
    const response = await this.client.put(`/pumps/${pumpId}`, pumpData)
    this.showSuccess('Pump updated successfully')
    return response.data
  }

  /**
   * Delete a pump
   */
  async deletePump(pumpId) {
    const response = await this.client.delete(`/pumps/${pumpId}`)
    this.showSuccess('Pump deleted successfully')
    return response.data
  }

  /**
   * Get real-time pump status
   */
  async getPumpStatus(pumpId) {
    const response = await this.client.get(`/pumps/${pumpId}/status`)
    return response.data
  }

  // ==================== Zone Operations ====================

  /**
   * Get all zones for a specific pump
   */
  async getZones(pumpId) {
    const response = await this.client.get(`/pumps/${pumpId}/zones`)
    return response.data
  }

  /**
   * Create a new zone for a pump
   */
  async createZone(pumpId, zoneData) {
    const response = await this.client.post(`/pumps/${pumpId}/zones`, zoneData)
    this.showSuccess('Zone created successfully')
    return response.data
  }

  /**
   * Get zone details by ID
   */
  async getZone(zoneId) {
    const response = await this.client.get(`/zones/${zoneId}`)
    return response.data
  }

  /**
   * Update zone configuration
   */
  async updateZone(zoneId, zoneData) {
    const response = await this.client.put(`/zones/${zoneId}`, zoneData)
    this.showSuccess('Zone updated successfully')
    return response.data
  }

  /**
   * Delete a zone
   */
  async deleteZone(zoneId) {
    const response = await this.client.delete(`/zones/${zoneId}`)
    this.showSuccess('Zone deleted successfully')
    return response.data
  }

  /**
   * Get next scheduled run time for a zone
   */
  async getZoneNextRun(zoneId) {
    const response = await this.client.get(`/zones/${zoneId}/next-run`)
    return response.data
  }

  // ==================== Entity Discovery ====================

  /**
   * Get available Home Assistant entities by type
   * @param {string} entityType - Type of entity (switch, input_datetime, input_number, input_boolean)
   */
  async getAvailableEntities(entityType) {
    const response = await this.client.get('/ha/entities', {
      params: { type: entityType }
    })
    return response.data
  }

  // ==================== Global Settings ====================

  /**
   * Get global settings
   */
  async getGlobalSettings() {
    const response = await this.client.get('/settings')
    return response.data
  }

  /**
   * Update global settings
   */
  async updateGlobalSettings(settings) {
    const response = await this.client.put('/settings', settings)
    this.showSuccess('Settings updated successfully')
    return response.data
  }

  // ==================== System Health ====================

  /**
   * Check system health
   */
  async getHealth() {
    const response = await this.client.get('/health')
    return response.data
  }

  /**
   * Get overall system status
   */
  async getStatus() {
    const response = await this.client.get('/status')
    return response.data
  }
}

// Export singleton instance
export default new IrrigationAPI()
