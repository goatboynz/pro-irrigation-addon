<template>
  <div class="manual-control">
    <div class="control-header">
      <h3>Manual Control</h3>
      <StatusBadge v-if="isRunning" status="running" label="Running" />
      <StatusBadge v-else status="idle" label="Idle" />
    </div>

    <div class="control-form">
      <!-- Zone Selector -->
      <div class="form-group">
        <label for="zone-select">Zone</label>
        <select 
          id="zone-select" 
          v-model="selectedZoneId" 
          :disabled="isRunning"
          class="zone-select"
        >
          <option :value="null" disabled>Select a zone...</option>
          <optgroup v-for="room in roomsWithZones" :key="room.id" :label="room.name">
            <optgroup v-for="pump in room.pumps" :key="pump.id" :label="`  ${pump.name}`">
              <option 
                v-for="zone in pump.zones.filter(z => z.enabled)" 
                :key="zone.id" 
                :value="zone.id"
              >
                {{ zone.name }}
              </option>
            </optgroup>
          </optgroup>
        </select>
      </div>

      <!-- Duration Input -->
      <div class="form-group">
        <label for="duration-input">Duration</label>
        <div class="duration-input-group">
          <input 
            id="duration-input"
            type="number" 
            v-model.number="durationSeconds" 
            :disabled="isRunning"
            min="1"
            placeholder="Seconds"
            class="duration-input"
          />
          <span class="duration-helper">{{ formattedDuration }}</span>
        </div>
        <small class="help-text">Enter duration in seconds (e.g., 60 = 1:00)</small>
      </div>

      <!-- Control Buttons -->
      <div class="control-buttons">
        <button 
          class="primary run-btn" 
          @click="runZone" 
          :disabled="!canRun"
        >
          ▶️ Run Zone
        </button>
        <button 
          class="danger stop-btn" 
          @click="stopPump" 
          :disabled="!isRunning"
        >
          ⏹️ Stop
        </button>
      </div>

      <!-- Progress Indicator -->
      <div v-if="isRunning" class="progress-section">
        <div class="progress-info">
          <div class="progress-text">
            <strong>{{ runningZoneName }}</strong>
            <span class="progress-status">{{ progressStatus }}</span>
          </div>
          <div class="progress-time">
            {{ elapsedTime }} / {{ totalTime }}
          </div>
        </div>
        <div class="progress-bar-container">
          <div class="progress-bar" :style="{ width: progressPercentage + '%' }"></div>
        </div>
      </div>

      <!-- Status Message -->
      <div v-if="statusMessage" :class="['status-message', statusMessageType]">
        {{ statusMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoomsStore } from '../stores/rooms'
import StatusBadge from './StatusBadge.vue'
import api from '../services/api'

const roomsStore = useRoomsStore()

const selectedZoneId = ref(null)
const durationSeconds = ref(60)
const isRunning = ref(false)
const runningZoneName = ref('')
const runningPumpId = ref(null)
const startTime = ref(null)
const endTime = ref(null)
const statusMessage = ref('')
const statusMessageType = ref('info')

let progressInterval = null
let statusCheckInterval = null

// Computed properties
const roomsWithZones = computed(() => {
  return roomsStore.rooms.filter(room => 
    room.pumps && room.pumps.some(pump => 
      pump.zones && pump.zones.length > 0
    )
  )
})

const canRun = computed(() => {
  return selectedZoneId.value !== null && 
         durationSeconds.value > 0 && 
         !isRunning.value
})

const formattedDuration = computed(() => {
  if (!durationSeconds.value || durationSeconds.value < 0) return '0:00'
  const minutes = Math.floor(durationSeconds.value / 60)
  const seconds = durationSeconds.value % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
})

const elapsedTime = computed(() => {
  if (!startTime.value) return '0:00'
  const now = Date.now()
  const elapsed = Math.floor((now - startTime.value) / 1000)
  const minutes = Math.floor(elapsed / 60)
  const seconds = elapsed % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
})

const totalTime = computed(() => {
  if (!startTime.value || !endTime.value) return '0:00'
  const total = Math.floor((endTime.value - startTime.value) / 1000)
  const minutes = Math.floor(total / 60)
  const seconds = total % 60
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
})

const progressPercentage = computed(() => {
  if (!startTime.value || !endTime.value) return 0
  const now = Date.now()
  const total = endTime.value - startTime.value
  const elapsed = now - startTime.value
  const percentage = Math.min(100, Math.max(0, (elapsed / total) * 100))
  return percentage
})

const progressStatus = computed(() => {
  if (progressPercentage.value >= 100) return 'Completing...'
  return 'In Progress'
})

// Methods
async function runZone() {
  if (!selectedZoneId.value || durationSeconds.value <= 0) return

  try {
    const response = await api.manualRun({
      zone_id: selectedZoneId.value,
      duration_seconds: durationSeconds.value
    })

    isRunning.value = true
    runningZoneName.value = response.data.zone_name
    runningPumpId.value = response.data.pump_id
    startTime.value = Date.now()
    endTime.value = startTime.value + (durationSeconds.value * 1000)

    showStatus(`Zone "${response.data.zone_name}" queued for manual run`, 'success')

    // Start progress tracking
    startProgressTracking()
    
    // Start checking pump status
    startStatusChecking()

  } catch (error) {
    showStatus(`Failed to run zone: ${error.message}`, 'error')
    console.error('Error running zone:', error)
  }
}

async function stopPump() {
  if (!runningPumpId.value) return

  try {
    const response = await api.manualStop({
      pump_id: runningPumpId.value
    })

    showStatus(response.data.message, 'success')
    resetRunningState()

  } catch (error) {
    showStatus(`Failed to stop pump: ${error.message}`, 'error')
    console.error('Error stopping pump:', error)
  }
}

function startProgressTracking() {
  if (progressInterval) clearInterval(progressInterval)
  
  progressInterval = setInterval(() => {
    if (Date.now() >= endTime.value) {
      // Job should be complete
      setTimeout(() => {
        resetRunningState()
        showStatus('Manual run completed', 'success')
      }, 3000) // Give 3 seconds buffer for cleanup
    }
  }, 100)
}

function startStatusChecking() {
  if (statusCheckInterval) clearInterval(statusCheckInterval)
  
  // Check pump status every 2 seconds
  statusCheckInterval = setInterval(async () => {
    if (!runningPumpId.value) return
    
    try {
      const response = await api.getPumpStatus(runningPumpId.value)
      
      // If pump becomes idle and we're past the end time, reset
      if (response.data.status === 'idle' && Date.now() >= endTime.value) {
        resetRunningState()
        showStatus('Manual run completed', 'success')
      }
    } catch (error) {
      console.error('Error checking pump status:', error)
    }
  }, 2000)
}

function resetRunningState() {
  isRunning.value = false
  runningZoneName.value = ''
  runningPumpId.value = null
  startTime.value = null
  endTime.value = null
  
  if (progressInterval) {
    clearInterval(progressInterval)
    progressInterval = null
  }
  
  if (statusCheckInterval) {
    clearInterval(statusCheckInterval)
    statusCheckInterval = null
  }
}

function showStatus(message, type = 'info') {
  statusMessage.value = message
  statusMessageType.value = type
  
  setTimeout(() => {
    statusMessage.value = ''
  }, 5000)
}

// Lifecycle hooks
onMounted(async () => {
  // Load rooms with zones
  await roomsStore.fetchRooms()
})

onUnmounted(() => {
  resetRunningState()
})
</script>

<style scoped>
.manual-control {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.control-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f0f0f0;
}

.control-header h3 {
  margin: 0;
  font-size: 1.5rem;
  color: #2c3e50;
}

.control-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.95rem;
}

.zone-select {
  padding: 0.75rem;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  font-size: 1rem;
  background: white;
  cursor: pointer;
  transition: border-color 0.2s;
}

.zone-select:hover:not(:disabled) {
  border-color: #4CAF50;
}

.zone-select:focus {
  outline: none;
  border-color: #4CAF50;
  box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
}

.zone-select:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
  opacity: 0.6;
}

.duration-input-group {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.duration-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.duration-input:hover:not(:disabled) {
  border-color: #4CAF50;
}

.duration-input:focus {
  outline: none;
  border-color: #4CAF50;
  box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
}

.duration-input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
  opacity: 0.6;
}

.duration-helper {
  font-weight: 600;
  color: #4CAF50;
  font-size: 1.1rem;
  min-width: 60px;
  font-family: monospace;
}

.help-text {
  color: #666;
  font-size: 0.875rem;
}

.control-buttons {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
}

.control-buttons button {
  flex: 1;
  padding: 0.875rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.control-buttons button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.run-btn {
  background: #4CAF50;
  color: white;
}

.run-btn:hover:not(:disabled) {
  background: #45a049;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(76, 175, 80, 0.3);
}

.stop-btn {
  background: #f44336;
  color: white;
}

.stop-btn:hover:not(:disabled) {
  background: #da190b;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(244, 67, 54, 0.3);
}

.progress-section {
  background: #f9f9f9;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.progress-text {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.progress-text strong {
  color: #2c3e50;
  font-size: 1rem;
}

.progress-status {
  color: #666;
  font-size: 0.875rem;
}

.progress-time {
  font-family: monospace;
  font-size: 1.1rem;
  font-weight: 600;
  color: #4CAF50;
}

.progress-bar-container {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #66BB6A);
  transition: width 0.3s ease;
  border-radius: 4px;
}

.status-message {
  padding: 0.75rem 1rem;
  border-radius: 6px;
  font-size: 0.95rem;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.status-message.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status-message.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.status-message.info {
  background: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}
</style>
