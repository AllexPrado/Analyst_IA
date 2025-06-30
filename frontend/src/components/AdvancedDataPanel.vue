<template>
  <div class="advanced-data-panel">
    <div v-if="hasData" class="bg-gray-800 rounded-xl shadow-lg overflow-hidden">
      <!-- Tabs for different data types -->
      <div class="flex border-b border-gray-700">
        <div 
          v-for="(tab, index) in availableTabs" 
          :key="index" 
          @click="activeTab = tab.id" 
          class="px-4 py-3 cursor-pointer text-sm font-medium transition-all"
          :class="activeTab === tab.id ? 'text-blue-400 border-b-2 border-blue-400' : 'text-gray-400 hover:text-gray-300'"
        >
          <font-awesome-icon :icon="tab.icon" class="mr-2" />
          {{ tab.label }}
          <span 
            v-if="tab.count" 
            class="ml-2 px-2 py-0.5 text-xs rounded-full"
            :class="tab.count > 0 ? 'bg-blue-900 text-blue-200' : 'bg-gray-700 text-gray-400'"
          >{{ tab.count }}</span>
        </div>
      </div>
      
      <!-- Logs Panel -->
      <div v-if="activeTab === 'logs'" class="p-4">
        <div v-if="logsData && logsData.length > 0" class="space-y-3">
          <div class="flex justify-between items-center mb-2">
            <h3 class="text-lg font-semibold text-white">Logs</h3>
            <span class="text-xs bg-blue-900 text-blue-200 px-2 py-1 rounded-full">{{ logsData.length }} registros</span>
          </div>
          
          <div class="max-h-[400px] overflow-y-auto">
            <div 
              v-for="(log, idx) in logsData" 
              :key="idx" 
              class="log-entry p-3 text-sm border-l-4 mb-2 rounded-r-lg bg-gray-900"
              :class="getLogSeverityClass(log.severity || log.level)"
            >
              <div class="flex justify-between text-xs text-gray-400 mb-1">
                <span>{{ formatTimestamp(log.timestamp) }}</span>
                <span class="px-2 py-0.5 rounded-full" :class="getLogSeverityBadgeClass(log.severity || log.level)">
                  {{ log.severity || log.level || 'INFO' }}
                </span>
              </div>
              <div class="text-white">{{ log.message }}</div>
              
              <div v-if="log.attributes || log.context" class="mt-2 pt-2 border-t border-gray-800">
                <pre class="text-xs text-gray-400 whitespace-pre-wrap">{{ JSON.stringify(log.attributes || log.context, null, 2) }}</pre>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-gray-400 p-4 text-center">
          <font-awesome-icon icon="info-circle" class="mr-2" />
          Nenhum dado de log disponível
        </div>
      </div>
      
      <!-- Traces Panel -->
      <div v-if="activeTab === 'traces'" class="p-4">
        <div v-if="tracesData && tracesData.length > 0" class="space-y-3">
          <div class="flex justify-between items-center mb-2">
            <h3 class="text-lg font-semibold text-white">Traces</h3>
            <span class="text-xs bg-blue-900 text-blue-200 px-2 py-1 rounded-full">{{ tracesData.length }} traces</span>
          </div>
          
          <div class="max-h-[400px] overflow-y-auto">
            <div 
              v-for="(trace, idx) in tracesData" 
              :key="idx" 
              class="trace-entry p-3 text-sm border-l-4 mb-2 rounded-r-lg bg-gray-900 border-indigo-600">
              <div class="flex justify-between text-xs mb-1">
                <span class="text-gray-400">{{ formatTimestamp(trace.timestamp) }}</span>
                <span class="text-gray-400">
                  <span class="font-mono">{{ formatDuration(trace.duration) }}</span>
                </span>
              </div>
              
              <div class="text-white font-medium">{{ trace.name || trace.endpoint }}</div>
              
              <div v-if="trace.spans && trace.spans.length" class="mt-3 pt-2 border-t border-gray-800">
                <div class="text-xs text-gray-400 mb-2">{{ trace.spans.length }} spans</div>
                <div v-for="(span, spanIdx) in trace.spans.slice(0, 3)" :key="spanIdx" class="ml-4 pl-3 border-l border-gray-700 mb-2">
                  <div class="flex justify-between">
                    <span class="text-gray-300">{{ span.name }}</span>
                    <span class="text-xs font-mono text-gray-400">{{ formatDuration(span.duration) }}</span>
                  </div>
                </div>
                <div v-if="trace.spans.length > 3" class="text-xs text-blue-400 cursor-pointer hover:underline mt-1">
                  + {{ trace.spans.length - 3 }} mais spans...
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-gray-400 p-4 text-center">
          <font-awesome-icon icon="info-circle" class="mr-2" />
          Nenhum dado de traces disponível
        </div>
      </div>
      
      <!-- SQL Queries Panel -->
      <div v-if="activeTab === 'queries'" class="p-4">
        <div v-if="queriesData && queriesData.length > 0" class="space-y-3">
          <div class="flex justify-between items-center mb-2">
            <h3 class="text-lg font-semibold text-white">Queries SQL</h3>
            <span class="text-xs bg-blue-900 text-blue-200 px-2 py-1 rounded-full">{{ queriesData.length }} queries</span>
          </div>
          
          <div class="max-h-[400px] overflow-y-auto">
            <div 
              v-for="(query, idx) in queriesData" 
              :key="idx" 
              class="query-entry p-3 text-sm border-l-4 mb-2 rounded-r-lg bg-gray-900 border-green-600">
              <div class="flex justify-between text-xs text-gray-400 mb-1">
                <span>{{ formatTimestamp(query.timestamp) }}</span>
                <span class="font-mono">{{ formatDuration(query.duration) }}</span>
              </div>
              
              <div class="text-gray-200 mb-2">
                <span class="text-green-500 font-medium mr-1">{{ query.database || query.vendor }}</span>
                <span>{{ query.operation || 'QUERY' }}</span>
              </div>
              
              <pre class="text-xs bg-gray-950 p-2 rounded overflow-x-auto whitespace-pre-wrap text-green-400">{{ query.sql || query.query }}</pre>
              
              <div v-if="query.params" class="mt-2 pt-2 border-t border-gray-800">
                <div class="text-xs text-gray-400 mb-1">Parâmetros:</div>
                <pre class="text-xs text-gray-400">{{ JSON.stringify(query.params, null, 2) }}</pre>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-gray-400 p-4 text-center">
          <font-awesome-icon icon="info-circle" class="mr-2" />
          Nenhum dado de query SQL disponível
        </div>
      </div>
      
      <!-- Errors Panel -->
      <div v-if="activeTab === 'errors'" class="p-4">
        <div v-if="errorsData && errorsData.length > 0" class="space-y-3">
          <div class="flex justify-between items-center mb-2">
            <h3 class="text-lg font-semibold text-white">Erros</h3>
            <span class="text-xs bg-red-900 text-red-200 px-2 py-1 rounded-full">{{ errorsData.length }} erros</span>
          </div>
          
          <div class="max-h-[400px] overflow-y-auto">
            <div 
              v-for="(error, idx) in errorsData" 
              :key="idx" 
              class="error-entry p-3 text-sm border-l-4 border-red-600 mb-2 rounded-r-lg bg-gray-900">
              <div class="flex justify-between text-xs text-gray-400 mb-1">
                <span>{{ formatTimestamp(error.timestamp) }}</span>
                <span class="px-2 py-0.5 bg-red-900 text-red-200 rounded-full">ERROR</span>
              </div>
              
              <div class="text-red-400 font-medium mb-1">{{ error.message || error.type }}</div>
              
              <div v-if="error.stack || error.backtrace" class="mt-2 pt-2 border-t border-gray-800">
                <pre class="text-xs bg-gray-950 p-2 rounded overflow-x-auto whitespace-pre-wrap text-gray-400">{{ error.stack || error.backtrace }}</pre>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-gray-400 p-4 text-center">
          <font-awesome-icon icon="info-circle" class="mr-2" />
          Nenhum erro registrado
        </div>
      </div>
    </div>
    
    <div v-else class="bg-gray-800 rounded-xl shadow-lg p-6">
      <div class="flex flex-col items-center justify-center">
        <font-awesome-icon icon="info-circle" class="text-3xl text-gray-600 mb-3" />
        <p class="text-gray-400 text-center">{{ noDataMessage }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// Props
const props = defineProps({
  entityData: {
    type: Object,
    default: () => ({})
  },
  noDataMessage: {
    type: String,
    default: 'Dados avançados não disponíveis para esta entidade'
  }
})

// State
const activeTab = ref('logs') // Default active tab

// Computed properties
const hasData = computed(() => 
  logsData.value.length > 0 || 
  tracesData.value.length > 0 || 
  queriesData.value.length > 0 ||
  errorsData.value.length > 0
)

const logsData = computed(() => props.entityData?.logs || [])
const tracesData = computed(() => props.entityData?.traces || [])
const queriesData = computed(() => props.entityData?.queries || [])
const errorsData = computed(() => props.entityData?.errors || [])

const availableTabs = computed(() => [
  { id: 'logs', label: 'Logs', icon: 'file-alt', count: logsData.value.length },
  { id: 'traces', label: 'Traces', icon: 'project-diagram', count: tracesData.value.length },
  { id: 'queries', label: 'Queries SQL', icon: 'database', count: queriesData.value.length },
  { id: 'errors', label: 'Erros', icon: 'exclamation-triangle', count: errorsData.value.length }
])

// Methods
const formatTimestamp = (timestamp) => {
  if (!timestamp) return 'N/A'
  
  // Check if timestamp is a number (Unix timestamp)
  if (typeof timestamp === 'number') {
    // Convert to date object
    const date = new Date(timestamp)
    return date.toLocaleString()
  }
  
  // Check if timestamp is ISO format
  try {
    const date = new Date(timestamp)
    return date.toLocaleString()
  } catch (e) {
    return timestamp // Return as is if not parseable
  }
}

const formatDuration = (duration) => {
  if (!duration) return 'N/A'
  
  // Convert to number if string
  const durationNum = parseFloat(duration)
  
  // Check if the value is in milliseconds (typical for traces)
  if (durationNum < 1000) {
    return `${durationNum.toFixed(2)} ms`
  }
  
  // Convert to seconds
  return `${(durationNum / 1000).toFixed(2)} s`
}

const getLogSeverityClass = (severity) => {
  severity = (severity || '').toUpperCase()
  
  switch (severity) {
    case 'ERROR':
    case 'CRITICAL':
    case 'FATAL':
      return 'border-red-600'
    case 'WARNING':
    case 'WARN':
      return 'border-yellow-600'
    case 'INFO':
      return 'border-blue-600'
    case 'DEBUG':
      return 'border-green-600'
    default:
      return 'border-gray-600'
  }
}

const getLogSeverityBadgeClass = (severity) => {
  severity = (severity || '').toUpperCase()
  
  switch (severity) {
    case 'ERROR':
    case 'CRITICAL':
    case 'FATAL':
      return 'bg-red-900 text-red-200'
    case 'WARNING':
    case 'WARN':
      return 'bg-yellow-900 text-yellow-200'
    case 'INFO':
      return 'bg-blue-900 text-blue-200'
    case 'DEBUG':
      return 'bg-green-900 text-green-200'
    default:
      return 'bg-gray-700 text-gray-300'
  }
}
</script>

<style scoped>
/* Custom scrollbar for the panels */
.max-h-\[400px\] {
  scrollbar-width: thin;
  scrollbar-color: #4a5568 #1a202c;
}

.max-h-\[400px\]::-webkit-scrollbar {
  width: 8px;
}

.max-h-\[400px\]::-webkit-scrollbar-track {
  background: #1a202c;
}

.max-h-\[400px\]::-webkit-scrollbar-thumb {
  background-color: #4a5568;
  border-radius: 4px;
}
</style>
