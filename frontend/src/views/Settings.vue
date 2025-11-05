<template>
  <div class="settings">
    <div class="container">
      <div class="header">
        <h1>Global Settings</h1>
        <p class="subtitle">Configure system-wide parameters for Auto Mode zones</p>
      </div>

      <div v-if="loading" class="loading-container">
        <div class="spinner"></div>
        <p>Loading settings...</p>
      </div>

      <form v-else @submit.prevent="handleSubmit" class="settings-form">
        <!-- Lighting Schedule Section -->
        <div class="form-section">
          <h2 class="section-title">Lighting Schedule</h2>
          <p class="section-description">
            Define when lights turn on and off. These times are used to calculate Auto Mode irrigation schedules.
          </p>

          <EntitySelector
            v-model="formData.lights_on_entity"
            entity-type="input_datetime"
            label="Lights On Time"
            placeholder="Select lights on time entity..."
            hint="input_datetime entity that defines when lights turn on"
          />

          <EntitySelector
            v-model="formData.lights_off_entity"
            entity-type="input_datetime"
            label="Lights Off Time"
            placeholder="Select lights off time entity..."
            hint="input_datetime entity that defines when lights turn off"
          />
        </div>

        <!-- P1 Timing Section -->
        <div class="form-section">
          <h2 class="section-title">P1 Event Timing</h2>
          <p class="section-description">
            P1 is the first irrigation event of the day, scheduled relative to lights-on time.
          </p>

          <EntitySelector
            v-model="formData.p1_delay_entity"
            entity-type="input_number"
            label="P1 Start Delay"
            placeholder="Select P1 delay entity..."
            hint="input_number entity (in minutes) to add to lights-on time for P1 start"
          />
        </div>

        <!-- P2 Timing Section -->
        <div class="form-section">
          <h2 class="section-title">P2 Event Timing</h2>
          <p class="section-description">
            P2 events are distributed throughout the day between P2 start and P2 end times.
          </p>

          <EntitySelector
            v-model="formData.p2_delay_entity"
            entity-type="input_number"
            label="P2 Start Delay"
            placeholder="Select P2 start delay entity..."
            hint="input_number entity (in minutes) to add to lights-on time for P2 start"
          />

          <EntitySelector
            v-model="formData.p2_buffer_entity"
            entity-type="input_number"
            label="P2 End Buffer"
            placeholder="Select P2 end buffer entity..."
            hint="input_number entity (in minutes) to subtract from lights-off time for P2 end"
          />
        </div>

        <!-- Feed Notes Section -->
        <div class="form-section">
          <h2 class="section-title">Feed Schedule Notes</h2>
          <p class="section-description">
            Optional notes about your feeding schedule for reference.
          </p>

          <div class="form-group">
            <label for="feed-notes" class="form-label">Notes</label>
            <textarea
              id="feed-notes"
              v-model="formData.feed_notes"
              class="form-textarea"
              rows="6"
              placeholder="Enter feed schedule notes, mixing ratios, or other relevant information..."
            ></textarea>
          </div>
        </div>

        <!-- Form Actions -->
        <div class="form-actions">
          <button 
            type="submit" 
            class="btn btn-primary"
            :disabled="saving"
          >
            <span v-if="saving">Saving...</span>
            <span v-else>Save Settings</span>
          </button>
        </div>
      </form>

      <!-- Toast Notification -->
      <div v-if="notification.show" :class="['toast', notification.type]">
        {{ notification.message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import EntitySelector from '../components/EntitySelector.vue'
import api from '../services/api'

// State
const loading = ref(true)
const saving = ref(false)
const notification = ref({
  show: false,
  message: '',
  type: 'success' // 'success' or 'error'
})

const formData = ref({
  lights_on_entity: '',
  lights_off_entity: '',
  p1_delay_entity: '',
  p2_delay_entity: '',
  p2_buffer_entity: '',
  feed_notes: ''
})

// Load settings on mount
onMounted(async () => {
  await loadSettings()
})

// Methods
const loadSettings = async () => {
  try {
    loading.value = true
    const settings = await api.getGlobalSettings()
    
    // Populate form with loaded settings
    formData.value = {
      lights_on_entity: settings.lights_on_entity || '',
      lights_off_entity: settings.lights_off_entity || '',
      p1_delay_entity: settings.p1_delay_entity || '',
      p2_delay_entity: settings.p2_delay_entity || '',
      p2_buffer_entity: settings.p2_buffer_entity || '',
      feed_notes: settings.feed_notes || ''
    }
  } catch (error) {
    console.error('Failed to load settings:', error)
    showNotification('Failed to load settings', 'error')
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  try {
    saving.value = true
    
    // Prepare data for submission (convert empty strings to null)
    const dataToSubmit = {
      lights_on_entity: formData.value.lights_on_entity || null,
      lights_off_entity: formData.value.lights_off_entity || null,
      p1_delay_entity: formData.value.p1_delay_entity || null,
      p2_delay_entity: formData.value.p2_delay_entity || null,
      p2_buffer_entity: formData.value.p2_buffer_entity || null,
      feed_notes: formData.value.feed_notes || null
    }
    
    await api.updateGlobalSettings(dataToSubmit)
    showNotification('Settings saved successfully', 'success')
  } catch (error) {
    console.error('Failed to save settings:', error)
    showNotification('Failed to save settings', 'error')
  } finally {
    saving.value = false
  }
}

const showNotification = (message, type = 'success') => {
  notification.value = {
    show: true,
    message,
    type
  }
  
  // Auto-hide after 3 seconds
  setTimeout(() => {
    notification.value.show = false
  }, 3000)
}
</script>

<style scoped>
.settings {
  padding: 20px;
  min-height: 100vh;
  background-color: var(--primary-background-color);
}

.container {
  max-width: 800px;
  margin: 0 auto;
}

.header {
  margin-bottom: 32px;
}

h1 {
  margin: 0 0 8px 0;
  color: var(--text-primary-color);
  font-size: 28px;
  font-weight: 500;
}

.subtitle {
  margin: 0;
  color: var(--text-secondary-color);
  font-size: 14px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--text-secondary-color);
}

.spinner {
  border: 3px solid var(--divider-color);
  border-top: 3px solid var(--primary-color);
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.settings-form {
  background-color: var(--card-background-color);
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.form-section {
  margin-bottom: 32px;
  padding-bottom: 32px;
  border-bottom: 1px solid var(--divider-color);
}

.form-section:last-of-type {
  border-bottom: none;
  margin-bottom: 24px;
}

.section-title {
  margin: 0 0 8px 0;
  color: var(--text-primary-color);
  font-size: 18px;
  font-weight: 500;
}

.section-description {
  margin: 0 0 20px 0;
  color: var(--text-secondary-color);
  font-size: 14px;
  line-height: 1.5;
}

.form-group {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--text-primary-color);
  font-size: 14px;
}

.form-textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--divider-color);
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
  background-color: var(--card-background-color);
  color: var(--text-primary-color);
  resize: vertical;
  transition: border-color 0.2s;
}

.form-textarea:focus {
  outline: none;
  border-color: var(--primary-color);
}

.form-textarea::placeholder {
  color: var(--text-secondary-color);
  opacity: 0.6;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  padding-top: 8px;
}

.btn {
  padding: 10px 24px;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
}

.btn-primary {
  background-color: var(--primary-color);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--primary-color);
  opacity: 0.9;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Toast Notification */
.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 16px 24px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  animation: slideIn 0.3s ease-out;
  z-index: 1000;
}

.toast.success {
  background-color: #4caf50;
  color: white;
}

.toast.error {
  background-color: #f44336;
  color: white;
}

@keyframes slideIn {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .settings {
    padding: 16px;
  }

  .settings-form {
    padding: 16px;
  }

  h1 {
    font-size: 24px;
  }

  .toast {
    left: 16px;
    right: 16px;
    bottom: 16px;
  }
}
</style>
