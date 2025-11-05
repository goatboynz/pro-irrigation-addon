<template>
  <div class="settings">
    <div class="settings-header">
      <h1>System Settings</h1>
    </div>

    <div v-if="loading" class="loading">
      Loading settings...
    </div>

    <div v-else-if="error" class="error-message">
      <p>Error loading settings: {{ error }}</p>
      <button @click="loadSettings" class="btn-secondary">Retry</button>
    </div>

    <div v-else class="settings-content">
      <!-- Settings Form -->
      <div class="settings-card">
        <h2>Timing Configuration</h2>
        <p class="card-description">Configure system timing parameters for pump and zone operations.</p>

        <form @submit.prevent="saveSettings" class="settings-form">
          <div class="form-group">
            <label for="pump-startup-delay">Pump Startup Delay (seconds)</label>
            <input
              id="pump-startup-delay"
              v-model.number="formData.pump_startup_delay_seconds"
              type="number"
              min="0"
              step="1"
              required
              class="form-input"
            />
            <p class="field-hint">Delay before opening zone after pump starts</p>
          </div>

          <div class="form-group">
            <label for="zone-switch-delay">Zone Switch Delay (seconds)</label>
            <input
              id="zone-switch-delay"
              v-model.number="formData.zone_switch_delay_seconds"
              type="number"
              min="0"
              step="1"
              required
              class="form-input"
            />
            <p class="field-hint">Delay between closing one zone and opening next</p>
          </div>

          <div class="form-group">
            <label for="scheduler-interval">Scheduler Interval (seconds)</label>
            <input
              id="scheduler-interval"
              v-model.number="formData.scheduler_interval_seconds"
              type="number"
              min="1"
              step="1"
              required
              class="form-input"
            />
            <p class="field-hint">How often scheduler checks for events (minimum 1 second)</p>
          </div>

          <div class="form-actions">
            <button 
              type="submit" 
              class="btn-primary"
              :disabled="saving"
            >
              {{ saving ? 'Saving...' : 'Save Settings' }}
            </button>
            <button 
              type="button" 
              @click="resetForm" 
              class="btn-secondary"
              :disabled="saving"
            >
              Reset
            </button>
          </div>

          <div v-if="saveSuccess" class="success-message">
            Settings saved successfully!
          </div>
          <div v-if="saveError" class="error-message">
            Error saving settings: {{ saveError }}
          </div>
        </form>
      </div>

      <!-- System Reset Section -->
      <div class="settings-card danger-zone">
        <h2>Danger Zone</h2>
        <p class="card-description">Irreversible actions that will affect your system data.</p>

        <div class="danger-action">
          <div class="danger-info">
            <h3>Delete All Data</h3>
            <p>This will permanently delete all rooms, pumps, zones, water events, and sensors. System settings will be preserved.</p>
          </div>
          <button 
            @click="showResetConfirm = true" 
            class="btn-danger"
            :disabled="resetting"
          >
            {{ resetting ? 'Deleting...' : 'Delete All Data' }}
          </button>
        </div>

        <div v-if="resetSuccess" class="success-message">
          All data deleted successfully!
        </div>
        <div v-if="resetError" class="error-message">
          Error deleting data: {{ resetError }}
        </div>
      </div>
    </div>

    <!-- Confirmation Dialog -->
    <div v-if="showResetConfirm" class="modal-overlay" @click="showResetConfirm = false">
      <div class="modal-content" @click.stop>
        <h3>Confirm Data Deletion</h3>
        <p>Are you sure you want to delete all data? This action cannot be undone.</p>
        <p class="warning-text">This will delete:</p>
        <ul class="deletion-list">
          <li>All rooms</li>
          <li>All pumps</li>
          <li>All zones</li>
          <li>All water events</li>
          <li>All sensors</li>
        </ul>
        <p class="warning-text">System settings will be preserved.</p>
        
        <div class="modal-actions">
          <button @click="confirmReset" class="btn-danger">
            Yes, Delete All Data
          </button>
          <button @click="showResetConfirm = false" class="btn-secondary">
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { settingsApi, systemApi } from '../services/api'

const loading = ref(false)
const error = ref(null)
const saving = ref(false)
const saveSuccess = ref(false)
const saveError = ref(null)
const resetting = ref(false)
const resetSuccess = ref(false)
const resetError = ref(null)
const showResetConfirm = ref(false)

const originalSettings = ref(null)
const formData = ref({
  pump_startup_delay_seconds: 5,
  zone_switch_delay_seconds: 2,
  scheduler_interval_seconds: 60
})

async function loadSettings() {
  loading.value = true
  error.value = null
  try {
    const response = await settingsApi.getSettings()
    originalSettings.value = response.data
    formData.value = {
      pump_startup_delay_seconds: response.data.pump_startup_delay_seconds,
      zone_switch_delay_seconds: response.data.zone_switch_delay_seconds,
      scheduler_interval_seconds: response.data.scheduler_interval_seconds
    }
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  saveSuccess.value = false
  saveError.value = null
  
  try {
    const response = await settingsApi.updateSettings(formData.value)
    originalSettings.value = response.data
    saveSuccess.value = true
    
    // Clear success message after 3 seconds
    setTimeout(() => {
      saveSuccess.value = false
    }, 3000)
  } catch (err) {
    saveError.value = err.message
  } finally {
    saving.value = false
  }
}

function resetForm() {
  if (originalSettings.value) {
    formData.value = {
      pump_startup_delay_seconds: originalSettings.value.pump_startup_delay_seconds,
      zone_switch_delay_seconds: originalSettings.value.zone_switch_delay_seconds,
      scheduler_interval_seconds: originalSettings.value.scheduler_interval_seconds
    }
  }
  saveSuccess.value = false
  saveError.value = null
}

async function confirmReset() {
  showResetConfirm.value = false
  resetting.value = true
  resetSuccess.value = false
  resetError.value = null
  
  try {
    await systemApi.reset()
    resetSuccess.value = true
    
    // Clear success message after 5 seconds
    setTimeout(() => {
      resetSuccess.value = false
    }, 5000)
  } catch (err) {
    resetError.value = err.message
  } finally {
    resetting.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings {
  padding: 1rem;
  max-width: 800px;
  margin: 0 auto;
}

.settings-header {
  margin-bottom: 2rem;
}

.settings-header h1 {
  margin: 0;
  font-size: 2rem;
  color: #2c3e50;
}

.loading,
.error-message {
  text-align: center;
  padding: 3rem 1rem;
}

.loading {
  color: #7f8c8d;
}

.error-message {
  color: #e74c3c;
}

.error-message button {
  margin-top: 1rem;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.settings-card {
  background: white;
  border: 1px solid #e1e8ed;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.settings-card h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  color: #2c3e50;
}

.card-description {
  margin: 0 0 1.5rem 0;
  color: #7f8c8d;
  font-size: 0.95rem;
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
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

.form-input {
  padding: 0.75rem;
  border: 1px solid #dce1e6;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.form-input:focus {
  outline: none;
  border-color: #3498db;
}

.field-hint {
  margin: 0;
  font-size: 0.85rem;
  color: #7f8c8d;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
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
  background-color: #ecf0f1;
  cursor: not-allowed;
}

.success-message {
  padding: 0.75rem;
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
  border-radius: 6px;
  font-size: 0.95rem;
}

.danger-zone {
  border-color: #e74c3c;
}

.danger-action {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
}

.danger-info h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  color: #2c3e50;
}

.danger-info p {
  margin: 0;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.btn-danger {
  padding: 0.75rem 1.5rem;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
  white-space: nowrap;
}

.btn-danger:hover:not(:disabled) {
  background-color: #c0392b;
}

.btn-danger:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

/* Modal Styles */
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
  padding: 2rem;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.modal-content h3 {
  margin: 0 0 1rem 0;
  font-size: 1.5rem;
  color: #2c3e50;
}

.modal-content p {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.warning-text {
  color: #e74c3c;
  font-weight: 600;
}

.deletion-list {
  margin: 0.5rem 0 1rem 1.5rem;
  color: #2c3e50;
}

.deletion-list li {
  margin: 0.25rem 0;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
}

.modal-actions button {
  flex: 1;
}

@media (max-width: 768px) {
  .danger-action {
    flex-direction: column;
    align-items: stretch;
  }
  
  .btn-danger {
    width: 100%;
  }
}
</style>
