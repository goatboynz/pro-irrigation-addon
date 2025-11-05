<template>
  <div v-if="show" class="modal-overlay" @click.self="handleCancel">
    <div class="modal-content">
      <div class="modal-header">
        <h2>{{ isEditMode ? 'Edit Room' : 'Create Room' }}</h2>
        <button @click="handleCancel" class="btn-close">&times;</button>
      </div>
      
      <div class="modal-body">
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="roomName">Room Name *</label>
            <input 
              id="roomName"
              v-model="formData.name" 
              type="text" 
              placeholder="e.g., Grow Room 1"
              required
              class="form-input"
              :disabled="saving"
            />
          </div>

          <div class="form-group">
            <EntitySelector 
              v-model="formData.lights_on_entity"
              label="Lights On Entity"
              placeholder="Select lights on entity (optional)"
              :disabled="saving"
            />
            <p class="field-hint">Entity that indicates when lights turn on (used for P1 event scheduling)</p>
          </div>

          <div class="form-group">
            <EntitySelector 
              v-model="formData.lights_off_entity"
              label="Lights Off Entity"
              placeholder="Select lights off entity (optional)"
              :disabled="saving"
            />
            <p class="field-hint">Entity that indicates when lights turn off (used for P2 event scheduling)</p>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input 
                type="checkbox" 
                v-model="formData.enabled"
                :disabled="saving"
              />
              <span>Enable room</span>
            </label>
            <p class="field-hint">When enabled, scheduled water events will run automatically</p>
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
              {{ saving ? 'Saving...' : (isEditMode ? 'Update Room' : 'Create Room') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoomsStore } from '../stores/rooms'
import EntitySelector from './EntitySelector.vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  room: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'saved'])

const roomsStore = useRoomsStore()

const formData = ref({
  name: '',
  lights_on_entity: '',
  lights_off_entity: '',
  enabled: true
})

const saving = ref(false)
const error = ref(null)

const isEditMode = computed(() => props.room !== null)

const isFormValid = computed(() => {
  return formData.value.name.trim().length > 0
})

// Watch for room prop changes to populate form
watch(() => props.room, (newRoom) => {
  if (newRoom) {
    formData.value = {
      name: newRoom.name || '',
      lights_on_entity: newRoom.lights_on_entity || '',
      lights_off_entity: newRoom.lights_off_entity || '',
      enabled: newRoom.enabled !== undefined ? newRoom.enabled : true
    }
  } else {
    resetForm()
  }
}, { immediate: true })

// Watch for show prop to reset form when opening
watch(() => props.show, (newShow) => {
  if (newShow && !props.room) {
    resetForm()
  }
  error.value = null
})

function resetForm() {
  formData.value = {
    name: '',
    lights_on_entity: '',
    lights_off_entity: '',
    enabled: true
  }
}

async function handleSubmit() {
  if (!isFormValid.value) return

  saving.value = true
  error.value = null

  try {
    // Prepare data for API (convert empty strings to null)
    const submitData = {
      name: formData.value.name.trim(),
      lights_on_entity: formData.value.lights_on_entity || null,
      lights_off_entity: formData.value.lights_off_entity || null,
      enabled: formData.value.enabled
    }

    if (isEditMode.value) {
      await roomsStore.updateRoom(props.room.id, submitData)
    } else {
      await roomsStore.createRoom(submitData)
    }

    emit('saved')
    emit('close')
  } catch (err) {
    error.value = err.message || 'Failed to save room'
    console.error('Error saving room:', err)
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
