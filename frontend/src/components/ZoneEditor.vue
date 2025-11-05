<template>
  <div class="zone-editor">
    <div class="editor-header">
      <h3>{{ isEditMode ? 'Edit Zone' : 'Add New Zone' }}</h3>
    </div>

    <form @submit.prevent="handleSubmit" class="editor-form">
      <!-- Zone Name -->
      <div class="form-group">
        <label class="form-label">
          Zone Name
          <span class="required-indicator">*</span>
        </label>
        <input 
          v-model="formData.name"
          type="text"
          class="form-input"
          placeholder="e.g., Tomatoes Zone 1"
          :class="{ 'input-error': errors.name }"
          @input="clearError('name')"
        />
        <p v-if="errors.name" class="error-text">{{ errors.name }}</p>
      </div>

      <!-- Switch Entity Selector -->
      <EntitySelector
        v-model="formData.switch_entity"
        entity-type="switch"
        label="Switch Entity"
        placeholder="Select a switch entity..."
        hint="Select the Home Assistant switch that controls this zone"
        :required="true"
        :error="errors.switch_entity"
        @change="clearError('switch_entity')"
      />

      <!-- Mode Toggle -->
      <div class="form-group">
        <label class="form-label">
          Schedule Mode
          <span class="required-indicator">*</span>
        </label>
        <div class="mode-toggle">
          <label class="mode-option">
            <input 
              type="radio" 
              v-model="formData.mode" 
              value="auto"
              @change="handleModeChange"
            />
            <span class="mode-label">
              <i class="mdi mdi-robot mode-icon"></i>
              Auto Mode
            </span>
            <span class="mode-description">
              Automatically calculate schedule based on global settings
            </span>
          </label>
          
          <label class="mode-option">
            <input 
              type="radio" 
              v-model="formData.mode" 
              value="manual"
              @change="handleModeChange"
            />
            <span class="mode-label">
              <i class="mdi mdi-clock-outline mode-icon"></i>
              Manual Mode
            </span>
            <span class="mode-description">
              Specify exact irrigation times manually
            </span>
          </label>
        </div>
      </div>

      <!-- Auto Mode Fields (shown when mode is 'auto') -->
      <div v-if="formData.mode === 'auto'" class="mode-fields">
        <h4 class="section-title">Auto Mode Configuration</h4>
        
        <div class="form-group">
          <label class="form-label">
            P1 Duration (seconds)
            <span class="required-indicator">*</span>
          </label>
          <input 
            v-model.number="formData.p1_duration_sec"
            type="number"
            class="form-input"
            placeholder="e.g., 60"
            min="1"
            :class="{ 'input-error': errors.p1_duration_sec }"
            @input="clearError('p1_duration_sec')"
          />
          <p class="hint-text">Duration for the first irrigation event of the day</p>
          <p v-if="errors.p1_duration_sec" class="error-text">{{ errors.p1_duration_sec }}</p>
        </div>

        <div class="form-group">
          <label class="form-label">
            P2 Event Count
            <span class="required-indicator">*</span>
          </label>
          <input 
            v-model.number="formData.p2_event_count"
            type="number"
            class="form-input"
            placeholder="e.g., 3"
            min="0"
            :class="{ 'input-error': errors.p2_event_count }"
            @input="clearError('p2_event_count')"
          />
          <p class="hint-text">Number of irrigation events throughout the day</p>
          <p v-if="errors.p2_event_count" class="error-text">{{ errors.p2_event_count }}</p>
        </div>

        <div class="form-group">
          <label class="form-label">
            P2 Duration (seconds)
            <span class="required-indicator">*</span>
          </label>
          <input 
            v-model.number="formData.p2_duration_sec"
            type="number"
            class="form-input"
            placeholder="e.g., 45"
            min="1"
            :class="{ 'input-error': errors.p2_duration_sec }"
            @input="clearError('p2_duration_sec')"
          />
          <p class="hint-text">Duration for each P2 irrigation event</p>
          <p v-if="errors.p2_duration_sec" class="error-text">{{ errors.p2_duration_sec }}</p>
        </div>
      </div>

      <!-- Manual Mode Fields (shown when mode is 'manual') -->
      <div v-if="formData.mode === 'manual'" class="mode-fields">
        <h4 class="section-title">Manual Mode Configuration</h4>
        
        <div class="form-group">
          <label class="form-label">
            P1 Event List
          </label>
          <textarea 
            v-model="formData.p1_manual_list"
            class="form-textarea"
            placeholder="08:00.60&#10;09:30.45"
            rows="3"
            :class="{ 'input-error': errors.p1_manual_list }"
            @input="clearError('p1_manual_list')"
          ></textarea>
          <p class="hint-text">
            Format: HH:MM.SS (one per line)<br>
            Example: 08:00.60 means 8:00 AM for 60 seconds
          </p>
          <p v-if="errors.p1_manual_list" class="error-text">{{ errors.p1_manual_list }}</p>
        </div>

        <div class="form-group">
          <label class="form-label">
            P2 Event List
          </label>
          <textarea 
            v-model="formData.p2_manual_list"
            class="form-textarea"
            placeholder="12:00.45&#10;15:00.45&#10;18:00.45"
            rows="4"
            :class="{ 'input-error': errors.p2_manual_list }"
            @input="clearError('p2_manual_list')"
          ></textarea>
          <p class="hint-text">
            Format: HH:MM.SS (one per line)<br>
            Example: 12:00.45 means 12:00 PM for 45 seconds
          </p>
          <p v-if="errors.p2_manual_list" class="error-text">{{ errors.p2_manual_list }}</p>
        </div>
      </div>

      <!-- Enabled Toggle -->
      <div class="form-group">
        <label class="checkbox-label">
          <input 
            type="checkbox" 
            v-model="formData.enabled"
            class="form-checkbox"
          />
          <span>Enable this zone</span>
        </label>
        <p class="hint-text">Disabled zones will not be scheduled for irrigation</p>
      </div>

      <!-- Form Actions -->
      <div class="form-actions">
        <button 
          type="button" 
          class="btn btn-secondary"
          @click="handleCancel"
          :disabled="saving"
        >
          Cancel
        </button>
        <button 
          type="submit" 
          class="btn btn-primary"
          :disabled="saving"
        >
          {{ saving ? 'Saving...' : (isEditMode ? 'Update Zone' : 'Create Zone') }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import EntitySelector from './EntitySelector.vue'

const props = defineProps({
  zone: {
    type: Object,
    default: null
  },
  pumpId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['save', 'cancel'])

// Computed
const isEditMode = computed(() => props.zone !== null)

// Form data
const formData = ref({
  name: '',
  switch_entity: '',
  mode: 'auto',
  p1_duration_sec: null,
  p2_event_count: null,
  p2_duration_sec: null,
  p1_manual_list: '',
  p2_manual_list: '',
  enabled: true
})

// Errors
const errors = ref({})

// Saving state
const saving = ref(false)

// Initialize form data if editing
watch(() => props.zone, (newZone) => {
  if (newZone) {
    formData.value = {
      name: newZone.name || '',
      switch_entity: newZone.switch_entity || '',
      mode: newZone.mode || 'auto',
      p1_duration_sec: newZone.p1_duration_sec,
      p2_event_count: newZone.p2_event_count,
      p2_duration_sec: newZone.p2_duration_sec,
      p1_manual_list: newZone.p1_manual_list || '',
      p2_manual_list: newZone.p2_manual_list || '',
      enabled: newZone.enabled !== undefined ? newZone.enabled : true
    }
  }
}, { immediate: true })

// Methods
const handleModeChange = () => {
  // Clear errors when mode changes
  errors.value = {}
}

const clearError = (field) => {
  if (errors.value[field]) {
    delete errors.value[field]
  }
}

const validateForm = () => {
  errors.value = {}
  
  // Validate zone name
  if (!formData.value.name || formData.value.name.trim() === '') {
    errors.value.name = 'Zone name is required'
  }
  
  // Validate switch entity
  if (!formData.value.switch_entity) {
    errors.value.switch_entity = 'Switch entity is required'
  }
  
  // Validate mode-specific fields
  if (formData.value.mode === 'auto') {
    if (!formData.value.p1_duration_sec || formData.value.p1_duration_sec < 1) {
      errors.value.p1_duration_sec = 'P1 duration must be at least 1 second'
    }
    
    if (formData.value.p2_event_count === null || formData.value.p2_event_count < 0) {
      errors.value.p2_event_count = 'P2 event count must be 0 or greater'
    }
    
    if (formData.value.p2_event_count > 0) {
      if (!formData.value.p2_duration_sec || formData.value.p2_duration_sec < 1) {
        errors.value.p2_duration_sec = 'P2 duration must be at least 1 second when P2 events are configured'
      }
    }
  } else if (formData.value.mode === 'manual') {
    // Validate manual schedule format
    if (formData.value.p1_manual_list) {
      const p1Valid = validateManualSchedule(formData.value.p1_manual_list)
      if (!p1Valid) {
        errors.value.p1_manual_list = 'Invalid format. Use HH:MM.SS (one per line)'
      }
    }
    
    if (formData.value.p2_manual_list) {
      const p2Valid = validateManualSchedule(formData.value.p2_manual_list)
      if (!p2Valid) {
        errors.value.p2_manual_list = 'Invalid format. Use HH:MM.SS (one per line)'
      }
    }
  }
  
  return Object.keys(errors.value).length === 0
}

const validateManualSchedule = (scheduleText) => {
  if (!scheduleText || scheduleText.trim() === '') {
    return true // Empty is valid
  }
  
  const lines = scheduleText.trim().split('\n')
  const pattern = /^([0-1][0-9]|2[0-3]):([0-5][0-9])\.(\d+)$/
  
  for (const line of lines) {
    const trimmedLine = line.trim()
    if (trimmedLine === '') continue // Skip empty lines
    
    if (!pattern.test(trimmedLine)) {
      return false
    }
  }
  
  return true
}

const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }
  
  saving.value = true
  
  try {
    // Prepare data for submission
    const submitData = {
      name: formData.value.name.trim(),
      switch_entity: formData.value.switch_entity,
      mode: formData.value.mode,
      enabled: formData.value.enabled
    }
    
    // Add mode-specific fields
    if (formData.value.mode === 'auto') {
      submitData.p1_duration_sec = formData.value.p1_duration_sec
      submitData.p2_event_count = formData.value.p2_event_count
      submitData.p2_duration_sec = formData.value.p2_duration_sec
      submitData.p1_manual_list = null
      submitData.p2_manual_list = null
    } else {
      submitData.p1_duration_sec = null
      submitData.p2_event_count = null
      submitData.p2_duration_sec = null
      submitData.p1_manual_list = formData.value.p1_manual_list.trim() || null
      submitData.p2_manual_list = formData.value.p2_manual_list.trim() || null
    }
    
    emit('save', submitData)
  } catch (error) {
    console.error('Form submission error:', error)
  } finally {
    saving.value = false
  }
}

const handleCancel = () => {
  emit('cancel')
}
</script>

<style scoped>
.zone-editor {
  width: 100%;
}

.editor-header {
  margin-bottom: 20px;
}

.editor-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
  color: var(--text-primary-color);
}

.editor-form {
  display: flex;
  flex-direction: column;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--text-primary-color);
  font-size: 14px;
}

.required-indicator {
  color: var(--error-color);
  margin-left: 2px;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--divider-color);
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
  background-color: var(--card-background-color);
  color: var(--text-primary-color);
  transition: border-color 0.2s;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--primary-color);
}

.input-error {
  border-color: var(--error-color);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.hint-text {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary-color);
  line-height: 1.4;
}

.error-text {
  margin-top: 4px;
  font-size: 12px;
  color: var(--error-color);
  font-weight: 500;
}

/* Mode Toggle */
.mode-toggle {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mode-option {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  border: 2px solid var(--divider-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-option:hover {
  border-color: var(--primary-color);
  background-color: rgba(3, 169, 244, 0.05);
}

.mode-option input[type="radio"] {
  margin-top: 2px;
  margin-right: 12px;
  cursor: pointer;
}

.mode-option input[type="radio"]:checked ~ .mode-label {
  color: var(--primary-color);
  font-weight: 600;
}

.mode-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: var(--text-primary-color);
  font-size: 14px;
}

.mode-icon {
  font-size: 20px;
  color: var(--primary-color);
}

.mode-description {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary-color);
  font-weight: normal;
  margin-left: 30px;
}

/* Mode Fields */
.mode-fields {
  background-color: var(--secondary-background-color);
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary-color);
}

/* Checkbox */
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-primary-color);
}

.form-checkbox {
  cursor: pointer;
  width: 18px;
  height: 18px;
}

/* Form Actions */
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--divider-color);
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.btn-primary {
  background-color: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-secondary {
  background-color: var(--secondary-background-color);
  color: var(--text-primary-color);
}

.btn-secondary:hover:not(:disabled) {
  background-color: var(--divider-color);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 768px) {
  .form-actions {
    flex-direction: column-reverse;
  }
  
  .form-actions .btn {
    width: 100%;
  }
}
</style>
