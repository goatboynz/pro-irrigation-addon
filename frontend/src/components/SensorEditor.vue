<template>
  <div v-if="show" class="modal-overlay" @click.self="handleCancel">
    <div class="modal-content">
      <div class="modal-header">
        <h2>{{ isEditMode ? 'Edit Sensor' : 'Add Sensor' }}</h2>
        <button @click="handleCancel" class="btn-close">&times;</button>
      </div>
      
      <div class="modal-body">
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="displayName">Display Name *</label>
            <input 
              id="displayName"
              v-model="formData.display_name" 
              type="text" 
              placeholder="e.g., Soil Moisture - Plant 1"
              required
              class="form-input"
              :disabled="saving"
            />
          </div>

          <div class="form-group">
            <EntitySelector 
              v-model="formData.sensor_entity"
              label="Sensor Entity *"
              placeholder="Select sensor entity"
              :filter="filterSensorEntities"
              :disabled="saving"
            />
            <p class="field-hint">Home Assistant sensor entity (e.g., sensor.soil_moisture_1)</p>
          </div>

          <div class="form-group">
            <label for="sensorType">Sensor Type *</label>
            <select 
              id="sensorType"
              v-model="formData.sensor_type"
              required
              class="form-input"
              :disabled="saving"
            >
              <option value="">Select sensor type...</option>
              <option value="soil_rh">Soil Moisture (RH)</option>
              <option value="ec">Electrical Conductivity (EC)</option>
              <option value="temperature">Temperature</option>
              <option value="humidity">Humidity</option>
              <option value="light">Light</option>
              <option value="ph">pH</option>
              <option value="other">Other</option>
            </select>
            <p class="field-hint">Type of environmental sensor</p>
          </div>

          <div class="form-group">
            <label for="unit">Unit (Optional)</label>
            <input 
              id="unit"
              v-model="formData.unit" 
              type="text" 
              placeholder="e.g., %, °C, lux"
              class="form-input"
              :disabled="saving"
            />
            <p class="field-hint">Unit of measurement (leave empty to use sensor's default)</p>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input 
                type="checkbox" 
                v-model="formData.enabled"
                :disabled="saving"
              />
              <span>Enable sensor</span>
            </label>
            <p class="field-hint">When enabled, sensor data will be available for monitoring</p>
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
              {{ saving ? 'Saving...' : (isEditMode ? 'Update Sensor' : 'Add Sensor') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import api from '../services/api'
import EntitySelector from './EntitySelector.vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  sensor: {
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
  display_name: '',
  sensor_entity: '',
  sensor_type: '',
  unit: '',
  enabled: true
})

const saving = ref(false)
const error = ref(null)

const isEditMode = computed(() => props.sensor !== null)

const isFormValid = computed(() => {
  return formData.value.display_name.trim().length > 0 && 
         formData.value.sensor_entity.trim().length > 0 &&
         formData.value.sensor_type.trim().length > 0
})

// Filter for sensor entities
function filterSensorEntities(entity) {
  const entityId = entity.entity_id.toLowerCase()
  return entityId.startsWith('sensor.') || 
         entityId.startsWith('binary_sensor.')
}

// Watch for sensor prop changes to populate form
watch(() => props.sensor, (newSensor) => {
  if (newSensor) {
    formData.value = {
      display_name: newSensor.display_name || '',
      sensor_entity: newSensor.sensor_entity || '',
      sensor_type: newSensor.sensor_type || '',
      unit: newSensor.unit || '',
      enabled: newSensor.enabled !== undefined ? newSensor.enabled : true
    }
  } else {
    resetForm()
  }
}, { immediate: true })

// Watch for show prop to reset form when opening
watch(() => props.show, (newShow) => {
  if (newShow && !props.sensor) {
    resetForm()
  }
  error.value = null
})

function resetForm() {
  formData.value = {
    display_name: '',
    sensor_entity: '',
    sensor_type: '',
    unit: '',
    enabled: true
  }
}

async function handleSubmit() {
  if (!isFormValid.value) return

  saving.value = true
  error.value = null

  try {
    const submitData = {
      display_name: formData.value.display_name.trim(),
      sensor_entity: formData.value.sensor_entity.trim(),
      sensor_type: formData.value.sensor_type.trim(),
      unit: formData.value.unit.trim() || null,
      enabled: formData.value.enabled
    }

    if (isEditMode.value) {
      await api.updateSensor(props.sensor.id, submitData)
    } else {
      await api.createSensor(props.roomId, submitData)
    }

    emit('saved')
    emit('close')
  } catch (err) {
    error.value = err.message || 'Failed to save sensor'
    console.error('Error saving sensor:', err)
  } finally {
    saving.value = false
  }
}

function handleCancel() {
  if (!saving.value) {
    emit('close')
  }
}
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
  max-width: 600px;
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
