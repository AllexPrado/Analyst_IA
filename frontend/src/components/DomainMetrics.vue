<template>
  <div>
    <div v-if="!selectedDomain" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div v-for="domain in availableDomains" :key="domain" 
           class="rounded-xl shadow-lg p-6 bg-gray-800 text-white cursor-pointer hover:bg-gray-700 transition-all"
           @click="selectDomain(domain)">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-xl font-bold">{{ getDomainLabel(domain) }}</h3>
          <span class="text-sm bg-blue-800 text-blue-200 rounded-full px-3 py-1">
            {{ domainEntityCount(domain) }} entidades
          </span>
        </div>
        <p class="text-gray-300 mb-4">{{ getDomainDescription(domain) }}</p>
        <div class="text-blue-300 flex items-center mt-4">
          <span>Ver métricas detalhadas</span>
          <font-awesome-icon icon="chevron-right" class="ml-2"/>
        </div>
      </div>
    </div>

    <div v-else>
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-2xl font-bold text-white flex items-center">
          <span @click="selectedDomain = null" class="cursor-pointer mr-3">
            <font-awesome-icon icon="chevron-left" />
          </span>
          Métricas de {{ getDomainLabel(selectedDomain) }}
        </h2>
        <span class="text-sm bg-blue-800 text-blue-200 rounded-full px-3 py-1">
          {{ domainEntityCount(selectedDomain) }} entidades
        </span>
      </div>

      <!-- Alertas e erros do domínio -->
      <div v-if="domainAlerts(selectedDomain) > 0 || domainErrors(selectedDomain) > 0"
           class="mb-6 p-4 rounded-lg" 
           :class="domainErrors(selectedDomain) > 0 ? 'bg-red-900' : 'bg-yellow-900'">
        <div class="flex items-center">
          <font-awesome-icon :icon="domainErrors(selectedDomain) > 0 ? 'exclamation-circle' : 'exclamation-triangle'" 
                           class="text-2xl mr-3"
                           :class="domainErrors(selectedDomain) > 0 ? 'text-red-400' : 'text-yellow-300'"/>
          <div>
            <h3 class="font-bold" :class="domainErrors(selectedDomain) > 0 ? 'text-red-300' : 'text-yellow-200'">
              {{ domainErrors(selectedDomain) > 0 ? 'Erros críticos detectados' : 'Alertas ativos' }}
            </h3>
            <p class="text-gray-300">
              {{ domainAlertMessage(selectedDomain) }}
            </p>
          </div>
        </div>
      </div>

      <!-- Entidades do domínio com suas métricas -->
      <div class="grid grid-cols-1 gap-6">
        <template v-if="domainEntities(selectedDomain).length > 0">
          <div v-for="entity in domainEntities(selectedDomain)" :key="entity.guid" 
               class="rounded-lg shadow-lg p-5 bg-gray-800">
            <div class="flex justify-between items-start mb-3">
              <h4 class="text-lg font-bold text-white">{{ entity.name }}</h4>
              <span class="text-xs rounded-full px-2 py-1"
                    :class="entityHasErrors(entity) ? 'bg-red-900 text-red-200' : 
                           entityHasAlerts(entity) ? 'bg-yellow-900 text-yellow-200' : 
                           'bg-green-900 text-green-200'">
                {{ entityHasErrors(entity) ? 'Crítico' : entityHasAlerts(entity) ? 'Alerta' : 'OK' }}
              </span>
            </div>
            
            <!-- Métricas específicas por domínio -->
            <div class="text-sm">
              <template v-if="selectedDomain === 'APM'">
                <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">Tempo de Resposta</div>
                    <div class="font-bold text-white">{{ formatMetricValue(getEntityMetric(entity, 'response_time_max')) }} ms</div>
                  </div>
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">Apdex</div>
                    <div class="font-bold text-white">{{ formatMetricValue(getEntityMetric(entity, 'apdex')) }}</div>
                  </div>
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">Throughput (rpm)</div>
                    <div class="font-bold text-white">{{ formatMetricValue(getEntityMetric(entity, 'throughput')) }}</div>
                  </div>
                </div>
                <div v-if="entityHasErrors(entity)" class="mt-4">
                  <h5 class="font-medium text-red-300 mb-2">Erros recentes:</h5>
                  <div class="bg-gray-900 p-3 rounded text-xs overflow-auto max-h-40">
                    {{ getEntityErrors(entity) }}
                  </div>
                </div>
                
                <!-- Painel de dados avançados -->
                <div v-if="hasAdvancedData(entity)" class="mt-4 pt-4 border-t border-gray-700">
                  <div class="flex items-center mb-3">
                    <h5 class="font-medium text-blue-300">Dados avançados</h5>
                    <span v-if="getAdvancedDataCount(entity) > 0" class="ml-2 text-xs bg-blue-900 text-blue-200 px-2 py-1 rounded-full">
                      {{ getAdvancedDataCount(entity) }} registros
                    </span>
                  </div>
                  <advanced-data-panel :entity-data="entity" />
                </div>
              </template>

              <template v-else-if="selectedDomain === 'BROWSER'">
                <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">LCP</div>
                    <div class="font-bold text-white">{{ formatMetricValue(getEntityMetric(entity, 'largest_contentful_paint')) }} ms</div>
                  </div>
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">CLS</div>
                    <div class="font-bold text-white">{{ formatMetricValue(getEntityMetric(entity, 'cls')) }}</div>
                  </div>
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">FID</div>
                    <div class="font-bold text-white">{{ formatMetricValue(getEntityMetric(entity, 'fid')) }} ms</div>
                  </div>
                </div>
                <div v-if="entityHasJsErrors(entity)" class="mt-4">
                  <h5 class="font-medium text-yellow-300 mb-2">Erros JavaScript:</h5>
                  <div class="bg-gray-900 p-3 rounded text-xs overflow-auto max-h-40">
                    {{ getEntityJsErrors(entity) }}
                  </div>
                </div>
                
                <!-- Painel de dados avançados para Browser -->
                <div v-if="hasAdvancedData(entity)" class="mt-4 pt-4 border-t border-gray-700">
                  <div class="flex items-center mb-3">
                    <h5 class="font-medium text-blue-300">Dados avançados</h5>
                    <span v-if="getAdvancedDataCount(entity) > 0" class="ml-2 text-xs bg-blue-900 text-blue-200 px-2 py-1 rounded-full">
                      {{ getAdvancedDataCount(entity) }} registros
                    </span>
                  </div>
                  <advanced-data-panel :entity-data="entity" />
                </div>
              </template>

              <template v-else-if="selectedDomain === 'INFRA'">
                <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">CPU</div>
                    <div class="font-bold text-white">{{ formatMetricValue(getEntityMetric(entity, 'cpu')) }}%</div>
                  </div>
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">Memória</div>
                    <div class="font-bold text-white">{{ formatMemoryValue(getEntityMetric(entity, 'memoria')) }}</div>
                  </div>
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">Uptime</div>
                    <div class="font-bold text-white">{{ formatUptimeValue(getEntityMetric(entity, 'uptime')) }}</div>
                  </div>
                </div>
                
                <!-- Painel de dados avançados para Infra -->
                <div v-if="hasAdvancedData(entity)" class="mt-4 pt-4 border-t border-gray-700">
                  <div class="flex items-center mb-3">
                    <h5 class="font-medium text-blue-300">Dados avançados</h5>
                    <span v-if="getAdvancedDataCount(entity) > 0" class="ml-2 text-xs bg-blue-900 text-blue-200 px-2 py-1 rounded-full">
                      {{ getAdvancedDataCount(entity) }} registros
                    </span>
                  </div>
                  <advanced-data-panel :entity-data="entity" />
                </div>
              </template>

              <template v-else-if="selectedDomain === 'DB'">
                <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">Queries</div>
                    <div class="font-bold text-white">{{ formatMetricValue(getEntityMetric(entity, 'query_count')) }}</div>
                  </div>
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">Tempo Médio</div>
                    <div class="font-bold text-white">{{ formatMetricValue(getEntityMetric(entity, 'query_time_avg')) }} ms</div>
                  </div>
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">Conexões</div>
                    <div class="font-bold text-white">{{ formatMetricValue(getEntityMetric(entity, 'connection_count')) }}</div>
                  </div>
                </div>
                <div v-if="entityHasSlowQueries(entity)" class="mt-4">
                  <h5 class="font-medium text-yellow-300 mb-2">Queries lentas:</h5>
                  <div class="bg-gray-900 p-3 rounded text-xs overflow-auto max-h-40">
                    {{ getEntitySlowQueries(entity) }}
                  </div>
                </div>
                
                <!-- Painel de dados avançados para DB -->
                <div v-if="hasAdvancedData(entity)" class="mt-4 pt-4 border-t border-gray-700">
                  <div class="flex items-center mb-3">
                    <h5 class="font-medium text-blue-300">Dados avançados</h5>
                    <span v-if="getAdvancedDataCount(entity) > 0" class="ml-2 text-xs bg-blue-900 text-blue-200 px-2 py-1 rounded-full">
                      {{ getAdvancedDataCount(entity) }} registros
                    </span>
                  </div>
                  <advanced-data-panel :entity-data="entity" />
                </div>
              </template>

              <template v-else-if="selectedDomain === 'MOBILE'">
                <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">Crash Rate</div>
                    <div class="font-bold text-white">{{ formatMetricValue(getEntityMetric(entity, 'crash_rate')) }}%</div>
                  </div>
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">Erros HTTP</div>
                    <div class="font-bold text-white">{{ formatMetricValue(getEntityMetric(entity, 'http_errors')) }}</div>
                  </div>
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">Launch Time</div>
                    <div class="font-bold text-white">{{ formatMetricValue(getEntityMetric(entity, 'app_launch_time')) }} ms</div>
                  </div>
                </div>
                <div v-if="entityHasCrashes(entity)" class="mt-4">
                  <h5 class="font-medium text-red-300 mb-2">Crashes recentes:</h5>
                  <div class="bg-gray-900 p-3 rounded text-xs overflow-auto max-h-40">
                    {{ getEntityCrashes(entity) }}
                  </div>
                </div>
              </template>

              <template v-else-if="selectedDomain === 'IOT'">
                <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">Mensagens</div>
                    <div class="font-bold text-white">{{ formatMetricValue(getEntityMetric(entity, 'message_count')) }}</div>
                  </div>
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">Erros</div>
                    <div class="font-bold text-white">{{ formatMetricValue(getEntityMetric(entity, 'device_errors')) }}</div>
                  </div>
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">Conectados</div>
                    <div class="font-bold text-white">{{ getEntityMetric(entity, 'device_connected') ? 'Sim' : 'Não' }}</div>
                  </div>
                </div>
              </template>

              <template v-else-if="selectedDomain === 'SERVERLESS'">
                <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">Invocações</div>
                    <div class="font-bold text-white">{{ formatMetricValue(getEntityMetric(entity, 'invocation_count')) }}</div>
                  </div>
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">Duração</div>
                    <div class="font-bold text-white">{{ formatMetricValue(getEntityMetric(entity, 'duration_avg')) }} ms</div>
                  </div>
                  <div class="bg-gray-700 p-3 rounded">
                    <div class="text-gray-400">Taxa de erro</div>
                    <div class="font-bold text-white">{{ formatMetricValue(getEntityMetric(entity, 'error_rate')) }}%</div>
                  </div>
                </div>
              </template>

              <template v-else>
                <div class="bg-gray-700 p-3 rounded">
                  <div class="text-gray-400">Status</div>
                  <div class="font-bold text-white">{{ entityHasErrors(entity) ? 'Com Erros' : entityHasAlerts(entity) ? 'Com Alertas' : 'OK' }}</div>
                </div>
              </template>
            </div>
          </div>
        </template>
        <div v-else class="rounded-xl shadow-lg p-6 bg-gray-800 text-white flex items-center justify-center min-h-[120px]">
          <span class="text-gray-400">Nenhuma entidade com dados reais disponível neste domínio.</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  entities: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const selectedDomain = ref(null)

// Domínios disponíveis baseado nas entidades carregadas
const availableDomains = computed(() => {
  const domains = new Set()
  props.entities.forEach(entity => {
    if (entity.domain) {
      domains.add(entity.domain)
    }
  })
  return Array.from(domains)
})

// Funções auxiliares
const getDomainLabel = (domain) => {
  const labels = {
    'APM': 'Aplicações',
    'BROWSER': 'Frontend',
    'INFRA': 'Infraestrutura',
    'DB': 'Banco de Dados',
    'MOBILE': 'Mobile',
    'IOT': 'IoT',
    'SERVERLESS': 'Serverless',
    'EXT': 'Externo',
    'SYNTH': 'Sintéticos',
    'UNKNOWN': 'Desconhecido'
  }
  return labels[domain] || domain
}

const getDomainDescription = (domain) => {
  const descriptions = {
    'APM': 'Métricas de performance de aplicações, incluindo tempo de resposta, apdex e throughput.',
    'BROWSER': 'Métricas de frontend, incluindo Web Vitals e erros JavaScript.',
    'INFRA': 'Métricas de infraestrutura, incluindo CPU, memória e uptime.',
    'DB': 'Métricas de banco de dados, incluindo queries, conexões e latência.',
    'MOBILE': 'Métricas de aplicativos móveis, incluindo crashes e performance.',
    'IOT': 'Métricas de dispositivos IoT, incluindo conectividade e eventos.',
    'SERVERLESS': 'Métricas de funções serverless, incluindo invocações e duração.',
    'EXT': 'Métricas de serviços externos e integrações.',
    'SYNTH': 'Métricas de monitoramento sintético.'
  }
  return descriptions[domain] || 'Métricas gerais e status.'
}

const domainEntityCount = (domain) => {
  return props.entities.filter(entity => entity.domain === domain).length
}

const domainEntities = (domain) => {
  return props.entities.filter(entity => entity.domain === domain)
}

const domainAlerts = (domain) => {
  let count = 0
  props.entities.forEach(entity => {
    if (entity.domain === domain && entityHasAlerts(entity)) {
      count++
    }
  })
  return count
}

const domainErrors = (domain) => {
  let count = 0
  props.entities.forEach(entity => {
    if (entity.domain === domain && entityHasErrors(entity)) {
      count++
    }
  })
  return count
}

const domainAlertMessage = (domain) => {
  const alertCount = domainAlerts(domain)
  const errorCount = domainErrors(domain)
  
  if (errorCount > 0) {
    return `${errorCount} ${errorCount === 1 ? 'erro crítico detectado' : 'erros críticos detectados'} em ${domainEntityCount(domain)} ${domainEntityCount(domain) === 1 ? 'entidade' : 'entidades'}.`
  } else if (alertCount > 0) {
    return `${alertCount} ${alertCount === 1 ? 'alerta ativo' : 'alertas ativos'} em ${domainEntityCount(domain)} ${domainEntityCount(domain) === 1 ? 'entidade' : 'entidades'}.`
  }
  return 'Todas entidades operando normalmente.'
}

// Função para pegar o período mais recente disponível
const getLatestPeriod = (metricas) => {
  if (!metricas) return null
  const periods = ['30min', '24h', '7d', '30d']
  for (const p of periods) {
    if (metricas[p]) return metricas[p]
  }
  // fallback para qualquer período
  const keys = Object.keys(metricas)
  if (keys.length > 0) return metricas[keys[0]]
  return null
}

const entityHasAlerts = (entity) => {
  const metricas = getLatestPeriod(entity.metricas)
  if (!metricas) return false
  
  const domain = entity.domain
  
  if (domain === 'APM') {
    return (metricas.apdex && getMetricValue(metricas.apdex) < 0.7)
  } else if (domain === 'BROWSER') {
    return (metricas.largest_contentful_paint && getMetricValue(metricas.largest_contentful_paint) > 2500)
  } else if (domain === 'INFRA') {
    return (metricas.cpu && getMetricValue(metricas.cpu) > 80)
  } else if (domain === 'DB') {
    return (metricas.query_time_avg && getMetricValue(metricas.query_time_avg) > 500)
  } else if (domain === 'MOBILE') {
    return (metricas.crash_rate && getMetricValue(metricas.crash_rate) > 1)
  }
  
  return false
}

const entityHasErrors = (entity) => {
  const metricas = getLatestPeriod(entity.metricas)
  if (!metricas) return false
  
  const domain = entity.domain
  
  if (domain === 'APM') {
    return metricas.recent_error && Array.isArray(metricas.recent_error.results) && metricas.recent_error.results.length > 0
  } else if (domain === 'BROWSER') {
    return metricas.js_errors && Array.isArray(metricas.js_errors.results) && metricas.js_errors.results.length > 5
  } else if (domain === 'MOBILE') {
    return metricas.top_crashes && Array.isArray(metricas.top_crashes.results) && metricas.top_crashes.results.length > 0
  }
  
  return false
}

const entityHasJsErrors = (entity) => {
  const metricas = getLatestPeriod(entity.metricas)
  if (!metricas?.js_errors) return false
  return Array.isArray(metricas.js_errors.results) && metricas.js_errors.results.length > 0
}

const entityHasSlowQueries = (entity) => {
  const metricas = getLatestPeriod(entity.metricas)
  if (!metricas?.slowest_queries) return false
  return Array.isArray(metricas.slowest_queries.results) && metricas.slowest_queries.results.length > 0
}

const entityHasCrashes = (entity) => {
  const metricas = getLatestPeriod(entity.metricas)
  if (!metricas?.top_crashes) return false
  return Array.isArray(metricas.top_crashes.results) && metricas.top_crashes.results.length > 0
}

const getEntityMetric = (entity, metricName) => {
  const metricas = getLatestPeriod(entity.metricas)
  if (!metricas || !metricas[metricName]) return null
  return getMetricValue(metricas[metricName])
}

const getMetricValue = (metricData) => {
  if (!metricData) return null
  if (typeof metricData === 'number') return metricData
  if (metricData.results && metricData.results[0]) {
    // Pegar o primeiro valor numérico disponível no objeto de resultados
    const result = metricData.results[0]
    const numericValue = Object.values(result).find(v => typeof v === 'number')
    return numericValue || null
  }
  return null
}

const getEntityErrors = (entity) => {
  if (!entity.metricas?.ultima_hora?.recent_error?.results) return 'Sem dados de erro'
  return JSON.stringify(entity.metricas.ultima_hora.recent_error.results, null, 2)
}

const getEntityJsErrors = (entity) => {
  if (!entity.metricas?.ultima_hora?.js_errors?.results) return 'Sem erros JavaScript'
  return JSON.stringify(entity.metricas.ultima_hora.js_errors.results, null, 2)
}

const getEntitySlowQueries = (entity) => {
  if (!entity.metricas?.ultima_hora?.slowest_queries?.results) return 'Sem queries lentas'
  return JSON.stringify(entity.metricas.ultima_hora.slowest_queries.results, null, 2)
}

const getEntityCrashes = (entity) => {
  if (!entity.metricas?.ultima_hora?.top_crashes?.results) return 'Sem crashes'
  return JSON.stringify(entity.metricas.ultima_hora.top_crashes.results, null, 2)
}

const formatMetricValue = (value) => {
  if (value === null || value === undefined) return 'N/A'
  if (typeof value === 'number') {
    // Para valores pequenos (menores que 0.01), usar notação científica
    if (value !== 0 && Math.abs(value) < 0.01) {
      return value.toExponential(2)
    }
    // Para valores decimais, limitar a 2 casas decimais
    else if (value % 1 !== 0) {
      return value.toFixed(2)
    }
    // Para valores grandes, usar formatação com separadores de milhar
    else if (value > 999) {
      return value.toLocaleString()
    }
    // Caso contrário, retornar o valor como está
    return value.toString()
  }
  return value.toString()
}

const formatMemoryValue = (value) => {
  if (value === null || value === undefined) return 'N/A'
  
  // Se o valor for menor que 1024 bytes, mostrar em bytes
  if (value < 1024) return `${value} B`
  
  // Se o valor for menor que 1MB, mostrar em KB
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(2)} KB`
  
  // Se o valor for menor que 1GB, mostrar em MB
  if (value < 1024 * 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(2)} MB`
  
  // Caso contrário, mostrar em GB
  return `${(value / (1024 * 1024 * 1024)).toFixed(2)} GB`
}

const formatUptimeValue = (seconds) => {
  if (seconds === null || seconds === undefined) return 'N/A'
  
  // Converter segundos para dias, horas, minutos
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  
  if (days > 0) {
    return `${days}d ${hours}h`
  } else if (hours > 0) {
    return `${hours}h ${minutes}m`
  } else {
    return `${minutes}m`
  }
}

const selectDomain = (domain) => {
  selectedDomain.value = domain
}

// Métodos para dados avançados
const hasAdvancedData = (entity) => {
  return entity && (
    (entity.logs && entity.logs.length > 0) || 
    (entity.traces && entity.traces.length > 0) || 
    (entity.queries && entity.queries.length > 0) ||
    (entity.errors && entity.errors.length > 0)
  )
}

const getAdvancedDataCount = (entity) => {
  if (!entity) return 0
  let count = 0
  
  if (entity.logs) count += entity.logs.length
  if (entity.traces) count += entity.traces.length
  if (entity.queries) count += entity.queries.length
  if (entity.errors) count += entity.errors.length
  
  return count
}

// Importar componentes necessários
import AdvancedDataPanel from './AdvancedDataPanel.vue'
</script>

<script>
export default {
  components: {
    AdvancedDataPanel
  }
}
</script>

<style scoped>
</style>
