<template>
  <div class="room-detail">
    <div v-if="loading" class="loading">Loading room details...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="room" class="room-content">
      <!-- Room Header -->
      <div class="room-header">
        <div class="header-left">
          <h1>{{ room.name }}</h1>
          <StatusBadge :status="room.enabled ? 'active' : 'disabled'" />
        </div>
        <div class="header-actions">
          <button class="secondary" @click="goBack">Back</button>
          <button class="primary" @click="editRoom">Edit Room</button>
        </div>
      </div>

      <!-- Room Info -->
      <div class="room-info">
        <div class="info-item">
          <span class="label">Lights On Entity:</span>
          <span class="value">{{ room.lights_on_entity || 'Not set' }}</span>
        </div>
        <div class="info-item">
          <span class="label">Lights Off Entity:</span>
          <span class="value">{{ room.lights_off_entity || 'Not set' }}</span>
        </div>
      </div>

      <!-- Pumps Section -->
      <section class="section">
        <div class="section-header">
          <h2>Pumps</h2>
          <button class="primary" @click="addPump">Add Pump</button>
        </div>
        <div v-if="room.pumps && room.pumps.length > 0" class="pumps-grid">
          <PumpCard 
            v-for="pump in room.pumps" 
            :key="pump.id" 
            :pump="pump"
            @edit="editPump"
            @delete="deletePump"
            @add-zone="addZone"
            @edit-zone="editZone"
            @delete-zone="deleteZone"
          />
        </div>
        <div v-else class="empty-state">
          No pumps configured. Add a pump to get started.
        </div>
      </section>

      <!-- Water Events Section -->
      <section class="section">
        <div class="section-header">
          <h2>Water Events</h2>
          <button class="primary" @click="addEvent">Add Event</button>
        </div>
        <div v-if="room.water_events && room.water_events.length > 0" class="events-grid">
          <EventCard 
            v-for="event in room.water_events" 
            :key="event.id" 
            :event="event"
            @edit="editEvent"
            @delete="deleteEvent"
          />
        </div>
        <div v-else class="empty-state">
          No water events configured. Add an event to schedule irrigation.
        </div>
      </section>

      <!-- Sensors Section -->
      <section class="section">
        <div class="section-header">
          <h2>Environmental Sensors</h2>
          <button class="primary" @click="addSensor">Add Sensor</button>
        </div>
        <div v-if="room.sensors && room.sensors.length > 0" class="sensors-grid">
          <SensorCard 
            v-for="sensor in room.sensors" 
            :key="sensor.id" 
            :sensor="sensor"
            @edit="editSensor"
            @delete="confirmDeleteSensor"
          />
        </div>
        <div v-else class="empty-state">
          No sensors configured. Add sensors to monitor environmental conditions.
        </div>
      </section>
    </div>

    <!-- Room Editor Modal -->
    <RoomEditor 
      :show="showRoomEditor"
      :room="room"
      @close="handleRoomEditorClose"
      @saved="handleRoomSaved"
    />

    <!-- Sensor Editor Modal -->
    <SensorEditor 
      :show="showSensorEditor"
      :sensor="selectedSensor"
      :room-id="room?.id"
      @close="handleSensorEditorClose"
      @saved="handleSensorSaved"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRoomsStore } from '../stores/rooms'
import StatusBadge from '../components/StatusBadge.vue'
import PumpCard from '../components/PumpCard.vue'
import EventCard from '../components/EventCard.vue'
import RoomEditor from '../components/RoomEditor.vue'
import SensorCard from '../components/SensorCard.vue'
import SensorEditor from '../components/SensorEditor.vue'
import api from '../services/api'

const route = useRoute()
const router = useRouter()
const roomsStore = useRoomsStore()

const room = ref(null)
const loading = ref(true)
const error = ref(null)
const showRoomEditor = ref(false)
const showSensorEditor = ref(false)
const selectedSensor = ref(null)

onMounted(async () => {
  await loadRoom()
})

async function loadRoom() {
  loading.value = true
  error.value = null
  try {
    const roomId = parseInt(route.params.id)
    room.value = await roomsStore.getRoom(roomId)
  } catch (err) {
    error.value = 'Failed to load room details'
    console.error(err)
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/')
}

function editRoom() {
  showRoomEditor.value = true
}

function handleRoomEditorClose() {
  showRoomEditor.value = false
}

async function handleRoomSaved() {
  showRoomEditor.value = false
  await loadRoom()
}

function addPump() {
  // TODO: Implement pump editor
  console.log('Add pump to room:', room.value.id)
}

function editPump(pump) {
  // TODO: Implement pump editor
  console.log('Edit pump:', pump.id)
}

function deletePump(pump) {
  // TODO: Implement pump deletion
  console.log('Delete pump:', pump.id)
}

function addZone(pump) {
  // TODO: Implement zone editor
  console.log('Add zone to pump:', pump.id)
}

function editZone(zone) {
  // TODO: Implement zone editor
  console.log('Edit zone:', zone.id)
}

function deleteZone(zone) {
  // TODO: Implement zone deletion
  console.log('Delete zone:', zone.id)
}

function addEvent() {
  // TODO: Implement event editor
  console.log('Add event to room:', room.value.id)
}

function editEvent(event) {
  // TODO: Implement event editor
  console.log('Edit event:', event.id)
}

function deleteEvent(event) {
  // TODO: Implement event deletion
  console.log('Delete event:', event.id)
}

function addSensor() {
  selectedSensor.value = null
  showSensorEditor.value = true
}

function editSensor(sensor) {
  selectedSensor.value = sensor
  showSensorEditor.value = true
}

function handleSensorEditorClose() {
  showSensorEditor.value = false
  selectedSensor.value = null
}

async function handleSensorSaved() {
  showSensorEditor.value = false
  selectedSensor.value = null
  await loadRoom()
}

async function confirmDeleteSensor(sensor) {
  if (confirm(`Are you sure you want to delete sensor "${sensor.display_name}"?`)) {
    try {
      await api.deleteSensor(sensor.id)
      await loadRoom()
    } catch (err) {
      alert('Failed to delete sensor: ' + err.message)
      console.error('Error deleting sensor:', err)
    }
  }
}
</script>

<style scoped>
.room-detail {
  padding: 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
}

.loading,
.error {
  text-align: center;
  padding: 2rem;
  font-size: 1.1rem;
}

.error {
  color: #d32f2f;
}

.room-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #e0e0e0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-left h1 {
  margin: 0;
  font-size: 2rem;
  color: #2c3e50;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.room-info {
  background: #f5f5f5;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 2rem;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-item .label {
  font-weight: 600;
  color: #666;
  font-size: 0.875rem;
}

.info-item .value {
  color: #2c3e50;
  font-size: 1rem;
}

.section {
  margin-bottom: 3rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #2c3e50;
}

.pumps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.events-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.sensors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 1.5rem;
}

.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: #999;
  font-size: 1rem;
  background: #f9f9f9;
  border-radius: 8px;
  border: 2px dashed #e0e0e0;
}
</style>
