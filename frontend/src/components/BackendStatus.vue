<template>
  <div class="fixed top-4 right-4 z-50">
    <div 
      class="flex items-center px-4 py-2 rounded-lg shadow-lg transition-all duration-300"
      :class="statusClass">
      <font-awesome-icon :icon="statusIcon" class="mr-2" :spin="isChecking" />
      <span class="text-sm font-medium">{{ statusText }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getHealth } from '../api/backend.js'

const backendStatus = ref('checking') // 'checking', 'online', 'offline', 'error'
const lastCheck = ref(null)
const isChecking = ref(false)
let checkInterval = null

const statusClass = computed(() => {
  switch (backendStatus.value) {
    case 'online':
      return 'bg-green-900 text-green-300 border border-green-700'
    case 'offline':
      return 'bg-red-900 text-red-300 border border-red-700'
    case 'error':
      return 'bg-yellow-900 text-yellow-300 border border-yellow-700'
    default:
      return 'bg-gray-900 text-gray-300 border border-gray-700'
  }
})

const statusIcon = computed(() => {
  switch (backendStatus.value) {
    case 'online':
      return 'check-circle'
    case 'offline':
      return 'times-circle'
    case 'error':
      return 'exclamation-triangle'
    default:
      return 'spinner'
  }
})

const statusText = computed(() => {
  switch (backendStatus.value) {
    case 'online':
      return 'Backend Online'
    case 'offline':
      return 'Backend Offline'
    case 'error':
      return 'Backend com Problemas'
    default:
      return 'Verificando Backend...'
  }
})

const checkBackendHealth = async () => {
  isChecking.value = true
  try {
    const result = await getHealth()
    if (result && !result.erro) {
      backendStatus.value = 'online'
    } else {
      backendStatus.value = 'error'
    }
    lastCheck.value = new Date()
  } catch (error) {
    console.warn('Backend health check failed:', error)
    backendStatus.value = 'offline'
    lastCheck.value = new Date()
  } finally {
    isChecking.value = false
  }
}

onMounted(() => {
  // Verificação inicial
  checkBackendHealth()
  
  // Verificação a cada 30 segundos
  checkInterval = setInterval(checkBackendHealth, 30000)
})

onUnmounted(() => {
  if (checkInterval) {
    clearInterval(checkInterval)
  }
})
</script>
