<template>
  <div class="zone-manager">
    <div class="container">
      <!-- Header with back button and pump name -->
      <div class="manager-header">
        <button class="btn-back" @click="handleBack">
          <i class="mdi mdi-arrow-left"></i>
          <span>Back to Dashboard</span>
        </button>
        <div class="header-content">
          <h1>
            <i class="mdi mdi-water-pump"></i>
            {{ pumpName }}
          </h1>
          <p class="subtitle">Zone Management</p>
        </div>
        <button 
          class="btn btn-primary add-zone-btn"
          @click="openAddZoneModal"
        >
          <i class="mdi mdi-plus"></i>
          <span>Add New Zone</span>
        </button>
      </div>

      <!-- Loading state -->
      <div v-if="loading && zones.length === 0" class="loading-container">
        <div class="spinner"></div>
        <p>Loading zones...</p>
      </div>

      <!-- Empty state -->
      <div v-else-if="!loading && zones.length === 0" class="empty-state">
        <i class="mdi mdi-sprinkler-variant empty-icon"></i>
        <h2>No Zones Configured</h2>
        <p>Add your first irrigation zone to this pump</p>
        <button 
          class="btn btn-primary"
          @click="openAddZoneModal"
        >
          <i class="mdi mdi-plus"></i>
          <span>Add Your First Zone</span>
        </button>
      </div>

      <!-- Zones list -->
      <div v-else class="zones-list">
        <ZoneListItem 
          v-for="zone in zones" 
          :key="zone.id"
          :zone="zone"
          @edit="handleEditZone"
          @delete="handleDeleteZone"
        />
      </div>

      <!-- Zone Editor Modal -->
      <div v-if="showEditorModal" class="modal-overlay" @click="closeEditorModal">
        <div class="modal-content modal-large" @click.stop>
          <div class="modal-header">
            <h2>
              <i class="mdi mdi-sprinkler-variant"></i>
              {{ editingZone ? 'Edit Zone' : 'Add New Zone' }}
            </h2>
            <button class="close-btn" @click="closeEditorModal">
              <i class="mdi mdi-close"></i>
            </button>
          </div>

          <div class="modal-body">
            <ZoneEditor
              :zone="editingZone"
              :pump-id="pumpIdNumber"
              @save="handleSaveZone"
              @cancel="closeEditorModal"
            />
          </div>
        </div>
      </div>

      <!-- Delete Confirmation Modal -->
      <div v-if="showDeleteModal" class="modal-overlay" @click="closeDeleteModal">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h2>
              <i class="mdi mdi-alert-circle"></i>
              Delete Zone
            </h2>
            <button class="close-btn" @click="closeDeleteModal">
              <i class="mdi mdi-close"></i>
            </button>
          </div>

          <div class="modal-body">
            <p>Are you sure you want to delete the zone <strong>{{ zoneToDelete?.name }}</strong>?</p>
            <p class="warning-text">This action cannot be undone.</p>
          </div>

          <div class="modal-actions">
            <button 
              type="button" 
              class="btn btn-secondary"
              @click="closeDeleteModal"
            >
              Cancel
            </button>
            <button 
              type="button" 
              class="btn btn-danger"
              @click="confirmDelete"
              :disabled="deleting"
            >
              {{ deleting ? 'Deleting...' : 'Delete Zone' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useIrrigationStore } from '../stores/irrigation'
import { storeToRefs } from 'pinia'
import ZoneListItem from '../components/ZoneListItem.vue'
import ZoneEditor from '../components/ZoneEditor.vue'

const props = defineProps({
  pumpId: {
    type: [String, Number],
    required: true
  }
})

const router = useRouter()
const store = useIrrigationStore()
const { loading } = storeToRefs(store)

// Local state
const showEditorModal = ref(false)
const editingZone = ref(null)
const showDeleteModal = ref(false)
const zoneToDelete = ref(null)
const deleting = ref(false)

// Computed properties
const pumpIdNumber = computed(() => parseInt(props.pumpId))

const pump = computed(() => store.getPumpById(pumpIdNumber.value))

const pumpName = computed(() => {
  return pump.value?.name || 'Unknown Pump'
})

const zones = computed(() => {
  return store.getZonesByPumpId(pumpIdNumber.value)
})

// Load data on mount
onMounted(async () => {
  // Set current pump in store
  store.setCurrentPump(pumpIdNumber.value)
  
  // Fetch pump if not already loaded
  if (!pump.value) {
    await store.fetchPumps()
  }
  
  // Fetch zones for this pump
  await store.fetchZones(pumpIdNumber.value)
  
  // Start polling for real-time updates
  store.startPolling()
})

// Stop polling on unmount
onUnmounted(() => {
  store.stopPolling()
})

// Navigation handlers
const handleBack = () => {
  router.push({ name: 'dashboard' })
}

// Zone handlers
const handleEditZone = (zone) => {
  editingZone.value = zone
  showEditorModal.value = true
}

const handleDeleteZone = (zone) => {
  zoneToDelete.value = zone
  showDeleteModal.value = true
}

const closeDeleteModal = () => {
  showDeleteModal.value = false
  zoneToDelete.value = null
}

const confirmDelete = async () => {
  if (!zoneToDelete.value) return
  
  try {
    deleting.value = true
    await store.deleteZone(zoneToDelete.value.id)
    
    // Show success notification
    window.dispatchEvent(new CustomEvent('api-success', {
      detail: { message: 'Zone deleted successfully' }
    }))
    
    closeDeleteModal()
  } catch (error) {
    console.error('Failed to delete zone:', error)
  } finally {
    deleting.value = false
  }
}

// Editor handlers
const openAddZoneModal = () => {
  editingZone.value = null
  showEditorModal.value = true
}

const closeEditorModal = () => {
  showEditorModal.value = false
  editingZone.value = null
}

const handleSaveZone = async (zoneData) => {
  try {
    if (editingZone.value) {
      // Update existing zone
      await store.updateZone(editingZone.value.id, zoneData)
      
      window.dispatchEvent(new CustomEvent('api-success', {
        detail: { message: 'Zone updated successfully' }
      }))
    } else {
      // Create new zone
      await store.createZone(pumpIdNumber.value, zoneData)
      
      window.dispatchEvent(new CustomEvent('api-success', {
        detail: { message: 'Zone created successfully' }
      }))
    }
    
    // Close modal and refresh zones
    closeEditorModal()
    await store.fetchZones(pumpIdNumber.value)
  } catch (error) {
    console.error('Failed to save zone:', error)
  }
}
</script>

<style scoped>
.zone-manager {
  padding: 20px;
  min-height: 100vh;
}

.manager-header {
  margin-bottom: 24px;
}

.btn-back {
  background: none;
  border: none;
  color: var(--primary-color);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  padding: 8px 0;
  margin-bottom: 16px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: opacity 0.2s;
}

.btn-back i {
  font-size: 18px;
}

.btn-back:hover {
  opacity: 0.8;
}

.header-content {
  margin-bottom: 16px;
}

h1 {
  margin: 0 0 4px 0;
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

.subtitle {
  margin: 0;
  color: var(--text-secondary-color);
  font-size: 14px;
}

.add-zone-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.add-zone-btn i {
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

.empty-state h2 {
  color: var(--text-primary-color);
  margin-bottom: 8px;
}

.empty-state p {
  color: var(--text-secondary-color);
  margin-bottom: 24px;
}

.empty-state .btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.empty-state .btn i {
  font-size: 18px;
}

/* Zones list */
.zones-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
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

.modal-large {
  max-width: 700px;
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

.modal-header h2 i.mdi-alert-circle {
  color: var(--error-color);
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

.modal-body {
  padding: 20px;
}

.modal-large .modal-body {
  padding: 24px;
}

.modal-body p {
  margin-bottom: 12px;
  color: var(--text-primary-color);
}

.warning-text {
  color: var(--error-color);
  font-size: 14px;
  font-weight: 500;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid var(--divider-color);
}

.btn-danger {
  background-color: var(--error-color);
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: opacity 0.3s ease;
}

.btn-danger:hover {
  opacity: 0.9;
}

.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Responsive design */
@media (min-width: 768px) {
  .add-zone-btn {
    width: auto;
  }
}
</style>
