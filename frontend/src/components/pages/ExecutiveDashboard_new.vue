<template>
  <div class="py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-4xl font-bold text-white mb-2">Dashboard Executivo</h1>
      <p class="text-gray-300">Visão executiva dos KPIs e métricas críticas do negócio</p>
    </div>

    <!-- Indicador de problemas -->
    <div v-if="erro" class="bg-red-900/30 border border-red-700 rounded-lg p-4 mb-6">
      <div class="flex items-center">
        <font-awesome-icon icon="exclamation-triangle" class="text-red-400 mr-3" />
        <div>
          <h3 class="text-red-300 font-semibold">Problema com dados do backend</h3>
          <p class="text-red-200 text-sm">{{ mensagemErro }}</p>
          <button @click="carregarDados" class="mt-2 bg-red-600 hover:bg-red-700 px-4 py-2 rounded text-white text-sm">
            Tentar novamente
          </button>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="carregando" class="flex items-center justify-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      <span class="ml-4 text-gray-300">Carregando dados...</span>
    </div>

    <!-- Dashboard Content -->
    <div v-else class="space-y-8">
      <!-- KPIs Principais -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <!-- Status Geral -->
        <div class="bg-gradient-to-br from-green-900 to-green-800 rounded-xl p-6 border border-green-700">
          <div class="flex items-center justify-between mb-4">
            <div class="p-3 rounded-full bg-green-700">
              <font-awesome-icon icon="heartbeat" class="text-white text-xl" />
            </div>
            <span :class="`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(statusSistema)}`">
              {{ statusSistema }}
            </span>
          </div>
          <h3 class="text-green-100 text-sm font-medium">Status do Sistema</h3>
          <p class="text-2xl font-bold text-white mt-2">{{ disponibilidade }}%</p>
          <p class="text-green-200 text-xs mt-1">Disponibilidade</p>
        </div>

        <!-- Receita/Performance -->
        <div class="bg-gradient-to-br from-blue-900 to-blue-800 rounded-xl p-6 border border-blue-700">
          <div class="flex items-center justify-between mb-4">
            <div class="p-3 rounded-full bg-blue-700">
              <font-awesome-icon icon="chart-line" class="text-white text-xl" />
            </div>
            <span class="text-blue-200 text-xs">24h</span>
          </div>
          <h3 class="text-blue-100 text-sm font-medium">Performance</h3>
          <p class="text-2xl font-bold text-white mt-2">{{ apdexMedio }}</p>
          <p class="text-blue-200 text-xs mt-1">Apdex Score</p>
        </div>

        <!-- Incidentes -->
        <div class="bg-gradient-to-br from-red-900 to-red-800 rounded-xl p-6 border border-red-700">
          <div class="flex items-center justify-between mb-4">
            <div class="p-3 rounded-full bg-red-700">
              <font-awesome-icon icon="exclamation-circle" class="text-white text-xl" />
            </div>
            <span class="text-red-200 text-xs">Ativo</span>
          </div>
          <h3 class="text-red-100 text-sm font-medium">Incidentes Críticos</h3>
          <p class="text-2xl font-bold text-white mt-2">{{ incidentesCriticos }}</p>
          <p class="text-red-200 text-xs mt-1">Requer atenção</p>
        </div>

        <!-- Cobertura -->
        <div class="bg-gradient-to-br from-purple-900 to-purple-800 rounded-xl p-6 border border-purple-700">
          <div class="flex items-center justify-between mb-4">
            <div class="p-3 rounded-full bg-purple-700">
              <font-awesome-icon icon="shield-alt" class="text-white text-xl" />
            </div>
            <span class="text-purple-200 text-xs">Monitoramento</span>
          </div>
          <h3 class="text-purple-100 text-sm font-medium">Cobertura</h3>
          <p class="text-2xl font-bold text-white mt-2">{{ coberturaPercentual }}%</p>
          <p class="text-purple-200 text-xs mt-1">{{ entidadesMonitoradas }}/{{ totalEntidades }} entidades</p>
        </div>
      </div>

      <!-- Gráficos Executivos -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Tendência de Performance -->
        <div class="bg-gray-900 rounded-xl p-6 border border-gray-700">
          <h3 class="text-xl font-semibold text-white mb-4">Tendência de Performance (7 dias)</h3>
          <div class="h-64">
            <SafeApexChart
              type="line"
              height="100%"
              :options="chartPerformanceOptions"
              :series="chartPerformanceSeries"
            />
          </div>
        </div>

        <!-- Distribuição de Alertas -->
        <div class="bg-gray-900 rounded-xl p-6 border border-gray-700">
          <h3 class="text-xl font-semibold text-white mb-4">Distribuição de Alertas</h3>
          <div class="h-64">
            <SafeApexChart
              type="donut"
              height="100%"
              :options="chartAlertasOptions"
              :series="chartAlertasSeries"
            />
          </div>
        </div>
      </div>

      <!-- Insights e Recomendações -->
      <div class="bg-gray-900 rounded-xl p-6 border border-gray-700">
        <h3 class="text-xl font-semibold text-white mb-6">Insights Executivos e Recomendações</h3>
        <div v-if="insights && insights.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="(insight, index) in insights.slice(0, 6)" :key="index" 
               :class="`p-4 rounded-lg border-l-4 ${getInsightColor(insight.prioridade)}`">
            <div class="flex items-start justify-between mb-2">
              <h4 class="font-semibold text-white">{{ insight.titulo }}</h4>
              <span :class="`px-2 py-1 rounded text-xs ${getPrioridadeClass(insight.prioridade)}`">
                {{ insight.prioridade }}
              </span>
            </div>
            <p class="text-gray-300 text-sm mb-3">{{ insight.descricao }}</p>
            <div class="text-xs text-gray-400">
              Impacto: {{ insight.impacto || 'Médio' }}
            </div>
          </div>
        </div>
        <div v-else class="text-center py-8 text-gray-400">
          <font-awesome-icon icon="lightbulb" class="text-3xl mb-3" />
          <p>Nenhum insight disponível no momento</p>
        </div>
      </div>

      <!-- Resumo Diagnóstico IA -->
      <div v-if="diagnostico" class="bg-gradient-to-r from-blue-900 to-indigo-900 rounded-xl p-6 border border-blue-700">
        <div class="flex items-center mb-4">
          <font-awesome-icon icon="brain" class="text-blue-400 text-2xl mr-3" />
          <h3 class="text-xl font-semibold text-white">Diagnóstico da IA</h3>
        </div>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h4 class="text-blue-300 font-medium mb-2">Análise Principal</h4>
            <p class="text-gray-200">{{ diagnostico.explicacao || 'Análise em andamento...' }}</p>
          </div>
          <div>
            <h4 class="text-blue-300 font-medium mb-2">Impacto no Negócio</h4>
            <p class="text-gray-200">{{ diagnostico.impacto || 'Impacto sendo calculado...' }}</p>
          </div>
        </div>
        <div v-if="diagnostico.recomendacoes && diagnostico.recomendacoes.length > 0" class="mt-4">
          <h4 class="text-blue-300 font-medium mb-2">Recomendações Prioritárias</h4>
          <ul class="space-y-1">
            <li v-for="(rec, index) in diagnostico.recomendacoes.slice(0, 3)" :key="index" 
                class="text-gray-200 text-sm">
              • {{ rec }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { getResumoGeral, getStatus, getKPIs, getInsights } from '../../api/backend.js'
import SafeApexChart from '../SafeApexChart.vue'

// Estado do componente
const carregando = ref(true)
const erro = ref(false)
const mensagemErro = ref('')

// Dados do dashboard
const dadosResumo = ref(null)
const dadosStatus = ref(null)
const dadosKPIs = ref(null)
const dadosInsights = ref(null)

// Computed properties para KPIs
const statusSistema = computed(() => {
  if (!dadosStatus.value) return 'UNKNOWN'
  return dadosStatus.value.statusGeral || 'UNKNOWN'
})

const disponibilidade = computed(() => {
  if (!dadosStatus.value) return 0
  return dadosStatus.value.disponibilidade || 0
})

const apdexMedio = computed(() => {
  if (!dadosKPIs.value) return 'N/A'
  return dadosKPIs.value.apdex_medio || 'N/A'
})

const incidentesCriticos = computed(() => {
  if (!dadosResumo.value) return 0
  return dadosResumo.value.severidade_critica || 0
})

const entidadesMonitoradas = computed(() => {
  if (!dadosStatus.value) return 0
  return dadosStatus.value.entidadesComMetricas || 0
})

const totalEntidades = computed(() => {
  if (!dadosStatus.value) return 0
  return dadosStatus.value.totalEntidades || 0
})

const coberturaPercentual = computed(() => {
  const total = totalEntidades.value
  const monitoradas = entidadesMonitoradas.value
  if (total === 0) return 0
  return Math.round((monitoradas / total) * 100)
})

const insights = computed(() => {
  if (!dadosInsights.value || !dadosInsights.value.recomendacoes) return []
  return dadosInsights.value.recomendacoes
})

const diagnostico = computed(() => {
  return dadosResumo.value || null
})

// Configurações dos gráficos
const chartPerformanceOptions = ref({
  chart: { type: 'line', toolbar: { show: false }, background: 'transparent' },
  theme: { mode: 'dark' },
  colors: ['#3B82F6', '#10B981', '#F59E0B'],
  stroke: { curve: 'smooth', width: 3 },
  xaxis: { 
    categories: ['6d', '5d', '4d', '3d', '2d', '1d', 'Hoje'],
    labels: { style: { colors: '#9CA3AF' } }
  },
  yaxis: { 
    labels: { style: { colors: '#9CA3AF' } },
    min: 0,
    max: 1
  },
  grid: { borderColor: '#374151' },
  legend: { labels: { colors: '#9CA3AF' } }
})

const chartPerformanceSeries = ref([
  { name: 'Apdex', data: [0.85, 0.87, 0.82, 0.90, 0.88, 0.91, 0.89] },
  { name: 'Disponibilidade', data: [0.99, 0.995, 0.98, 0.992, 0.994, 0.996, 0.998] }
])

const chartAlertasOptions = ref({
  chart: { type: 'donut', background: 'transparent' },
  theme: { mode: 'dark' },
  colors: ['#EF4444', '#F59E0B', '#10B981'],
  labels: ['Crítico', 'Alerta', 'Normal'],
  legend: { labels: { colors: '#9CA3AF' } },
  plotOptions: {
    pie: { donut: { size: '60%' } }
  }
})

const chartAlertasSeries = ref([5, 12, 83])

// Funções utilitárias
const getStatusColor = (status) => {
  switch (status) {
    case 'OPERATIONAL': return 'bg-green-600 text-green-100'
    case 'DEGRADED': return 'bg-yellow-600 text-yellow-100'
    case 'CRITICAL': return 'bg-red-600 text-red-100'
    default: return 'bg-gray-600 text-gray-100'
  }
}

const getInsightColor = (prioridade) => {
  switch (prioridade) {
    case 'alta': return 'border-red-500 bg-red-900/20'
    case 'media': return 'border-yellow-500 bg-yellow-900/20'
    case 'baixa': return 'border-green-500 bg-green-900/20'
    default: return 'border-blue-500 bg-blue-900/20'
  }
}

const getPrioridadeClass = (prioridade) => {
  switch (prioridade) {
    case 'alta': return 'bg-red-900 text-red-200'
    case 'media': return 'bg-yellow-900 text-yellow-200'
    case 'baixa': return 'bg-green-900 text-green-200'
    default: return 'bg-blue-900 text-blue-200'
  }
}

// Função para carregar dados
const carregarDados = async () => {
  carregando.value = true
  erro.value = false
  mensagemErro.value = ''

  try {
    // Carrega dados em paralelo
    const [resumo, status, kpis, insights] = await Promise.all([
      getResumoGeral(),
      getStatus(),
      getKPIs(),
      getInsights()
    ])

    // Verifica se há algum erro
    const temErro = [resumo, status, kpis, insights].some(data => data && data.erro)
    
    if (temErro) {
      erro.value = true
      mensagemErro.value = 'Alguns dados não puderam ser carregados. Verifique se o backend está funcionando.'
    }

    // Armazena os dados (mesmo com alguns erros)
    dadosResumo.value = resumo && !resumo.erro ? resumo : null
    dadosStatus.value = status && !status.erro ? status : null
    dadosKPIs.value = kpis && !kpis.erro ? kpis : null
    dadosInsights.value = insights && !insights.erro ? insights : null

    // Atualiza séries dos gráficos com dados reais se disponível
    if (dadosKPIs.value && dadosKPIs.value.historico) {
      atualizarGraficos()
    }

  } catch (error) {
    console.error('Erro ao carregar dashboard executivo:', error)
    erro.value = true
    mensagemErro.value = 'Erro ao conectar com o backend. Verifique se o serviço está em execução.'
  } finally {
    carregando.value = false
  }
}

const atualizarGraficos = () => {
  // Atualiza gráficos com dados reais se disponível
  if (dadosKPIs.value && dadosKPIs.value.historico) {
    const historico = dadosKPIs.value.historico
    if (historico.apdex && historico.disponibilidade) {
      chartPerformanceSeries.value = [
        { name: 'Apdex', data: historico.apdex },
        { name: 'Disponibilidade', data: historico.disponibilidade }
      ]
    }
  }

  // Atualiza gráfico de alertas
  if (dadosResumo.value) {
    const criticos = dadosResumo.value.severidade_critica || 0
    const total = dadosResumo.value.total_alertas || 0
    const normais = Math.max(0, 100 - total)
    const alertas = Math.max(0, total - criticos)

    chartAlertasSeries.value = [criticos, alertas, normais]
  }
}

// Inicialização
onMounted(() => {
  carregarDados()
})
</script>

<style scoped>
/* Estilos específicos se necessário */
</style>
