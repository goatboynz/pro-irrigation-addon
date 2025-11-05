<template>
  <div class="pump-card">
    <div class="pump-header">
      <div class="pump-title">
        <h3>{{ pump.name }}</h3>
        <StatusBadge :status="pumpStatus" :label="statusLabel" />
      </div>
      <div class="pump-actions">
        <button class="icon-btn" @click="handleEdit" title="Edit Pump">✏️</button>
        <button class="icon-btn danger" @click="handleDelete" title="Delete Pump">🗑️</button>
      </div>
    </div>

    <div class="pump-info">
      <div class="info-row">
        <span class="label">Lock Entity:</span>
        <span class="value">{{ pump.lock_entity }}</span>
      </div>
      <div class="info-row">
        <span class="label">Status:</span>
        <span class="value">{{ pump.enabled ? 'Enabled' : 'Disabled' }}</span>
      </div>
    </div>

    <div class="zones-section">
      <div class="zones-header">
        <h4>Zones ({{ zoneCount }})</h4>
        <button class="small primary" @click="handleAddZone">Add Zone</button>
      </div>
      
      <div v-if="pump.zones && pump.zones.length > 0" class="zones-list">
        <div v-for="zone in pump.zones" :key="zone.id" class="zone-item">
          <div class="zone-info">
            <span class="zone-name">{{ zone.name }}</span>
            <span class="zone-entity">{{ zone.switch_entity }}</span>
            <StatusBadge :status="zone.enabled ? 'active' : 'disabled'" />
          </div>
          <div class="zone-actions">
            <button class="icon-btn small" @click="handleEditZone(zone)" title="Edit Zone">✏️</button>
            <button class="icon-btn small danger" @click="handleDeleteZone(zone)" title="Delete Zone">🗑️</button>
          </div>
        </div>
      </div>
      <div v-else class="empty-zones">
        No zones configured
      </div>
    </div>

    <ConfirmDialog
      :isOpen="showDeleteDialog"
      title="Delete Pump"
      :message="`Are you sure you want to delete pump '${pump.name}'? This will also delete all associated zones.`"
      confirmText="Delete"
      cancelText="Cancel"
      variant="danger"
      @confirm="confirmDelete"
      @close="showDeleteDialog = false"
    />

    <ConfirmDialog
      :isOpen="showDeleteZoneDialog"
      title="Delete Zone"
      :message="`Are you sure you want to delete zone '${zoneToDelete?.name}'?`"
      confirmText="Delete"
      cancelText="Cancel"
      variant="danger"
      @confirm="confirmDeleteZone"
      @close="showDeleteZoneDialog = false"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import StatusBadge from './StatusBadge.vue'
import ConfirmDialog from './ConfirmDialog.vue'

const props = defineProps({
  pump: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['edit', 'delete', 'add-zone', 'edit-zone', 'delete-zone'])

const showDeleteDialog = ref(false)
const showDeleteZoneDialog = ref(false)
const zoneToDelete = ref(null)

const zoneCount = computed(() => {
  return props.pump.zones ? props.pump.zones.length : 0
})

const pumpStatus = computed(() => {
  if (!props.pump.enabled) return 'disabled'
  // TODO: Get real-time status from API
  return 'idle'
})

const statusLabel = computed(() => {
  if (!props.pump.enabled) return 'Disabled'
  // TODO: Show 'Running' or 'Queued' based on real-time status
  return 'Idle'
})

function handleEdit() {
  emit('edit', props.pump)
}

function handleDelete() {
  showDeleteDialog.value = true
}

function confirmDelete() {
  emit('delete', props.pump)
  showDeleteDialog.value = false
}

function handleAddZone() {
  emit('add-zone', props.pump)
}

function handleEditZone(zone) {
  emit('edit-zone', zone)
}

function handleDeleteZone(zone) {
  zoneToDelete.value = zone
  showDeleteZoneDialog.value = true
}

function confirmDeleteZone() {
  emit('delete-zone', zoneToDelete.value)
  showDeleteZoneDialog.value = false
  zoneToDelete.value = null
}
</script>

<style scoped>
.pump-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: box-shadow 0.2s;
}

.pump-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.pump-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f0f0f0;
}

.pump-title {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.pump-title h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #2c3e50;
}

.pump-actions {
  display: flex;
  gap: 0.5rem;
}

.pump-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.875rem;
}

.info-row .label {
  color: #666;
  font-weight: 500;
}

.info-row .value {
  color: #2c3e50;
  font-family: monospace;
  font-size: 0.8rem;
}

.zones-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #f0f0f0;
}

.zones-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.zones-header h4 {
  margin: 0;
  font-size: 1rem;
  color: #2c3e50;
}

.zones-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.zone-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f9f9f9;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
}

.zone-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  flex: 1;
}

.zone-name {
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.9rem;
}

.zone-entity {
  color: #999;
  font-size: 0.75rem;
  font-family: monospace;
}

.zone-actions {
  display: flex;
  gap: 0.25rem;
}

.empty-zones {
  text-align: center;
  padding: 1.5rem;
  color: #999;
  font-size: 0.875rem;
  background: #f9f9f9;
  border-radius: 6px;
  border: 1px dashed #e0e0e0;
}

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.25rem;
  padding: 0.25rem;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.icon-btn:hover {
  opacity: 1;
}

.icon-btn.small {
  font-size: 1rem;
}

.icon-btn.danger:hover {
  filter: brightness(1.2);
}

button.small {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
}
</style>
