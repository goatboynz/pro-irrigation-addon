<template>
  <div class="zone-list-item card card-interactive">
    <div class="zone-header">
      <div class="zone-info">
        <div class="zone-title-row">
          <i 
            :class="['zone-icon', zone.enabled ? 'mdi mdi-sprinkler-variant' : 'mdi mdi-sprinkler-variant']" 
            :style="{ color: zone.enabled ? 'var(--state-icon-color)' : 'var(--text-disabled-color)' }"
            :title="zone.enabled ? 'Enabled' : 'Disabled'"
          ></i>
          <h4 class="zone-name">{{ zone.name }}</h4>
        </div>
        <div class="zone-meta">
          <span :class="['badge', `badge-${zone.mode}`]">
            <i :class="zone.mode === 'auto' ? 'mdi mdi-robot' : 'mdi mdi-clock-outline'"></i>
            {{ modeText }}
          </span>
          <span v-if="!zone.enabled" class="badge badge-disabled">
            <i class="mdi mdi-cancel"></i>
            Disabled
          </span>
        </div>
      </div>
      <div class="zone-actions">
        <button 
          class="btn-icon btn-edit"
          @click="handleEdit"
          :aria-label="`Edit ${zone.name}`"
          title="Edit zone"
        >
          <i class="mdi mdi-pencil"></i>
        </button>
        <button 
          class="btn-icon btn-delete"
          @click="handleDelete"
          :aria-label="`Delete ${zone.name}`"
          title="Delete zone"
        >
          <i class="mdi mdi-delete"></i>
        </button>
      </div>
    </div>

    <div class="zone-details">
      <div class="detail-row">
        <span class="detail-label">Switch Entity:</span>
        <span class="detail-value">{{ zone.switch_entity }}</span>
      </div>
      <div class="detail-row">
        <span class="detail-label">Next Run:</span>
        <span class="detail-value next-run">
          {{ nextRunText }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  zone: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['edit', 'delete'])

// Computed properties
const modeText = computed(() => {
  return props.zone.mode === 'auto' ? 'Auto' : 'Manual'
})

const nextRunText = computed(() => {
  if (!props.zone.enabled) {
    return 'Zone disabled'
  }
  
  if (!props.zone.next_run) {
    return 'Not scheduled'
  }
  
  // Format the next run time
  const nextRun = new Date(props.zone.next_run)
  const now = new Date()
  
  // Check if it's today
  const isToday = nextRun.toDateString() === now.toDateString()
  
  if (isToday) {
    return `Today at ${nextRun.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    })}`
  }
  
  // Check if it's tomorrow
  const tomorrow = new Date(now)
  tomorrow.setDate(tomorrow.getDate() + 1)
  const isTomorrow = nextRun.toDateString() === tomorrow.toDateString()
  
  if (isTomorrow) {
    return `Tomorrow at ${nextRun.toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    })}`
  }
  
  // Otherwise show full date and time
  return nextRun.toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
})

// Event handlers
const handleEdit = () => {
  emit('edit', props.zone)
}

const handleDelete = () => {
  emit('delete', props.zone)
}
</script>

<style scoped>
.zone-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.zone-info {
  flex: 1;
  min-width: 0;
}

.zone-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.zone-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.zone-name {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary-color);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.zone-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.badge-disabled {
  background-color: var(--text-secondary-color);
  color: white;
}

.zone-actions {
  display: flex;
  gap: 8px;
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 4px;
  transition: background-color 0.2s, color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  color: var(--text-secondary-color);
}

.btn-icon i {
  font-size: 18px;
}

.btn-icon:hover {
  background-color: var(--secondary-background-color);
  color: var(--text-primary-color);
}

.btn-delete:hover {
  background-color: rgba(219, 68, 55, 0.1);
  color: var(--error-color);
}

.zone-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--divider-color);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  gap: 12px;
}

.detail-label {
  color: var(--text-secondary-color);
  font-weight: 500;
  flex-shrink: 0;
}

.detail-value {
  color: var(--text-primary-color);
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.next-run {
  font-weight: 500;
  color: var(--primary-color);
}

/* Responsive design */
@media (max-width: 768px) {
  .zone-header {
    flex-direction: column;
  }

  .zone-actions {
    align-self: flex-end;
  }

  .detail-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .detail-value {
    text-align: left;
  }
}
</style>
