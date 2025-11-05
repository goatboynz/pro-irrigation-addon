import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 10000
})

// Response interceptor for error handling
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || error.response.statusText
      console.error('API Error:', message)
      return Promise.reject(new Error(message))
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error: No response from server')
      return Promise.reject(new Error('Network error: Unable to reach server'))
    } else {
      // Error in request setup
      console.error('Request Error:', error.message)
      return Promise.reject(error)
    }
  }
)

// Rooms API
export const roomsApi = {
  getRooms: () => apiClient.get('/rooms'),
  getRoom: (id) => apiClient.get(`/rooms/${id}`),
  createRoom: (data) => apiClient.post('/rooms', data),
  updateRoom: (id, data) => apiClient.put(`/rooms/${id}`, data),
  deleteRoom: (id) => apiClient.delete(`/rooms/${id}`),
  getRoomStatus: (id) => apiClient.get(`/rooms/${id}/status`)
}

// Pumps API
export const pumpsApi = {
  getPumps: (roomId) => apiClient.get(`/rooms/${roomId}/pumps`),
  createPump: (roomId, data) => apiClient.post(`/rooms/${roomId}/pumps`, data),
  updatePump: (id, data) => apiClient.put(`/pumps/${id}`, data),
  deletePump: (id) => apiClient.delete(`/pumps/${id}`),
  getPumpStatus: (id) => apiClient.get(`/pumps/${id}/status`)
}

// Zones API
export const zonesApi = {
  getZones: (pumpId) => apiClient.get(`/pumps/${pumpId}/zones`),
  createZone: (pumpId, data) => apiClient.post(`/pumps/${pumpId}/zones`, data),
  updateZone: (id, data) => apiClient.put(`/zones/${id}`, data),
  deleteZone: (id) => apiClient.delete(`/zones/${id}`)
}

// Water Events API
export const eventsApi = {
  getEvents: (roomId) => apiClient.get(`/rooms/${roomId}/events`),
  createEvent: (roomId, data) => apiClient.post(`/rooms/${roomId}/events`, data),
  updateEvent: (id, data) => apiClient.put(`/events/${id}`, data),
  deleteEvent: (id) => apiClient.delete(`/events/${id}`),
  assignZone: (eventId, zoneId) => apiClient.post(`/events/${eventId}/zones/${zoneId}`),
  removeZone: (eventId, zoneId) => apiClient.delete(`/events/${eventId}/zones/${zoneId}`),
  getNextRun: (id) => apiClient.get(`/events/${id}/next-run`)
}

// Sensors API
export const sensorsApi = {
  getSensors: (roomId) => apiClient.get(`/rooms/${roomId}/sensors`),
  createSensor: (roomId, data) => apiClient.post(`/rooms/${roomId}/sensors`, data),
  updateSensor: (id, data) => apiClient.put(`/sensors/${id}`, data),
  deleteSensor: (id) => apiClient.delete(`/sensors/${id}`),
  getCurrentValue: (id) => apiClient.get(`/sensors/${id}/current`),
  getHistory: (id, duration) => apiClient.get(`/sensors/${id}/history`, { params: { duration } })
}

// Settings API
export const settingsApi = {
  getSettings: () => apiClient.get('/settings'),
  updateSettings: (data) => apiClient.put('/settings', data)
}

// System API
export const systemApi = {
  reset: () => apiClient.post('/system/reset'),
  health: () => apiClient.get('/system/health')
}

// Manual Control API
export const manualApi = {
  run: (data) => apiClient.post('/manual/run', data),
  stop: (data) => apiClient.post('/manual/stop', data)
}

// Home Assistant API
export const haApi = {
  getEntities: () => apiClient.get('/ha/entities')
}

// Default export with all APIs
export default {
  getRooms: roomsApi.getRooms,
  getRoom: roomsApi.getRoom,
  createRoom: roomsApi.createRoom,
  updateRoom: roomsApi.updateRoom,
  deleteRoom: roomsApi.deleteRoom,
  getRoomStatus: roomsApi.getRoomStatus,
  
  getPumps: pumpsApi.getPumps,
  createPump: pumpsApi.createPump,
  updatePump: pumpsApi.updatePump,
  deletePump: pumpsApi.deletePump,
  getPumpStatus: pumpsApi.getPumpStatus,
  
  getZones: zonesApi.getZones,
  createZone: zonesApi.createZone,
  updateZone: zonesApi.updateZone,
  deleteZone: zonesApi.deleteZone,
  
  getEvents: eventsApi.getEvents,
  createEvent: eventsApi.createEvent,
  updateEvent: eventsApi.updateEvent,
  deleteEvent: eventsApi.deleteEvent,
  assignZone: eventsApi.assignZone,
  removeZone: eventsApi.removeZone,
  getNextRun: eventsApi.getNextRun,
  
  getSensors: sensorsApi.getSensors,
  createSensor: sensorsApi.createSensor,
  updateSensor: sensorsApi.updateSensor,
  deleteSensor: sensorsApi.deleteSensor,
  getCurrentValue: sensorsApi.getCurrentValue,
  getHistory: sensorsApi.getHistory,
  
  getSettings: settingsApi.getSettings,
  updateSettings: settingsApi.updateSettings,
  
  systemReset: systemApi.reset,
  systemHealth: systemApi.health,
  
  manualRun: manualApi.run,
  manualStop: manualApi.stop,
  
  getHAEntities: haApi.getEntities
}
