<template>
  <div class="sensor-card">
    <div class="sensor-header">
      <div class="sensor-title">
        <h3>{{ sensor.display_name }}</h3>
        <span class="sensor-type-badge">{{ formatSensorType(sensor.sensor_type) }}</span>
      </div>
      <div class="sensor-actions">
        <button class="icon-btn" @click="$emit('edit', sensor)" title="Edit">✏️</button>
        <button class="icon-btn danger" @click="$emit('delete', sensor)" title="Delete">🗑️</button>
      </div>
    </div>

    <div class="sensor-entity">{{ sensor.sensor_entity }}</div>

    <!-- Current Value -->
    <div class="current-value-section">
      <div v-if="loadingCurrent" class="loading-indicator">Loading current value...</div>
      <div v-else-if="currentError" class="error-message">{{ currentError }}</div>
      <div v-else-if="currentValue" class="current-value">
        <span class="value">{{ currentValue.current_value || 'N/A' }}</span>
        <span v-if="currentValue.unit" class="unit">{{ currentValue.unit }}</span>
      </div>
      <div v-else class="no-data">No current data</div>
    </div>

    <!-- Historical Graph -->
    <div class="graph-section">
      <div class="graph-controls">
        <label for="duration-select">History:</label>
        <select 
          id="duration-select"
          v-model="selectedDuration" 
          @change="loadHistory"
          class="duration-select"
        >
          <option value="1h">Last Hour</option>
          <option value="6h">Last 6 Hours</option>
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
        </select>
      </div>

      <div class="graph-container">
        <div v-if="loadingHistory" class="loading-indicator">Loading history...</div>
        <div v-else-if="historyError" class="error-message">{{ historyError }}</div>
        <canvas v-else ref="chartCanvas" class="chart-canvas"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import api from '../services/api'

const props = defineProps({
  sensor: {
    type: Object,
    required: true
  }
})

defineEmits(['edit', 'delete'])

const currentValue = ref(null)
const loadingCurrent = ref(false)
const currentError = ref(null)

const historyData = ref(null)
const loadingHistory = ref(false)
const historyError = ref(null)
const selectedDuration = ref('24h')

const chartCanvas = ref(null)
let chartInstance = null

onMounted(async () => {
  await loadCurrentValue()
  await loadHistory()
})

watch(() => props.sensor.id, async () => {
  await loadCurrentValue()
  await loadHistory()
})

async function loadCurrentValue() {
  loadingCurrent.value = true
  currentError.value = null
  try {
    const response = await api.getCurrentValue(props.sensor.id)
    currentValue.value = response.data
  } catch (err) {
    currentError.value = 'Failed to load current value'
    console.error('Error loading current value:', err)
  } finally {
    loadingCurrent.value = false
  }
}

async function loadHistory() {
  loadingHistory.value = true
  historyError.value = null
  try {
    const response = await api.getHistory(props.sensor.id, selectedDuration.value)
    historyData.value = response.data
    await nextTick()
    renderChart()
  } catch (err) {
    historyError.value = 'Failed to load history'
    console.error('Error loading history:', err)
  } finally {
    loadingHistory.value = false
  }
}

function renderChart() {
  if (!chartCanvas.value || !historyData.value) return

  const canvas = chartCanvas.value
  const ctx = canvas.getContext('2d')
  
  // Set canvas size
  const container = canvas.parentElement
  canvas.width = container.clientWidth
  canvas.height = 200

  // Clear canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height)

  const dataPoints = historyData.value.data_points || []
  
  if (dataPoints.length === 0) {
    // Draw "No data" message
    ctx.fillStyle = '#999'
    ctx.font = '14px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('No historical data available', canvas.width / 2, canvas.height / 2)
    return
  }

  // Parse and prepare data
  const points = dataPoints
    .map(point => ({
      timestamp: new Date(point.timestamp),
      value: parseFloat(point.value)
    }))
    .filter(point => !isNaN(point.value))
    .sort((a, b) => a.timestamp - b.timestamp)

  if (points.length === 0) {
    ctx.fillStyle = '#999'
    ctx.font = '14px sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('No valid data points', canvas.width / 2, canvas.height / 2)
    return
  }

  // Calculate bounds
  const values = points.map(p => p.value)
  const minValue = Math.min(...values)
  const maxValue = Math.max(...values)
  const valueRange = maxValue - minValue || 1

  const padding = { top: 20, right: 40, bottom: 30, left: 50 }
  const chartWidth = canvas.width - padding.left - padding.right
  const chartHeight = canvas.height - padding.top - padding.bottom

  // Draw axes
  ctx.strokeStyle = '#ddd'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(padding.left, padding.top)
  ctx.lineTo(padding.left, canvas.height - padding.bottom)
  ctx.lineTo(canvas.width - padding.right, canvas.height - padding.bottom)
  ctx.stroke()

  // Draw Y-axis labels
  ctx.fillStyle = '#666'
  ctx.font = '11px sans-serif'
  ctx.textAlign = 'right'
  ctx.textBaseline = 'middle'
  
  const ySteps = 5
  for (let i = 0; i <= ySteps; i++) {
    const value = minValue + (valueRange * i / ySteps)
    const y = canvas.height - padding.bottom - (chartHeight * i / ySteps)
    ctx.fillText(value.toFixed(1), padding.left - 5, y)
  }

  // Draw line graph
  ctx.strokeStyle = '#3498db'
  ctx.lineWidth = 2
  ctx.beginPath()

  points.forEach((point, index) => {
    const x = padding.left + (chartWidth * index / (points.length - 1 || 1))
    const normalizedValue = (point.value - minValue) / valueRange
    const y = canvas.height - padding.bottom - (chartHeight * normalizedValue)

    if (index === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  })

  ctx.stroke()

  // Draw data points
  ctx.fillStyle = '#3498db'
  points.forEach((point, index) => {
    const x = padding.left + (chartWidth * index / (points.length - 1 || 1))
    const normalizedValue = (point.value - minValue) / valueRange
    const y = canvas.height - padding.bottom - (chartHeight * normalizedValue)
    
    ctx.beginPath()
    ctx.arc(x, y, 3, 0, 2 * Math.PI)
    ctx.fill()
  })

  // Draw X-axis time labels
  ctx.fillStyle = '#666'
  ctx.font = '10px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'top'
  
  const labelCount = Math.min(5, points.length)
  for (let i = 0; i < labelCount; i++) {
    const pointIndex = Math.floor(i * (points.length - 1) / (labelCount - 1 || 1))
    const point = points[pointIndex]
    const x = padding.left + (chartWidth * pointIndex / (points.length - 1 || 1))
    const timeLabel = formatTimeLabel(point.timestamp, selectedDuration.value)
    ctx.fillText(timeLabel, x, canvas.height - padding.bottom + 5)
  }
}

function formatTimeLabel(date, duration) {
  if (duration === '1h' || duration === '6h') {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  } else if (duration === '24h') {
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  } else {
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }
}

function formatSensorType(type) {
  const typeMap = {
    'soil_rh': 'Soil Moisture',
    'ec': 'EC',
    'temperature': 'Temperature',
    'humidity': 'Humidity',
    'light': 'Light',
    'ph': 'pH',
    'other': 'Other'
  }
  return typeMap[type] || type
}
</script>

<style scoped>
.sensor-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.sensor-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.sensor-title {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.sensor-title h3 {
  margin: 0;
  font-size: 1.125rem;
  color: #2c3e50;
  font-weight: 600;
}

.sensor-type-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background-color: #e3f2fd;
  color: #1976d2;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
}

.sensor-actions {
  display: flex;
  gap: 0.5rem;
}

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.125rem;
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

.sensor-entity {
  font-family: monospace;
  font-size: 0.75rem;
  color: #999;
  margin-top: -0.5rem;
}

.current-value-section {
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 6px;
  text-align: center;
}

.current-value {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 0.5rem;
}

.current-value .value {
  font-size: 2rem;
  font-weight: 700;
  color: #2c3e50;
}

.current-value .unit {
  font-size: 1.25rem;
  color: #7f8c8d;
  font-weight: 500;
}

.no-data {
  color: #999;
  font-size: 0.875rem;
}

.graph-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.graph-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.graph-controls label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #666;
}

.duration-select {
  padding: 0.375rem 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.875rem;
  cursor: pointer;
  background: white;
}

.duration-select:focus {
  outline: none;
  border-color: #3498db;
}

.graph-container {
  position: relative;
  width: 100%;
  min-height: 200px;
  background: #fafafa;
  border-radius: 6px;
  padding: 0.5rem;
}

.chart-canvas {
  display: block;
  width: 100%;
  height: 200px;
}

.loading-indicator {
  padding: 1rem;
  text-align: center;
  color: #7f8c8d;
  font-size: 0.875rem;
}

.error-message {
  padding: 0.75rem;
  background-color: #fee;
  border: 1px solid #fcc;
  border-radius: 6px;
  color: #c33;
  font-size: 0.875rem;
  text-align: center;
}
</style>
