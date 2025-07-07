<template>
  <div class="card bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl p-6 shadow-lg flex flex-col items-center border-l-8" :class="borderClass">
    <div class="w-14 h-14 rounded-full flex items-center justify-center mb-3" :class="iconBg">
      <font-awesome-icon :icon="icon" :class="iconClass" class="text-3xl" />
    </div>
    <span class="text-xl font-bold mb-1">{{ title }}</span>
    <span class="text-3xl font-extrabold" :class="valueClass">{{ mainValue }}</span>
    <span class="mt-2 text-gray-300 text-center text-sm">{{ description }}</span>
    <div v-if="tooltip" class="mt-2 text-xs text-blue-300 cursor-help" :title="tooltip">
      <font-awesome-icon icon="info-circle" /> {{ tooltip }}
    </div>
    <div v-if="erro" class="mt-3 text-yellow-300 text-sm">{{ erro }}</div>
    <div v-if="loading" class="mt-3 text-blue-300 text-sm">Carregando...</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getLogs, getAlertas, getDashboards, getIncidentes } from '../../api/backend.js'

const props = defineProps({
  type: { type: String, required: true } // 'logs', 'alertas', 'dashboards', 'incidentes'
})

const titleMap = {
  logs: 'Logs Recentes',
  alertas: 'Alertas Ativos',
  dashboards: 'Dashboards',
  incidentes: 'Incidentes Críticos'
}
const iconMap = {
  logs: ['fas', 'file-alt'],
  alertas: ['fas', 'exclamation-triangle'],
  dashboards: ['fas', 'chart-line'],
  incidentes: ['fas', 'bolt']
}
const colorMap = {
  logs: 'border-blue-500',
  alertas: 'border-yellow-500',
  dashboards: 'border-green-500',
  incidentes: 'border-red-500'
}
const iconBgMap = {
  logs: 'bg-blue-500/20 text-blue-400',
  alertas: 'bg-yellow-500/20 text-yellow-300',
  dashboards: 'bg-green-500/20 text-green-400',
  incidentes: 'bg-red-500/20 text-red-400'
}
const valueClassMap = {
  logs: 'text-blue-400',
  alertas: 'text-yellow-300',
  dashboards: 'text-green-400',
  incidentes: 'text-red-400'
}

const title = titleMap[props.type]
const icon = iconMap[props.type]
const borderClass = colorMap[props.type]
const iconBg = iconBgMap[props.type]
const valueClass = valueClassMap[props.type]

const mainValue = ref('-')
const description = ref('')
const tooltip = ref('')
const erro = ref('')
const loading = ref(true)

const iconClass = valueClass

const fetchData = async () => {
  loading.value = true
  erro.value = ''
  try {
    let data
    if (props.type === 'logs') {
      data = await getLogs()
      if (data && !data.erro) {
        mainValue.value = Array.isArray(data) ? data.length : (data?.total || 0)
        description.value = 'Total de logs coletados nas últimas 24h.'
        tooltip.value = 'Inclui logs de aplicações, infraestrutura e erros.'
      } else {
        throw new Error(data?.mensagem || 'Erro ao carregar logs')
      }
    } else if (props.type === 'alertas') {
      data = await getAlertas()
      if (data && !data.erro) {
        mainValue.value = Array.isArray(data) ? data.length : (data?.total || 0)
        description.value = 'Alertas ativos detectados pelo monitoramento.'
        tooltip.value = 'Inclui alertas críticos, warnings e recomendações.'
      } else {
        throw new Error(data?.mensagem || 'Erro ao carregar alertas')
      }
    } else if (props.type === 'dashboards') {
      data = await getDashboards()
      if (data && !data.erro) {
        mainValue.value = Array.isArray(data) ? data.length : (data?.total || 0)
        description.value = 'Dashboards disponíveis para análise.'
        tooltip.value = 'Dashboards integrados do New Relic e outros provedores.'
      } else {
        throw new Error(data?.mensagem || 'Erro ao carregar dashboards')
      }
    } else if (props.type === 'incidentes') {
      data = await getIncidentes()
      if (data && !data.erro) {
        mainValue.value = Array.isArray(data) ? data.length : (data?.total || 0)
        description.value = 'Incidentes críticos registrados.'
        tooltip.value = 'Incidentes abertos, fechados e em investigação.'
      } else {
        throw new Error(data?.mensagem || 'Erro ao carregar incidentes')
      }
    }
  } catch (e) {
    console.error(`Erro ao carregar dados de ${props.type}:`, e)
    erro.value = e.message || 'Erro ao carregar dados.'
    mainValue.value = '!'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
  setInterval(fetchData, 60000) // Atualiza a cada 1 min
})
</script>

<style scoped>
.card {
  min-width: 220px;
  min-height: 180px;
}
</style>
