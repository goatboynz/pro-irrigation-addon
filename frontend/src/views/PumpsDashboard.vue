<template>
  <div class="pumps-dashboard">
    <div class="container">
      <!-- Header -->
      <div class="dashboard-header">
        <h1>
          <i class="mdi mdi-water-pump"></i>
          Pumps Dashboard
        </h1>
        <button 
          class="btn btn-primary add-pump-btn"
          @click="showAddPumpModal = true"
        >
          <i class="mdi mdi-plus"></i>
          <span>Add New Pump</span>
        </button>
      </div>

      <!-- Loading state with skeleton -->
      <div v-if="loading && pumps.length === 0" class="pumps-grid">
        <PumpCardSkeleton v-for="n in 3" :key="`skeleton-${n}`" />
      </div>

      <!-- Empty state -->
      <div v-else-if="!loading && pumps.length === 0" class="empty-state">
        <i class="mdi mdi-water-pump-off empty-icon"></i>
        <h2>No Pumps Configured</h2>
        <p>Get started by adding your first irrigation pump</p>
        <button 
          class="btn btn-primary"
          @click="showAddPumpModal = true"
        >
          <i class="mdi mdi-plus"></i>
          <span>Add Your First Pump</span>
        </button>
      </div>

      <!-- Pumps grid -->
      <div v-else class="pumps-grid">
        <PumpCard 
          v-for="pump in pumps" 
          :key="pump.id"
          :pump="pump"
        />
      </div>

      <!-- Add Pump Modal -->
      <div v-if="showAddPumpModal" class="modal-overlay" @click="closeModal">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h2>
              <i class="mdi mdi-water-pump"></i>
              Add New Pump
            </h2>
            <button class="close-btn" @click="closeModal">
              <i class="mdi mdi-close"></i>
            </button>
          </div>

          <form @submit.prevent="handleCreatePump" class="pump-form">
            <div class="form-group">
              <label class="form-label" for="pump-name">
                Pump Name <span class="required">*</span>
              </label>
              <input
                id="pump-name"
                v-model="newPump.name"
                type="text"
                class="form-input"
                placeholder="e.g., Main Pump, Greenhouse Pump"
                required
              />
              <small class="form-hint">Give your pump a descriptive name</small>
            </div>

            <div class="form-group">
              <label class="form-label" for="lock-entity">
                Lock Entity <span class="required">*</span>
              </label>
              <select
                id="lock-entity"
                v-model="newPump.lock_entity"
                class="form-select"
                required
                :disabled="loadingEntities"
              >
                <option value="">
                  {{ loadingEntities ? 'Loading entities...' : 'Select a lock entity' }}
                </option>
                <option 
                  v-for="entity in lockEntities" 
                  :key="entity.entity_id"
                  :value="entity.entity_id"
                >
                  {{ entity.friendly_name || entity.entity_id }}
                </option>
              </select>
              <small class="form-hint">
                Select an input_boolean entity to use as the pump lock
              </small>
            </div>

            <div v-if="formError" class="error-message">
              {{ formError }}
            </div>

            <div class="modal-actions">
              <button 
                type="button" 
                class="btn btn-secondary"
                @click="closeModal"
              >
                Cancel
              </button>
              <button 
                type="submit" 
                class="btn btn-primary"
                :disabled="submitting"
              >
                {{ submitting ? 'Creating...' : 'Create Pump' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useIrrigationStore } from '../stores/irrigation'
import { storeToRefs } from 'pinia'
import PumpCard from '../components/PumpCard.vue'
import PumpCardSkeleton from '../components/PumpCardSkeleton.vue'
import api from '../services/api'

const store = useIrrigationStore()
const { pumps, loading } = storeToRefs(store)

// Modal state
const showAddPumpModal = ref(false)
const loadingEntities = ref(false)
const lockEntities = ref([])
const submitting = ref(false)
const formError = ref(null)

// New pump form data
const newPump = ref({
  name: '',
  lock_entity: ''
})

// Load pumps on mount
onMounted(async () => {
  await store.fetchPumps()
  store.startPolling()
})

// Stop polling on unmount
onUnmounted(() => {
  store.stopPolling()
})

// Load lock entities when modal opens
const loadLockEntities = async () => {
  try {
    loadingEntities.value = true
    lockEntities.value = await api.getAvailableEntities('input_boolean')
  } catch (error) {
    console.error('Failed to load lock entities:', error)
    formError.value = 'Failed to load available entities'
  } finally {
    loadingEntities.value = false
  }
}

// Watch for modal open to load entities
const openModal = () => {
  showAddPumpModal.value = true
  loadLockEntities()
}

// Close modal and reset form
const closeModal = () => {
  showAddPumpModal.value = false
  newPump.value = {
    name: '',
    lock_entity: ''
  }
  formError.value = null
}

// Handle pump creation
const handleCreatePump = async () => {
  try {
    submitting.value = true
    formError.value = null

    // Validate form
    if (!newPump.value.name.trim()) {
      formError.value = 'Pump name is required'
      return
    }

    if (!newPump.value.lock_entity) {
      formError.value = 'Lock entity is required'
      return
    }

    // Create pump
    await store.createPump({
      name: newPump.value.name.trim(),
      lock_entity: newPump.value.lock_entity
    })

    // Close modal on success
    closeModal()
    
    // Show success notification
    window.dispatchEvent(new CustomEvent('api-success', {
      detail: { message: 'Pump created successfully' }
    }))
  } catch (error) {
    formError.value = error.response?.data?.detail || 'Failed to create pump'
  } finally {
    submitting.value = false
  }
}

// Update the button click to use openModal
const handleAddPumpClick = () => {
  openModal()
}
</script>

<style scoped>
.pumps-dashboard {
  padding: 20px;
  min-height: 100vh;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  gap: 16px;
  flex-wrap: wrap;
}

h1 {
  margin: 0;
  color: var(--text-primary-color);
  font-size: 28px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 12px;
}

h1 i {
  font-size: 32px;
  color: var(--primary-color);
}

.add-pump-btn {
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 6px;
}

.add-pump-btn i {
  font-size: 18px;
}

/* Loading state */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--text-secondary-color);
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 80px;
  margin-bottom: 16px;
  color: var(--text-disabled-color);
}

.empty-state .btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.empty-state .btn i {
  font-size: 18px;
}

.empty-state h2 {
  color: var(--text-primary-color);
  margin-bottom: 8px;
}

.empty-state p {
  color: var(--text-secondary-color);
  margin-bottom: 24px;
}

/* Pumps grid */
.pumps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

/* Modal styles */
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
  padding: 20px;
}

.modal-content {
  background: var(--card-background-color);
  border-radius: 8px;
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid var(--divider-color);
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
  color: var(--text-primary-color);
  display: flex;
  align-items: center;
  gap: 8px;
}

.modal-header h2 i {
  font-size: 24px;
  color: var(--primary-color);
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary-color);
  cursor: pointer;
  padding: 4px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.2s, color 0.2s;
}

.close-btn i {
  font-size: 24px;
}

.close-btn:hover {
  background-color: var(--divider-color);
  color: var(--text-primary-color);
}

.pump-form {
  padding: 20px;
}

.form-hint {
  display: block;
  margin-top: 4px;
  color: var(--text-secondary-color);
  font-size: 12px;
}

.required {
  color: var(--error-color);
}

.error-message {
  padding: 12px;
  background-color: #ffebee;
  color: var(--error-color);
  border-radius: 4px;
  margin-bottom: 16px;
  font-size: 14px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

/* Responsive design */
@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    align-items: stretch;
  }

  .add-pump-btn {
    width: 100%;
  }

  .pumps-grid {
    grid-template-columns: 1fr;
  }
}
</style>
