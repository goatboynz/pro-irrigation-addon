<template>
  <div class="entity-selector">
    <label v-if="label" :for="inputId">{{ label }}</label>
    <div class="selector-wrapper">
      <input
        :id="inputId"
        v-model="searchQuery"
        type="text"
        :placeholder="placeholder"
        @focus="showDropdown = true"
        @blur="handleBlur"
        @input="filterEntities"
        class="selector-input"
      />
      <div v-if="showDropdown && filteredEntities.length > 0" class="dropdown">
        <div
          v-for="entity in filteredEntities"
          :key="entity.entity_id"
          class="dropdown-item"
          @mousedown.prevent="selectEntity(entity)"
        >
          <div class="entity-id">{{ entity.entity_id }}</div>
          <div class="entity-name">{{ entity.friendly_name || entity.entity_id }}</div>
        </div>
      </div>
      <div v-if="loading" class="loading-indicator">Loading entities...</div>
      <div v-if="error" class="error-message">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '../services/api'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  label: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Search for entity...'
  },
  filter: {
    type: Function,
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

const inputId = `entity-selector-${Math.random().toString(36).substr(2, 9)}`
const searchQuery = ref(props.modelValue)
const showDropdown = ref(false)
const entities = ref([])
const loading = ref(false)
const error = ref(null)

const filteredEntities = computed(() => {
  if (!searchQuery.value) {
    return props.filter ? entities.value.filter(props.filter) : entities.value
  }
  
  const query = searchQuery.value.toLowerCase()
  let filtered = entities.value.filter(entity => {
    const entityId = entity.entity_id.toLowerCase()
    const friendlyName = (entity.friendly_name || '').toLowerCase()
    return entityId.includes(query) || friendlyName.includes(query)
  })
  
  if (props.filter) {
    filtered = filtered.filter(props.filter)
  }
  
  return filtered.slice(0, 50) // Limit to 50 results
})

async function loadEntities() {
  loading.value = true
  error.value = null
  try {
    const response = await api.getHAEntities()
    entities.value = response.data
  } catch (err) {
    error.value = 'Failed to load entities'
    console.error('Failed to load entities:', err)
  } finally {
    loading.value = false
  }
}

function selectEntity(entity) {
  searchQuery.value = entity.entity_id
  emit('update:modelValue', entity.entity_id)
  showDropdown.value = false
}

function handleBlur() {
  setTimeout(() => {
    showDropdown.value = false
  }, 200)
}

function filterEntities() {
  showDropdown.value = true
}

watch(() => props.modelValue, (newValue) => {
  searchQuery.value = newValue
})

onMounted(() => {
  loadEntities()
})
</script>

<style scoped>
.entity-selector {
  margin-bottom: 1rem;
}

.entity-selector label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.selector-wrapper {
  position: relative;
}

.selector-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
}

.selector-input:focus {
  outline: none;
  border-color: #3498db;
}

.dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  max-height: 300px;
  overflow-y: auto;
  background: white;
  border: 1px solid #ddd;
  border-top: none;
  border-radius: 0 0 4px 4px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  z-index: 1000;
}

.dropdown-item {
  padding: 0.75rem;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
}

.dropdown-item:hover {
  background-color: #f8f9fa;
}

.dropdown-item:last-child {
  border-bottom: none;
}

.entity-id {
  font-family: monospace;
  font-size: 0.875rem;
  color: #2c3e50;
}

.entity-name {
  font-size: 0.75rem;
  color: #7f8c8d;
  margin-top: 0.25rem;
}

.loading-indicator {
  padding: 0.5rem;
  color: #7f8c8d;
  font-size: 0.875rem;
}

.error-message {
  padding: 0.5rem;
  color: #e74c3c;
  font-size: 0.875rem;
}
</style>
