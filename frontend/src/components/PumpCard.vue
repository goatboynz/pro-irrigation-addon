<template>
  <div class="pump-card card card-interactive">
    <div class="pump-header">
      <div class="pump-title-row">
        <i :class="['pump-icon', statusIconClass]" :title="statusDescription"></i>
        <h3 class="pump-name">{{ pump.name }}</h3>
      </div>
      <span :class="['badge', `badge-${pump.status}`]">
        <i :class="statusBadgeIcon"></i>
        {{ statusText }}
      </span>
    </div>

    <div class="pump-info">
      <div class="info-row">
        <span class="info-label">Status:</span>
        <span class="info-value">{{ statusDescription }}</span>
      </div>

      <div v-if="pump.active_zone" class="info-row">
        <span class="info-label">Active Zone:</span>
        <span class="info-value active-zone">{{ pump.active_zone }}</span>
      </div>

      <div v-if="pump.queue_length > 0" class="info-row">
        <span class="info-label">Queue:</span>
        <span class="info-value queue-indicator">
          {{ pump.queue_length }} {{ pump.queue_length === 1 ? 'job' : 'jobs' }} waiting
        </span>
      </div>
    </div>

    <div class="pump-actions">
      <button 
        class="btn btn-primary manage-btn"
        @click="handleManage"
        :aria-label="`Manage zones for ${pump.name}`"
      >
        <i class="mdi mdi-cog"></i>
        <span>Manage Zones</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  pump: {
    type: Object,
    required: true
  }
})

const router = useRouter()

// Computed properties for status display
const statusText = computed(() => {
  const status = props.pump.status || 'idle'
  return status.charAt(0).toUpperCase() + status.slice(1)
})

const statusDescription = computed(() => {
  const status = props.pump.status || 'idle'
  switch (status) {
    case 'idle':
      return 'No zones running'
    case 'running':
      return 'Zone in progress'
    case 'queued':
      return 'Jobs queued'
    default:
      return 'Unknown'
  }
})

const statusIconClass = computed(() => {
  const status = props.pump.status || 'idle'
  switch (status) {
    case 'idle':
      return 'mdi mdi-water-pump-off'
    case 'running':
      return 'mdi mdi-water-pump'
    case 'queued':
      return 'mdi mdi-clock-outline'
    default:
      return 'mdi mdi-water-pump'
  }
})

const statusBadgeIcon = computed(() => {
  const status = props.pump.status || 'idle'
  switch (status) {
    case 'idle':
      return 'mdi mdi-check-circle'
    case 'running':
      return 'mdi mdi-play-circle'
    case 'queued':
      return 'mdi mdi-clock-outline'
    default:
      return 'mdi mdi-help-circle'
  }
})

// Navigate to zone manager
const handleManage = () => {
  router.push({
    name: 'zone-manager',
    params: { pumpId: props.pump.id }
  })
}
</script>

<style scoped>
.pump-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.pump-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.pump-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.pump-icon {
  font-size: 24px;
  color: var(--state-icon-color);
  flex-shrink: 0;
}

.pump-icon.mdi-water-pump {
  color: var(--warning-color);
  animation: pulse 2s ease-in-out infinite;
}

.pump-icon.mdi-water-pump-off {
  color: var(--success-color);
}

.pump-icon.mdi-clock-outline {
  color: var(--accent-color);
}

.pump-name {
  font-size: 18px;
  font-weight: 500;
  color: var(--text-primary-color);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pump-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.info-label {
  color: var(--text-secondary-color);
  font-weight: 500;
}

.info-value {
  color: var(--text-primary-color);
}

.active-zone {
  font-weight: 500;
  color: var(--primary-color);
}

.queue-indicator {
  color: var(--accent-color);
  font-weight: 500;
}

.pump-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 8px;
}

.manage-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.manage-btn i {
  font-size: 18px;
}

/* Responsive design */
@media (min-width: 768px) {
  .manage-btn {
    width: auto;
  }
}
</style>
