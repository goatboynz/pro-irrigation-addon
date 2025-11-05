<template>
  <div :class="['error-display', typeClass]">
    <div class="error-icon">
      {{ icon }}
    </div>
    <div class="error-content">
      <h3 class="error-title">{{ title }}</h3>
      <p class="error-message">{{ message }}</p>
      <button v-if="showRetry" @click="$emit('retry')" class="retry-button">
        Try Again
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'error',
    validator: (value) => ['error', 'warning', 'info'].includes(value)
  },
  title: {
    type: String,
    default: 'Error'
  },
  message: {
    type: String,
    required: true
  },
  showRetry: {
    type: Boolean,
    default: false
  }
})

defineEmits(['retry'])

const typeClass = computed(() => `type-${props.type}`)

const icon = computed(() => {
  switch (props.type) {
    case 'error':
      return '❌'
    case 'warning':
      return '⚠️'
    case 'info':
      return 'ℹ️'
    default:
      return '❌'
  }
})
</script>

<style scoped>
.error-display {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  border-radius: 8px;
  background-color: var(--card-background-color);
  border: 2px solid;
}

.type-error {
  border-color: var(--error-color);
  background-color: rgba(244, 67, 54, 0.05);
}

.type-warning {
  border-color: #ff9800;
  background-color: rgba(255, 152, 0, 0.05);
}

.type-info {
  border-color: #2196f3;
  background-color: rgba(33, 150, 243, 0.05);
}

.error-icon {
  font-size: 32px;
  flex-shrink: 0;
}

.error-content {
  flex: 1;
}

.error-title {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary-color);
}

.error-message {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: var(--text-secondary-color);
  line-height: 1.5;
}

.retry-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
}

.retry-button:hover {
  background-color: #0288d1;
}

.retry-button:active {
  background-color: #01579b;
}
</style>
