import { defineStore } from 'pinia'
import api from '../services/api'

/**
 * Irrigation Store - Central state management for Pro-Irrigation
 * Manages pumps, zones, settings, and real-time status polling
 */
export const useIrrigationStore = defineStore('irrigation', {
  state: () => ({
    // Pumps data
    pumps: [],
    currentPump: null,
    
    // Zones data
    zones: [],
    currentZone: null,
    
    // Global settings
    settings: null,
    
    // UI state
    loading: false,
    error: null,
    
    // Polling state
    pollingInterval: null,
    isPolling: false
  }),

  getters: {
    /**
     * Get pump by ID
     */
    getPumpById: (state) => (pumpId) => {
      return state.pumps.find(pump => pump.id === pumpId)
    },

    /**
     * Get zones for a specific pump
     */
    getZonesByPumpId: (state) => (pumpId) => {
      return state.zones.filter(zone => zone.pump_id === pumpId)
    },

    /**
     * Get zone by ID
     */
    getZoneById: (state) => (zoneId) => {
      return state.zones.find(zone => zone.id === zoneId)
    },

    /**
     * Get pumps with running status
     */
    runningPumps: (state) => {
      return state.pumps.filter(pump => pump.status === 'running')
    },

    /**
     * Get pumps with queued jobs
     */
    queuedPumps: (state) => {
      return state.pumps.filter(pump => pump.status === 'queued')
    },

    /**
     * Get enabled zones count
     */
    enabledZonesCount: (state) => {
      return state.zones.filter(zone => zone.enabled).length
    },

    /**
     * Check if settings are configured
     */
    hasSettings: (state) => {
      return state.settings !== null && 
             state.settings.lights_on_entity !== null
    }
  },

  actions: {
    // ==================== Pump Actions ====================

    /**
     * Fetch all pumps
     */
    async fetchPumps() {
      try {
        this.loading = true
        this.error = null
        this.pumps = await api.getPumps()
      } catch (error) {
        this.error = 'Failed to fetch pumps'
        console.error('Error fetching pumps:', error)
        // Error already handled by API interceptor
      } finally {
        this.loading = false
      }
    },

    /**
     * Create a new pump
     */
    async createPump(pumpData) {
      try {
        this.loading = true
        this.error = null
        const newPump = await api.createPump(pumpData)
        this.pumps.push(newPump)
        return newPump
      } catch (error) {
        this.error = 'Failed to create pump'
        console.error('Error creating pump:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * Update a pump
     */
    async updatePump(pumpId, pumpData) {
      try {
        this.loading = true
        this.error = null
        const updatedPump = await api.updatePump(pumpId, pumpData)
        const index = this.pumps.findIndex(p => p.id === pumpId)
        if (index !== -1) {
          this.pumps[index] = updatedPump
        }
        return updatedPump
      } catch (error) {
        this.error = 'Failed to update pump'
        console.error('Error updating pump:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * Delete a pump
     */
    async deletePump(pumpId) {
      try {
        this.loading = true
        this.error = null
        await api.deletePump(pumpId)
        this.pumps = this.pumps.filter(p => p.id !== pumpId)
        // Also remove associated zones
        this.zones = this.zones.filter(z => z.pump_id !== pumpId)
      } catch (error) {
        this.error = 'Failed to delete pump'
        console.error('Error deleting pump:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * Fetch pump status
     */
    async fetchPumpStatus(pumpId) {
      try {
        const status = await api.getPumpStatus(pumpId)
        const pump = this.pumps.find(p => p.id === pumpId)
        if (pump) {
          Object.assign(pump, status)
        }
        return status
      } catch (error) {
        console.error('Error fetching pump status:', error)
      }
    },

    /**
     * Set current pump for zone management
     */
    setCurrentPump(pumpId) {
      this.currentPump = this.getPumpById(pumpId)
    },

    // ==================== Zone Actions ====================

    /**
     * Fetch zones for a pump
     */
    async fetchZones(pumpId) {
      try {
        this.loading = true
        this.error = null
        const zones = await api.getZones(pumpId)
        // Update zones for this pump
        this.zones = this.zones.filter(z => z.pump_id !== pumpId)
        this.zones.push(...zones)
      } catch (error) {
        this.error = 'Failed to fetch zones'
        console.error('Error fetching zones:', error)
      } finally {
        this.loading = false
      }
    },

    /**
     * Create a new zone
     */
    async createZone(pumpId, zoneData) {
      try {
        this.loading = true
        this.error = null
        const newZone = await api.createZone(pumpId, zoneData)
        this.zones.push(newZone)
        return newZone
      } catch (error) {
        this.error = 'Failed to create zone'
        console.error('Error creating zone:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * Update a zone
     */
    async updateZone(zoneId, zoneData) {
      try {
        this.loading = true
        this.error = null
        const updatedZone = await api.updateZone(zoneId, zoneData)
        const index = this.zones.findIndex(z => z.id === zoneId)
        if (index !== -1) {
          this.zones[index] = updatedZone
        }
        return updatedZone
      } catch (error) {
        this.error = 'Failed to update zone'
        console.error('Error updating zone:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * Delete a zone
     */
    async deleteZone(zoneId) {
      try {
        this.loading = true
        this.error = null
        await api.deleteZone(zoneId)
        this.zones = this.zones.filter(z => z.id !== zoneId)
      } catch (error) {
        this.error = 'Failed to delete zone'
        console.error('Error deleting zone:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * Fetch next run time for a zone
     */
    async fetchZoneNextRun(zoneId) {
      try {
        const nextRun = await api.getZoneNextRun(zoneId)
        const zone = this.zones.find(z => z.id === zoneId)
        if (zone) {
          zone.next_run = nextRun.next_run
        }
        return nextRun
      } catch (error) {
        console.error('Error fetching zone next run:', error)
      }
    },

    /**
     * Set current zone for editing
     */
    setCurrentZone(zoneId) {
      this.currentZone = this.getZoneById(zoneId)
    },

    // ==================== Settings Actions ====================

    /**
     * Fetch global settings
     */
    async fetchSettings() {
      try {
        this.loading = true
        this.error = null
        this.settings = await api.getGlobalSettings()
      } catch (error) {
        this.error = 'Failed to fetch settings'
        console.error('Error fetching settings:', error)
      } finally {
        this.loading = false
      }
    },

    /**
     * Update global settings
     */
    async updateSettings(settingsData) {
      try {
        this.loading = true
        this.error = null
        this.settings = await api.updateGlobalSettings(settingsData)
        return this.settings
      } catch (error) {
        this.error = 'Failed to update settings'
        console.error('Error updating settings:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    // ==================== Polling Actions ====================

    /**
     * Start real-time status polling (every 5 seconds)
     */
    startPolling() {
      if (this.isPolling) {
        console.debug('Polling already active')
        return
      }

      this.isPolling = true
      console.info('Starting real-time status polling (5-second interval)')
      
      // Initial fetch
      this.fetchPumps()
      
      // Poll every 5 seconds
      this.pollingInterval = setInterval(async () => {
        try {
          // Update pump statuses (silently, don't show errors for polling)
          const pumps = await api.getPumps()
          
          // Update pump data while preserving reactivity
          this.pumps = pumps
          
          // Update next run times for loaded zones (if any)
          // This ensures zone manager view stays up-to-date
          if (this.zones.length > 0) {
            const zoneUpdatePromises = this.zones
              .filter(zone => zone.enabled)
              .map(zone => this.fetchZoneNextRun(zone.id).catch(err => {
                // Silently handle individual zone errors
                console.debug(`Failed to update next run for zone ${zone.id}:`, err.message)
              }))
            
            await Promise.all(zoneUpdatePromises)
          }
          
          console.debug('Status polling update completed')
        } catch (error) {
          // Log polling errors but don't show toast notifications
          // to avoid spamming the user during temporary network issues
          console.warn('Polling error (will retry):', error.message || error)
        }
      }, 5000)
    },

    /**
     * Stop real-time status polling
     */
    stopPolling() {
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval)
        this.pollingInterval = null
        console.info('Stopped real-time status polling')
      }
      this.isPolling = false
    },

    /**
     * Clear error state
     */
    clearError() {
      this.error = null
    }
  }
})
