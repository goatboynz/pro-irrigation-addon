<template>
  <div class="entity-selector">
    <label v-if="label" class="form-label">
      {{ label }}
      <span v-if="required" class="required-indicator">*</span>
    </label>
    
    <div class="selector-wrapper">
      <select 
        v-model="selectedValue"
        class="form-select"
        :disabled="loading || disabled"
        @change="handleChange"
      >
        <option value="">{{ placeholder }}</option>
        <option 
          v-for="entity in filteredEntities" 
          :key="entity.entity_id"
          :value="entity.entity_id"
        >
          {{ entity.friendly_name || entity.entity_id }}
        </option>
      </select>
      
      <div v-if="loading" class="loading-indicator">
        <div class="mini-spinner"></div>
      </div>
    </div>
    
    <p v-if="hint" class="hint-text">{{ hint }}</p>
    <p v-if="error" class="error-text">{{ error }}</p>
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
  entityType: {
    type: String,
    required: true,
    validator: (value) => ['switch', 'input_datetime', 'input_number', 'input_boolean'].includes(value)
  },
  label: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Select an entity...'
  },
  hint: {
    type: String,
    default: ''
  },
  required: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

// Local state
const entities = ref([])
const loading = ref(false)
const selectedValue = ref(props.modelValue)

// Computed
const filteredEntities = computed(() => {
  return entities.value
})

// Watch for external changes to modelValue
watch(() => props.modelValue, (newValue) => {
  selectedValue.value = newValue
})

// Load entities on mount
onMounted(async () => {
  await loadEntities()
})

// Methods
const loadEntities = async () => {
  try {
    loading.value = true
    entities.value = await api.getAvailableEntities(props.entityType)
  } catch (error) {
    console.error('Failed to load entities:', error)
  } finally {
    loading.value = false
  }
}

const handleChange = () => {
  emit('update:modelValue', selectedValue.value)
  emit('change', selectedValue.value)
}
</script>

<style scoped>
.entity-selector {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: var(--text-primary-color);
  font-size: 14px;
}

.required-indicator {
  color: var(--error-color);
  margin-left: 2px;
}

.selector-wrapper {
  position: relative;
}

.form-select {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--divider-color);
  border-radius: 4px;
  font-size: 14px;
  font-family: inherit;
  background-color: var(--card-background-color);
  color: var(--text-primary-color);
  cursor: pointer;
  transition: border-color 0.2s;
}

.form-select:focus {
  outline: none;
  border-color: var(--primary-color);
}

.form-select:disabled {
  background-color: var(--secondary-background-color);
  cursor: not-allowed;
  opacity: 0.6;
}

.loading-indicator {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
}

.mini-spinner {
  border: 2px solid var(--divider-color);
  border-top: 2px solid var(--primary-color);
  border-radius: 50%;
  width: 16px;
  height: 16px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.hint-text {
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-secondary-color);
}

.error-text {
  margin-top: 4px;
  font-size: 12px;
  color: var(--error-color);
  font-weight: 500;
}
</style>
