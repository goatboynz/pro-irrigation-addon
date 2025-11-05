<template>
  <div v-if="show" class="modal-overlay" @click.self="handleCancel">
    <div class="modal-content">
      <div class="modal-header">
        <h2>{{ isEditMode ? 'Edit Water Event' : 'Create Water Event' }}</h2>
        <button @click="handleCancel" class="btn-close">&times;</button>
      </div>
      
      <div class="modal-body">
        <form @submit.prevent="handleSubmit">
          <!-- Event Type Selector -->
          <div class="form-group">
            <label for="eventType">Event Type *</label>
            <select 
              id="eventType"
              v-model="formData.event_type" 
              class="form-input"
              :disabled="saving"
              required
            >
              <option value="p1">P1 - After Lights On</option>
              <option value="p2">P2 - Specific Time</option>
            </select>
            <p class="field-hint">
              P1 events trigger after lights turn on. P2 events run at a specific time of day.
            </p>
          </div>

          <!-- Event Name -->
          <div class="form-group">
            <label for="eventName">Event Name *</label>
            <input 
              id="eventName"
              v-model="formData.name" 
              type="text" 
              placeholder="e.g., Morning Watering"
              required
              class="form-input"
              :disabled="saving"
            />
          </div>

          <!-- P1: Delay Minutes -->
          <div v-if="formData.event_type === 'p1'" class="form-group">
            <label for="delayMinutes">Delay After Lights On (minutes) *</label>
            <input 
              id="delayMinutes"
              v-model.number="formData.delay_minutes" 
              type="number" 
              min="0"
              placeholder="e.g., 30"
              required
              class="form-input"
              :disabled="saving"
            />
            <p class="field-hint">
              Event will trigger this many minutes after the room's lights turn on.
            </p>
          </div>

          <!-- P2: Time of Day -->
          <div v-if="formData.event_type === 'p2'" class="form-group">
            <label for="timeOfDay">Time of Day (HH:MM) *</label>
            <input 
              id="timeOfDay"
              v-model="formData.time_of_day" 
              type="time" 
              required
              class="form-input"
              :disabled="saving"
            />
            <p class="field-hint">
              Event will trigger at this specific time each day.
            </p>
          </div>

          <!-- Run Time -->
          <div class="form-group">
            <label for="runTime">Run Time *</label>
            <div class="time-input-group">
              <div class="time-input-field">
                <input 
                  id="runTimeMinutes"
                  v-model.number="runTimeMinutes" 
                  type="number" 
                  min="0"
                  placeholder="MM"
                  class="form-input time-input"
                  :disabled="saving"
                />
                <span class="time-label">minutes</span>
              </div>
              <span class="time-separator">:</span>
              <div class="time-input-field">
                <input 
                  id="runTimeSeconds"
                  v-model.number="runTimeSeconds" 
                  type="number" 
                  min="0"
                  max="59"
                  placeholder="SS"
                  class="form-input time-input"
                  :disabled="saving"
                />
                <span class="time-label">seconds</span>
              </div>
            </div>
            <p class="field-hint">
              Total: {{ totalRunTimeDisplay }}
            </p>
          </div>

          <!-- Zone Multi-Select -->
          <div class="form-group">
            <label>Assign Zones *</label>
            <div v-if="loadingZones" class="loading-message">
              Loading zones...
            </div>
            <div v-else-if="availableZones.length === 0" class="info-message">
              No zones available. Please create zones first.
            </div>
            <div v-else class="zone-checkboxes">
              <label 
                v-for="zone in availableZones" 
                :key="zone.id"
                class="checkbox-label zone-checkbox"
              >
                <input 
                  type="checkbox" 
                  :value="zone.id"
                  v-model="formData.zone_ids"
                  :disabled="saving"
                />
                <span>{{ zone.name }} ({{ getPumpName(zone.pump_id) }})</span>
              </label>
            </div>
            <p class="field-hint">
              Select one or more zones to water during this event.
            </p>
          </div>

          <!-- Enabled Toggle -->
          <div class="form-group">
            <label class="checkbox-label">
              <input 
                type="checkbox" 
                v-model="formData.enabled"
                :disabled="saving"
              />
              <span>Enable event</span>
            </label>
            <p class="field-hint">When enabled, this event will run automatically according to its schedule</p>
          </div>

          <div v-if="error" class="error-message">
            {{ error }}
          </div>

          <div class="modal-actions">
            <button 
              type="button" 
              @click="handleCancel" 
              class="btn-secondary"
              :disabled="saving"
            >
              Cancel
            </button>
            <button 
              type="submit" 
              class="btn-primary"
              :disabled="saving || !isFormValid"
            >
              {{ saving ? 'Saving...' : (isEditMode ? 'Update Event' : 'Create Event') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import api from '../services/api'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  event: {
    type: Object,
    default: null
  },
  roomId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['close', 'saved'])

const formData = ref({
  event_type: 'p1',
  name: '',
  delay_minutes: null,
  time_of_day: '',
  run_time_seconds: 0,
  zone_ids: [],
  enabled: true
})

const runTimeMinutes = ref(0)
const runTimeSeconds = ref(0)
const availableZones = ref([])
const pumps = ref([])
const loadingZones = ref(false)
const saving = ref(false)
const error = ref(null)

const isEditMode = computed(() => props.event !== null)

const isFormValid = computed(() => {
  const hasName = formData.value.name.trim().length > 0
  const hasZones = formData.value.zone_ids.length > 0
  const hasValidRunTime = formData.value.run_time_seconds > 0
  
  let hasValidTiming = false
  if (formData.value.event_type === 'p1') {
    hasValidTiming = formData.value.delay_minutes !== null && formData.value.delay_minutes >= 0
  } else if (formData.value.event_type === 'p2') {
    hasValidTiming = formData.value.time_of_day.trim().length > 0
  }
  
  return hasName && hasZones && hasValidRunTime && hasValidTiming
})

const totalRunTimeDisplay = computed(() => {
  const totalSeconds = formData.value.run_time_seconds
  if (totalSeconds === 0) return '0 seconds'
  
  const minutes = Math.floor(totalSeconds / 60)
  const seconds = totalSeconds % 60
  
  if (minutes === 0) return `${seconds} seconds`
  if (seconds === 0) return `${minutes} minutes`
  return `${minutes} minutes ${seconds} seconds`
})

function getPumpName(pumpId) {
  const pump = pumps.value.find(p => p.id === pumpId)
  return pump ? pump.name : 'Unknown Pump'
}

// Watch run time inputs and update total seconds
watch([runTimeMinutes, runTimeSeconds], () => {
  const minutes = runTimeMinutes.value || 0
  const seconds = runTimeSeconds.value || 0
  formData.value.run_time_seconds = (minutes * 60) + seconds
})

// Watch event type to clear irrelevant fields
watch(() => formData.value.event_type, (newType) => {
  if (newType === 'p1') {
    formData.value.time_of_day = ''
  } else if (newType === 'p2') {
    formData.value.delay_minutes = null
  }
})

// Watch for event prop changes to populate form
watch(() => props.event, (newEvent) => {
  if (newEvent) {
    formData.value = {
      event_type: newEvent.event_type || 'p1',
      name: newEvent.name || '',
      delay_minutes: newEvent.delay_minutes,
      time_of_day: newEvent.time_of_day || '',
      run_time_seconds: newEvent.run_time_seconds || 0,
      zone_ids: newEvent.zones ? newEvent.zones.map(z => z.id) : [],
      enabled: newEvent.enabled !== undefined ? newEvent.enabled : true
    }
    
    // Update run time display
    const totalSeconds = newEvent.run_time_seconds || 0
    runTimeMinutes.value = Math.floor(totalSeconds / 60)
    runTimeSeconds.value = totalSeconds % 60
  } else {
    resetForm()
  }
}, { immediate: true })

// Watch for show prop to reset form and load zones when opening
watch(() => props.show, (newShow) => {
  if (newShow) {
    if (!props.event) {
      resetForm()
    }
    loadZones()
  }
  error.value = null
})

function resetForm() {
  formData.value = {
    event_type: 'p1',
    name: '',
    delay_minutes: null,
    time_of_day: '',
    run_time_seconds: 0,
    zone_ids: [],
    enabled: true
  }
  runTimeMinutes.value = 0
  runTimeSeconds.value = 0
}

async function loadZones() {
  loadingZones.value = true
  error.value = null
  
  try {
    // Load pumps for the room
    const pumpsResponse = await api.getPumps(props.roomId)
    pumps.value = pumpsResponse.data
    
    // Load zones for each pump
    const allZones = []
    for (const pump of pumps.value) {
      const zonesResponse = await api.getZones(pump.id)
      allZones.push(...zonesResponse.data)
    }
    
    availableZones.value = allZones
  } catch (err) {
    error.value = 'Failed to load zones'
    console.error('Error loading zones:', err)
  } finally {
    loadingZones.value = false
  }
}

async function handleSubmit() {
  if (!isFormValid.value) return

  saving.value = true
  error.value = null

  try {
    const submitData = {
      event_type: formData.value.event_type,
      name: formData.value.name.trim(),
      delay_minutes: formData.value.event_type === 'p1' ? formData.value.delay_minutes : null,
      time_of_day: formData.value.event_type === 'p2' ? formData.value.time_of_day : null,
      run_time_seconds: formData.value.run_time_seconds,
      zone_ids: formData.value.zone_ids,
      enabled: formData.value.enabled
    }

    if (isEditMode.value) {
      // For update, we need to update the event and then sync zones
      const updateData = {
        event_type: submitData.event_type,
        name: submitData.name,
        delay_minutes: submitData.delay_minutes,
        time_of_day: submitData.time_of_day,
        run_time_seconds: submitData.run_time_seconds,
        enabled: submitData.enabled
      }
      await api.updateEvent(props.event.id, updateData)
      
      // Sync zones: remove old ones and add new ones
      const currentZoneIds = props.event.zones ? props.event.zones.map(z => z.id) : []
      const zonesToRemove = currentZoneIds.filter(id => !submitData.zone_ids.includes(id))
      const zonesToAdd = submitData.zone_ids.filter(id => !currentZoneIds.includes(id))
      
      for (const zoneId of zonesToRemove) {
        await api.removeZone(props.event.id, zoneId)
      }
      
      for (const zoneId of zonesToAdd) {
        await api.assignZone(props.event.id, zoneId)
      }
    } else {
      await api.createEvent(props.roomId, submitData)
    }

    emit('saved')
    emit('close')
  } catch (err) {
    error.value = err.message || 'Failed to save water event'
    console.error('Error saving water event:', err)
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  if (!saving.value) {
    emit('close')
  }
}

onMounted(() => {
  if (props.show) {
    loadZones()
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 700px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #ecf0f1;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #2c3e50;
}

.btn-close {
  background: none;
  border: none;
  font-size: 2rem;
  color: #95a5a6;
  cursor: pointer;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.3s;
}

.btn-close:hover {
  color: #2c3e50;
}

.modal-body {
  padding: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #2c3e50;
}

.form-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.form-input:focus {
  outline: none;
  border-color: #3498db;
}

.form-input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

select.form-input {
  cursor: pointer;
}

select.form-input:disabled {
  cursor: not-allowed;
}

.time-input-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.time-input-field {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.time-input {
  width: 100%;
}

.time-separator {
  font-size: 1.5rem;
  font-weight: bold;
  color: #2c3e50;
  margin-top: -1.5rem;
}

.time-label {
  font-size: 0.75rem;
  color: #7f8c8d;
  text-align: center;
}

.zone-checkboxes {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  max-height: 200px;
  overflow-y: auto;
  background-color: #f9f9f9;
}

.zone-checkbox {
  margin: 0;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-weight: 500;
  color: #2c3e50;
}

.checkbox-label input[type="checkbox"] {
  width: 1.25rem;
  height: 1.25rem;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"]:disabled {
  cursor: not-allowed;
}

.field-hint {
  margin-top: 0.25rem;
  font-size: 0.875rem;
  color: #7f8c8d;
  font-style: italic;
}

.loading-message {
  padding: 1rem;
  text-align: center;
  color: #7f8c8d;
  font-style: italic;
}

.info-message {
  padding: 1rem;
  background-color: #e8f4f8;
  border: 1px solid #b8dce8;
  border-radius: 6px;
  color: #2c3e50;
  font-size: 0.9rem;
}

.error-message {
  padding: 0.75rem;
  background-color: #fee;
  border: 1px solid #fcc;
  border-radius: 6px;
  color: #c33;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-primary:hover:not(:disabled) {
  background-color: #2980b9;
}

.btn-primary:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background-color: #ecf0f1;
  color: #2c3e50;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #bdc3c7;
}

.btn-secondary:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
</style>
