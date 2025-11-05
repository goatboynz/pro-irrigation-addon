<template>
  <div :class="['loading-spinner', sizeClass]">
    <div class="spinner"></div>
    <p v-if="message" class="loading-message">{{ message }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  size: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium', 'large'].includes(value)
  },
  message: {
    type: String,
    default: ''
  }
})

const sizeClass = computed(() => `size-${props.size}`)
</script>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.spinner {
  border: 3px solid rgba(3, 169, 244, 0.2);
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.size-small .spinner {
  width: 24px;
  height: 24px;
  border-width: 2px;
}

.size-medium .spinner {
  width: 40px;
  height: 40px;
  border-width: 3px;
}

.size-large .spinner {
  width: 60px;
  height: 60px;
  border-width: 4px;
}

.loading-message {
  color: var(--text-secondary-color);
  font-size: 14px;
  margin: 0;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
