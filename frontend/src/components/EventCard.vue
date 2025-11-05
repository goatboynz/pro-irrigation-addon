<template>
  <div class="event-card">
    <div class="event-header">
      <div class="event-title">
        <div class="title-row">
          <span class="event-type-badge" :class="eventTypeClass">{{ eventTypeLabel }}</span>
          <h3>{{ event.name }}</h3>
        </div>
        <StatusBadge :status="event.enabled ? 'active' : 'disabled'" />
      </div>
      <div class="event-actions">
        <button class="icon-btn" @click="handleEdit" title="Edit Event">✏️</button>
        <button class="icon-btn danger" @click="handleDelete" title="Delete Event">🗑️</button>
      </div>
    </div>

    <div class="event-info">
      <div class="info-row">
        <span class="label">Timing:</span>
        <span class="value">{{ timingDisplay }}</span>
      </div>
      <div class="info-row">
        <span class="label">Duration:</span>
        <span class="value">{{ durationDisplay }}</span>
      </div>
      <div class="info-row">
        <span class="label">Zones:</span>
        <span class="value">{{ zonesDisplay }}</span>
      </div>
    </div>

    <div v-if="event.zones && event.zones.length > 0" class="assigned-zones">
      <h4>Assigned Zones</h4>
      <div class="zones-list">
        <span v-for="zone in event.zones" :key="zone.id" class="zone-tag">
          {{ zone.name }}
        </span>
      </div>
    </div>

    <ConfirmDialog
      :isOpen="showDeleteDialog"
      title="Delete Water Event"
      :message="`Are you sure you want to delete event '${event.name}'?`"
      confirmText="Delete"
      cancelText="Cancel"
      variant="danger"
      @confirm="confirmDelete"
      @close="showDeleteDialog = false"
    />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import StatusBadge from './StatusBadge.vue'
import ConfirmDialog from './ConfirmDialog.vue'

const props = defineProps({
  event: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['edit', 'delete'])

const showDeleteDialog = ref(false)

const eventTypeClass = computed(() => {
  return props.event.event_type === 'p1' ? 'type-p1' : 'type-p2'
})

const eventTypeLabel = computed(() => {
  return props.event.event_type.toUpperCase()
})

const timingDisplay = computed(() => {
  if (props.event.event_type === 'p1') {
    return `${props.event.delay_minutes} minutes after lights on`
  } else {
    return `At ${props.event.time_of_day}`
  }
})

const durationDisplay = computed(() => {
  const seconds = props.event.run_time_seconds
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  
  if (minutes > 0 && remainingSeconds > 0) {
    return `${minutes}m ${remainingSeconds}s`
  } else if (minutes > 0) {
    return `${minutes}m`
  } else {
    return `${seconds}s`
  }
})

const zonesDisplay = computed(() => {
  const count = props.event.zones ? props.event.zones.length : 0
  return count === 1 ? '1 zone' : `${count} zones`
})

function handleEdit() {
  emit('edit', props.event)
}

function handleDelete() {
  showDeleteDialog.value = true
}

function confirmDelete() {
  emit('delete', props.event)
  showDeleteDialog.value = false
}
</script>

<style scoped>
.event-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: box-shadow 0.2s;
}

.event-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.event-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #f0f0f0;
}

.event-title {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.event-type-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.type-p1 {
  background-color: #e3f2fd;
  color: #1565c0;
}

.type-p2 {
  background-color: #f3e5f5;
  color: #6a1b9a;
}

.event-title h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #2c3e50;
}

.event-actions {
  display: flex;
  gap: 0.5rem;
}

.event-info {
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
  font-weight: 600;
}

.assigned-zones {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #f0f0f0;
}

.assigned-zones h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.9rem;
  color: #666;
  font-weight: 600;
}

.zones-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.zone-tag {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  background: #f0f0f0;
  border-radius: 16px;
  font-size: 0.875rem;
  color: #2c3e50;
  font-weight: 500;
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

.icon-btn.danger:hover {
  filter: brightness(1.2);
}
</style>
