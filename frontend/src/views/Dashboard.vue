<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>Rooms</h1>
      <button @click="showRoomEditor = true" class="btn-primary">
        <span class="icon">+</span>
        Create Room
      </button>
    </div>

    <div v-if="loading" class="loading">
      Loading rooms...
    </div>

    <div v-else-if="error" class="error-message">
      <p>Error loading rooms: {{ error }}</p>
      <button @click="loadRooms" class="btn-secondary">Retry</button>
    </div>

    <div v-else-if="rooms.length === 0" class="empty-state">
      <p>No rooms configured yet.</p>
      <p class="empty-hint">Create your first room to get started with irrigation management.</p>
    </div>

    <div v-else class="rooms-grid">
      <div 
        v-for="room in rooms" 
        :key="room.id" 
        class="room-card"
        @click="navigateToRoom(room.id)"
      >
        <div class="room-header">
          <h3>{{ room.name }}</h3>
          <StatusBadge :status="getRoomStatus(room)" :label="getRoomStatusLabel(room)" />
        </div>
        
        <div class="room-info">
          <div class="info-item">
            <span class="label">Pumps:</span>
            <span class="value">{{ room.pump_count || 0 }}</span>
          </div>
          <div class="info-item">
            <span class="label">Zones:</span>
            <span class="value">{{ room.zone_count || 0 }}</span>
          </div>
          <div class="info-item">
            <span class="label">Events:</span>
            <span class="value">{{ room.event_count || 0 }}</span>
          </div>
        </div>

        <div v-if="room.active_events && room.active_events.length > 0" class="active-events">
          <div class="active-label">Active:</div>
          <div class="event-list">
            <span v-for="event in room.active_events" :key="event" class="event-tag">
              {{ event }}
            </span>
          </div>
        </div>

        <div class="room-footer">
          <span v-if="room.enabled" class="status-text enabled">Enabled</span>
          <span v-else class="status-text disabled">Disabled</span>
        </div>
      </div>
    </div>

    <!-- Room Editor Modal -->
    <RoomEditor 
      :show="showRoomEditor"
      :room="null"
      @close="handleRoomEditorClose"
      @saved="handleRoomSaved"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useRoomsStore } from '../stores/rooms'
import StatusBadge from '../components/StatusBadge.vue'
import RoomEditor from '../components/RoomEditor.vue'

const router = useRouter()
const roomsStore = useRoomsStore()

const rooms = ref([])
const loading = ref(false)
const error = ref(null)
const showRoomEditor = ref(false)
let refreshInterval = null

async function loadRooms() {
  loading.value = true
  error.value = null
  try {
    await roomsStore.fetchRooms()
    rooms.value = roomsStore.rooms
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function refreshRooms() {
  // Silent refresh without showing loading state
  try {
    await roomsStore.fetchRooms()
    rooms.value = roomsStore.rooms
  } catch (err) {
    console.error('Failed to refresh rooms:', err)
    // Don't update error state during background refresh
  }
}

function startAutoRefresh() {
  // Poll room status every 5 seconds
  refreshInterval = setInterval(() => {
    refreshRooms()
  }, 5000)
}

function stopAutoRefresh() {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

function getRoomStatus(room) {
  if (!room.enabled) return 'disabled'
  if (room.active_events && room.active_events.length > 0) return 'running'
  return 'idle'
}

function getRoomStatusLabel(room) {
  if (!room.enabled) return 'Disabled'
  if (room.active_events && room.active_events.length > 0) return 'Active'
  return 'Idle'
}

function navigateToRoom(roomId) {
  router.push(`/room/${roomId}`)
}

function handleRoomEditorClose() {
  showRoomEditor.value = false
}

async function handleRoomSaved() {
  showRoomEditor.value = false
  await loadRooms()
}

onMounted(() => {
  loadRooms()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style scoped>
.dashboard {
  padding: 1rem;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.dashboard-header h1 {
  margin: 0;
  font-size: 2rem;
  color: #2c3e50;
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-primary:hover {
  background-color: #2980b9;
}

.btn-primary:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background-color: #ecf0f1;
  color: #2c3e50;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-secondary:hover {
  background-color: #bdc3c7;
}

.icon {
  font-size: 1.25rem;
  font-weight: bold;
}

.loading,
.error-message,
.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: #7f8c8d;
}

.error-message {
  color: #e74c3c;
}

.error-message button {
  margin-top: 1rem;
}

.empty-hint {
  font-size: 0.9rem;
  margin-top: 0.5rem;
}

.rooms-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.room-card {
  background: white;
  border: 1px solid #e1e8ed;
  border-radius: 8px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.room-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.room-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.room-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #2c3e50;
}

.room-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #ecf0f1;
}

.info-item {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
}

.info-item .label {
  color: #7f8c8d;
}

.info-item .value {
  font-weight: 600;
  color: #2c3e50;
}

.active-events {
  margin-bottom: 1rem;
  padding: 0.75rem;
  background-color: #e8f5e9;
  border-radius: 6px;
}

.active-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #27ae60;
  margin-bottom: 0.5rem;
}

.event-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.event-tag {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background-color: #27ae60;
  color: white;
  border-radius: 4px;
  font-size: 0.8rem;
}

.room-footer {
  display: flex;
  justify-content: flex-end;
}

.status-text {
  font-size: 0.85rem;
  font-weight: 500;
}

.status-text.enabled {
  color: #27ae60;
}

.status-text.disabled {
  color: #95a5a6;
}
</style>
