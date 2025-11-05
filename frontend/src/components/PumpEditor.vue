<template>
  <div v-if="show" class="modal-overlay" @click.self="handleCancel">
    <div class="modal-content">
      <div class="modal-header">
        <h2>{{ isEditMode ? 'Edit Pump' : 'Create Pump' }}</h2>
        <button @click="handleCancel" class="btn-close">&times;</button>
      </div>
      
      <div class="modal-body">
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="pumpName">Pump Name *</label>
            <input 
              id="pumpName"
              v-model="formData.name" 
              type="text" 
              placeholder="e.g., Main Pump"
              required
              class="form-input"
              :disabled="saving"
            />
          </div>

          <div class="form-group">
            <EntitySelector 
              v-model="formData.lock_entity"
              label="Lock Entity *"
              placeholder="Select pump lock entity"
              :filter="filterLockEntities"
              :disabled="saving"
            />
            <p class="field-hint">Home Assistant entity that controls the pump lock (e.g., switch.pump_lock)</p>
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
              {{ saving ? 'Saving...' : (isEditMode ? 'Update Pump' : 'Create Pump') }}
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
  pump: {
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
  name: '',
  lock_entity: ''
})

const saving = ref(false)
const error = ref(null)

const isEditMode = computed(() => props.pump !== null)

const isFormValid = computed(() => {
  return formData.value.name.trim().length > 0 && 
         formData.value.lock_entity.trim().length > 0
})

// Filter for lock entities (switches, locks, etc.)
function filterLockEntities(entity) {
  const entityId = entity.entity_id.toLowerCase()
  return entityId.startsWith('switch.') || 
         entityId.startsWith('lock.') ||
         entityId.startsWith('input_boolean.')
}

// Watch for pump prop changes to populate form
watch(() => props.pump, (newPump) => {
  if (newPump) {
    formData.value = {
      name: newPump.name || '',
      lock_entity: newPump.lock_entity || ''
    }
  } else {
    resetForm()
  }
}, { immediate: true })

// Watch for show prop to reset form when opening
watch(() => props.show, (newShow) => {
  if (newShow && !props.pump) {
    resetForm()
  }
  error.value = null
})

function resetForm() {
  formData.value = {
    name: '',
    lock_entity: ''
  }
}

async function handleSubmit() {
  if (!isFormValid.value) return

  saving.value = true
  error.value = null

  try {
    const submitData = {
      name: formData.value.name.trim(),
      lock_entity: formData.value.lock_entity.trim()
    }

    if (isEditMode.value) {
      await api.updatePump(props.pump.id, submitData)
    } else {
      await api.createPump(props.roomId, submitData)
    }

    emit('saved')
    emit('close')
  } catch (err) {
    error.value = err.message || 'Failed to save pump'
    console.error('Error saving pump:', err)
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
