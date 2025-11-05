<template>
  <span :class="['status-badge', statusClass]">
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true,
    validator: (value) => ['active', 'idle', 'error', 'disabled', 'running', 'stopped'].includes(value)
  },
  label: {
    type: String,
    default: ''
  }
})

const statusClass = computed(() => {
  return `status-${props.status}`
})

const displayLabel = computed(() => {
  return props.label || props.status.charAt(0).toUpperCase() + props.status.slice(1)
})
</script>

<style scoped>
.status-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;
  text-transform: capitalize;
}

.status-active,
.status-running {
  background-color: #d4edda;
  color: #155724;
}

.status-idle,
.status-stopped {
  background-color: #d1ecf1;
  color: #0c5460;
}

.status-error {
  background-color: #f8d7da;
  color: #721c24;
}

.status-disabled {
  background-color: #e2e3e5;
  color: #6c757d;
}
</style>
