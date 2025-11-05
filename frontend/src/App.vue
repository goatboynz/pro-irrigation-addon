<template>
  <div id="app" class="app-container">
    <!-- Navigation Bar -->
    <nav class="navbar">
      <div class="nav-content">
        <div class="nav-brand">
          <i class="mdi mdi-water nav-icon"></i>
          <span class="nav-title">Pro-Irrigation</span>
        </div>
        <div class="nav-links">
          <router-link to="/" class="nav-link" active-class="active">
            <i class="mdi mdi-view-dashboard"></i>
            <span>Dashboard</span>
          </router-link>
          <router-link to="/settings" class="nav-link" active-class="active">
            <i class="mdi mdi-cog"></i>
            <span>Settings</span>
          </router-link>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="main-content">
      <router-view />
    </main>

    <!-- Toast Notification Container -->
    <div class="toast-container">
      <transition-group name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="['toast', `toast-${toast.type}`, { 'fade-out': !toast.visible }]"
          @click="removeToast(toast.id)"
        >
          <i :class="['toast-icon', getToastIcon(toast.type)]"></i>
          <span class="toast-message">{{ toast.message }}</span>
          <button class="toast-close" @click.stop="removeToast(toast.id)">
            <i class="mdi mdi-close"></i>
          </button>
        </div>
      </transition-group>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useIrrigationStore } from './stores/irrigation'

const irrigationStore = useIrrigationStore()
const toasts = ref([])
let toastIdCounter = 0

// Handle API error notifications
const showToast = (message, type = 'error', duration = 5000) => {
  const id = toastIdCounter++
  const toast = {
    id,
    message,
    type,
    visible: true
  }

  toasts.value.push(toast)

  // Auto-remove after duration
  setTimeout(() => {
    removeToast(id)
  }, duration)
}

const removeToast = (id) => {
  const index = toasts.value.findIndex(t => t.id === id)
  if (index !== -1) {
    toasts.value[index].visible = false
    // Remove from array after animation
    setTimeout(() => {
      toasts.value = toasts.value.filter(t => t.id !== id)
    }, 300)
  }
}

const handleApiError = (event) => {
  const { message, details } = event.detail
  
  // Show main error message
  showToast(message, 'error')

  // Log details for debugging
  if (details && Object.keys(details).length > 0) {
    console.error('Error details:', details)
  }
}

const handleApiSuccess = (event) => {
  showToast(event.detail.message, 'success', 3000)
}

const handleApiInfo = (event) => {
  showToast(event.detail.message, 'info', 4000)
}

const handleApiWarning = (event) => {
  showToast(event.detail.message, 'warning', 4000)
}

const getToastIcon = (type) => {
  switch (type) {
    case 'error':
      return 'mdi mdi-alert-circle'
    case 'success':
      return 'mdi mdi-check-circle'
    case 'warning':
      return 'mdi mdi-alert'
    case 'info':
      return 'mdi mdi-information'
    default:
      return 'mdi mdi-information'
  }
}

onMounted(() => {
  window.addEventListener('api-error', handleApiError)
  window.addEventListener('api-success', handleApiSuccess)
  window.addEventListener('api-info', handleApiInfo)
  window.addEventListener('api-warning', handleApiWarning)
  
  // Start real-time status polling
  irrigationStore.startPolling()
})

onUnmounted(() => {
  window.removeEventListener('api-error', handleApiError)
  window.removeEventListener('api-success', handleApiSuccess)
  window.removeEventListener('api-info', handleApiInfo)
  window.removeEventListener('api-warning', handleApiWarning)
  
  // Stop polling when app unmounts
  irrigationStore.stopPolling()
})
</script>

<style scoped>
.app-container {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Navigation Bar */
.navbar {
  background-color: var(--card-background-color);
  border-bottom: 1px solid var(--divider-color);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary-color);
}

.nav-icon {
  font-size: 28px;
  color: var(--primary-color);
}

.nav-links {
  display: flex;
  gap: 12px;
}

.nav-link {
  text-decoration: none;
  color: var(--text-secondary-color);
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 4px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.nav-link i {
  font-size: 20px;
}

.nav-link:hover {
  color: var(--text-primary-color);
  background-color: var(--secondary-background-color);
}

.nav-link.active {
  color: var(--primary-color);
  background-color: rgba(3, 169, 244, 0.1);
}

/* Responsive navigation */
@media (max-width: 480px) {
  .nav-link span {
    display: none;
  }
  
  .nav-link {
    padding: 8px 12px;
  }
}

/* Main Content */
.main-content {
  flex: 1;
  overflow: auto;
}

/* Toast Notifications */
.toast-container {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}

.toast {
  background-color: var(--error-color);
  color: white;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  min-width: 280px;
  max-width: 400px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  pointer-events: auto;
  transition: all 0.3s ease;
}

.toast:hover {
  transform: translateX(-5px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}

.toast-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.toast-message {
  flex: 1;
  font-size: 14px;
  line-height: 1.4;
}

.toast-close {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 4px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: background-color 0.2s;
  flex-shrink: 0;
}

.toast-close i {
  font-size: 20px;
}

.toast-close:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.toast-success {
  background-color: var(--success-color);
}

.toast-warning {
  background-color: #ff9800;
}

.toast-info {
  background-color: #2196f3;
}

.toast.fade-out {
  opacity: 0;
  transform: translateX(400px);
}

/* Toast transition animations */
.toast-enter-active {
  animation: slideIn 0.3s ease;
}

.toast-leave-active {
  animation: slideOut 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideOut {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(400px);
    opacity: 0;
  }
}

/* Responsive design for mobile */
@media (max-width: 768px) {
  .toast-container {
    right: 10px;
    left: 10px;
    top: 70px;
  }

  .toast {
    min-width: auto;
    max-width: none;
  }
}
</style>
