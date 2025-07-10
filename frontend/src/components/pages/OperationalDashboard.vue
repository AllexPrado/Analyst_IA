<template>
  <div class="py-8">
    <!-- Filtro de período -->
    <div class="flex flex-wrap gap-4 mb-8 items-end">
      <div>
        <label class="block text-gray-300 text-sm mb-1">Período</label>
        <select v-model="periodoSelecionado" class="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white">
          <option value="24h">Últimas 24h</option>
          <option value="7d">Últimos 7 dias</option>
          <option value="30d">Últimos 30 dias</option>
        </select>
      </div>
      <button @click="carregarDadosAvancados" class="bg-blue-700 hover:bg-blue-800 text-white px-4 py-2 rounded">Atualizar</button>
    </div>
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-4xl font-bold text-white mb-2">Dashboard Operacional</h1>
      <p class="text-gray-300">Monitoramento técnico e operacional detalhado</p>
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
      <span class="ml-4 text-gray-300">Carregando dados operacionais...</span>
    </div>

    <!-- Dashboard Content -->
    <div v-else class="space-y-8">
      <!-- Métricas Operacionais -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <!-- Response Time -->
        <div class="bg-gradient-to-br from-blue-900 to-blue-800 rounded-xl p-6 border border-blue-700">
          <div class="flex items-center justify-between mb-4">
            <div class="p-3 rounded-full bg-blue-700">
              <font-awesome-icon icon="clock" class="text-white text-xl" />
            </div>
            <span class="text-blue-200 text-xs">Média 24h</span>
          </div>
          <h3 class="text-blue-100 text-sm font-medium">Tempo de Resposta</h3>
          <p class="text-2xl font-bold text-white mt-2">{{ tempoResposta }}ms</p>
          <p class="text-blue-200 text-xs mt-1">{{ getTendencia(kpis?.tempo_resposta_tendencia) }}</p>
        </div>

        <!-- Throughput -->
        <div class="bg-gradient-to-br from-green-900 to-green-800 rounded-xl p-6 border border-green-700">
          <div class="flex items-center justify-between mb-4">
            <div class="p-3 rounded-full bg-green-700">
              <font-awesome-icon icon="tachometer-alt" class="text-white text-xl" />
            </div>
            <span class="text-green-200 text-xs">req/min</span>
          </div>
          <h3 class="text-green-100 text-sm font-medium">Throughput</h3>
          <p class="text-2xl font-bold text-white mt-2">{{ throughput }}</p>
          <p class="text-green-200 text-xs mt-1">{{ getTendencia(kpis?.throughput_tendencia) }}</p>
        </div>

        <!-- Error Rate -->
        <div class="bg-gradient-to-br from-red-900 to-red-800 rounded-xl p-6 border border-red-700">
          <div class="flex items-center justify-between mb-4">
            <div class="p-3 rounded-full bg-red-700">
              <font-awesome-icon icon="exclamation-triangle" class="text-white text-xl" />
            </div>
            <span class="text-red-200 text-xs">%</span>
          </div>
          <h3 class="text-red-100 text-sm font-medium">Taxa de Erro</h3>
          <p class="text-2xl font-bold text-white mt-2">{{ taxaErro }}%</p>
          <p class="text-red-200 text-xs mt-1">{{ getTendencia(kpis?.taxa_erro_tendencia) }}</p>
        </div>

        <!-- CPU Usage -->
        <div class="bg-gradient-to-br from-purple-900 to-purple-800 rounded-xl p-6 border border-purple-700">
          <div class="flex items-center justify-between mb-4">
            <div class="p-3 rounded-full bg-purple-700">
              <font-awesome-icon icon="microchip" class="text-white text-xl" />
            </div>
            <span class="text-purple-200 text-xs">Média</span>
          </div>
          <h3 class="text-purple-100 text-sm font-medium">CPU</h3>
          <p class="text-2xl font-bold text-white mt-2">{{ cpuUsage }}%</p>
          <p class="text-purple-200 text-xs mt-1">{{ getTendencia(kpis?.cpu_tendencia) }}</p>
        </div>
      </div>

      <!-- Gráficos de Monitoramento -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Gráfico de Performance -->
        <div class="bg-gray-900 rounded-xl p-6 border border-gray-700">
          <h3 class="text-xl font-semibold text-white mb-4">Performance ao Longo do Tempo</h3>
          <div class="h-64">
            <SafeApexChart
              type="line"
              height="100%"
              :options="chartPerformanceOptions"
              :series="chartPerformanceSeries"
            />
          </div>
        </div>

        <!-- Gráfico de Recursos -->
        <div class="bg-gray-900 rounded-xl p-6 border border-gray-700">
          <h3 class="text-xl font-semibold text-white mb-4">Utilização de Recursos</h3>
          <div class="h-64">
            <SafeApexChart
              type="area"
              height="100%"
              :options="chartRecursosOptions"
              :series="chartRecursosSeries"
            />
          </div>
        </div>
      </div>

      <!-- Alertas e Incidentes Ativos -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Alertas Ativos -->
        <div class="bg-gray-900 rounded-xl p-6 border border-gray-700">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-xl font-semibold text-white">Alertas Ativos</h3>
            <span class="bg-red-600 text-white px-2 py-1 rounded text-sm">{{ alertasAtivos.length }}</span>
          </div>
          <div v-if="alertasAtivos.length > 0" class="space-y-3 max-h-64 overflow-y-auto">
            <div v-for="(alerta, index) in alertasAtivos" :key="index" 
                 :class="`p-3 rounded border-l-4 ${getAlertaSeverityClass(alerta.severity)}`">
              <div class="flex items-start justify-between">
                <div>
                  <h4 class="font-medium text-white">{{ alerta.nome || alerta.title }}</h4>
                  <p class="text-gray-300 text-sm">{{ alerta.descricao || alerta.description }}</p>
                  <p class="text-gray-400 text-xs mt-1">{{ formatarTempo(alerta.timestamp) }}</p>
                </div>
                <span :class="`px-2 py-1 rounded text-xs ${getSeverityBadgeClass(alerta.severity)}`">
                  {{ alerta.severity }}
                </span>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-8 text-gray-400">
            <font-awesome-icon icon="check-circle" class="text-3xl text-green-500 mb-3" />
            <p>Nenhum alerta ativo</p>
          </div>
        </div>

        <!-- Incidentes Recentes -->
        <div class="bg-gray-900 rounded-xl p-6 border border-gray-700">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-xl font-semibold text-white">Incidentes Recentes</h3>
            <span class="bg-yellow-600 text-white px-2 py-1 rounded text-sm">{{ incidentesRecentes.length }}</span>
          </div>
          <div v-if="incidentesRecentes.length > 0" class="space-y-3 max-h-64 overflow-y-auto">
            <div v-for="(incidente, index) in incidentesRecentes" :key="index" 
                 class="p-3 rounded border-l-4 border-yellow-500 bg-yellow-900/20">
              <div class="flex items-start justify-between">
                <div>
                  <h4 class="font-medium text-white">{{ incidente.titulo || incidente.title }}</h4>
                  <p class="text-gray-300 text-sm">{{ incidente.descricao || incidente.description }}</p>
                  <p class="text-gray-400 text-xs mt-1">{{ formatarTempo(incidente.timestamp) }}</p>
                </div>
                <span :class="`px-2 py-1 rounded text-xs ${getIncidenteStatusClass(incidente.status)}`">
                  {{ incidente.status || 'Ativo' }}
                </span>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-8 text-gray-400">
            <font-awesome-icon icon="clipboard-check" class="text-3xl text-green-500 mb-3" />
            <p>Nenhum incidente recente</p>
          </div>
        </div>
      </div>

      <!-- Cobertura de Monitoramento -->
      <div class="bg-gray-900 rounded-xl p-6 border border-gray-700">
        <h3 class="text-xl font-semibold text-white mb-6">Cobertura de Monitoramento</h3>
        <div v-if="entidades && entidades.length > 0" class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-gray-700">
                <th class="text-left py-3 px-4 text-gray-300">Entidade</th>
                <th class="text-left py-3 px-4 text-gray-300">Tipo</th>
                <th class="text-left py-3 px-4 text-gray-300">Status</th>
                <th class="text-left py-3 px-4 text-gray-300">Apdex</th>
                <th class="text-left py-3 px-4 text-gray-300">Tempo Resposta</th>
                <th class="text-left py-3 px-4 text-gray-300">Taxa Erro</th>
                <th class="text-left py-3 px-4 text-gray-300">Última Atualização</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(entidade, index) in entidades.slice(0, 10)" :key="index" 
                  class="border-b border-gray-800 hover:bg-gray-800/50">
                <td class="py-3 px-4">
                  <div class="flex items-center">
                    <font-awesome-icon :icon="getEntityIcon(entidade.tipo)" class="text-blue-400 mr-2" />
                    <span class="text-white">{{ entidade.name }}</span>
                  </div>
                </td>
                <td class="py-3 px-4 text-gray-300">{{ entidade.tipo }}</td>
                <td class="py-3 px-4">
                  <span :class="`px-2 py-1 rounded text-xs ${getEntityStatusClass(entidade.status)}`">
                    {{ entidade.status || 'Unknown' }}
                  </span>
                </td>
                <td class="py-3 px-4 text-gray-300">{{ formatarMetrica(entidade.metricas?.apdex) }}</td>
                <td class="py-3 px-4 text-gray-300">{{ formatarMetrica(entidade.metricas?.tempo_resposta, 'ms') }}</td>
                <td class="py-3 px-4 text-gray-300">{{ formatarMetrica(entidade.metricas?.taxa_erro, '%') }}</td>
                <td class="py-3 px-4 text-gray-400 text-xs">{{ formatarTempo(entidade.ultima_atualizacao) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="text-center py-8 text-gray-400">
          <font-awesome-icon icon="database" class="text-3xl mb-3" />
          <p>Nenhuma entidade monitorada encontrada</p>
        </div>
      </div>

      <!-- Logs Recentes -->
      <div class="bg-gray-900 rounded-xl p-6 border border-gray-700">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-xl font-semibold text-white">Logs Recentes</h3>
          <div class="flex space-x-2">
            <button v-for="nivel in ['ERROR', 'WARN', 'INFO']" :key="nivel"
                    @click="filtroLog = nivel"
                    :class="`px-3 py-1 rounded text-xs ${filtroLog === nivel ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-300'}`">
              {{ nivel }}
            </button>
          </div>
        </div>
        <div v-if="logsRecentes.length > 0" class="space-y-2 max-h-64 overflow-y-auto">
          <div v-for="(log, index) in logsFiltrados" :key="index" 
               :class="`p-3 rounded text-sm ${getLogLevelClass(log.level || log.severity)}`">
            <div class="flex items-start justify-between">
              <div class="flex-1">
                <span class="text-xs text-gray-400">{{ formatarTempo(log.timestamp) }}</span>
                <span class="ml-2 font-medium">{{ log.level || log.severity }}</span>
                <p class="mt-1">{{ log.message }}</p>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-8 text-gray-400">
          <font-awesome-icon icon="file-alt" class="text-3xl mb-3" />
          <p>Nenhum log recente disponível</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { coletarNewRelic } from '../../api/agno.js'
import SafeApexChart from '../SafeApexChart.vue'

// Estado do componente
const carregando = ref(true)
const erro = ref(false)
const mensagemErro = ref('')
const filtroLog = ref('ERROR')


const entidades = ref([])
const entidadeSelecionada = ref('')
const periodoSelecionado = ref('7d')

// Dados avançados
const dadosAvancados = ref({})
const entidadeInfo = ref(null)
const kpis = ref(null)
const alertas = ref([])
const incidentes = ref([])
const logs = ref([])

// Computed properties para métricas e visão executiva
const tempoResposta = computed(() => {
  if (!kpis.value) return 'N/A'
  return kpis.value.tempo_resposta || kpis.value.tempo_resposta_medio || 'N/A'
})
const throughput = computed(() => {
  if (!kpis.value) return 'N/A'
  return kpis.value.throughput || 'N/A'
})
const taxaErro = computed(() => {
  if (!kpis.value) return 'N/A'
  return kpis.value.taxa_erro || kpis.value.taxa_erro_media ? (kpis.value.taxa_erro_media * 100).toFixed(2) : 'N/A'
})
const cpuUsage = computed(() => {
  if (!kpis.value) return 'N/A'
  return kpis.value.cpu || kpis.value.cpu_medio || 'N/A'
})
const alertasAtivos = computed(() => alertas.value.filter(a => a.status === 'active' || !a.status) || [])
const incidentesRecentes = computed(() => incidentes.value.slice(0, 5) || [])
const logsRecentes = computed(() => logs.value.slice(0, 20) || [])
const logsFiltrados = computed(() => logsRecentes.value.filter(log => (log.level || log.severity) === filtroLog.value).slice(0, 10))

// Configurações dos gráficos
const chartPerformanceOptions = ref({
  chart: { type: 'line', toolbar: { show: false }, background: 'transparent' },
  theme: { mode: 'dark' },
  colors: ['#3B82F6', '#10B981', '#F59E0B'],
  stroke: { curve: 'smooth', width: 2 },
  xaxis: { 
    categories: ['6h', '5h', '4h', '3h', '2h', '1h', 'Agora'],
    labels: { style: { colors: '#9CA3AF' } }
  },
  yaxis: { labels: { style: { colors: '#9CA3AF' } } },
  grid: { borderColor: '#374151' },
  legend: { labels: { colors: '#9CA3AF' } }
})

const chartPerformanceSeries = ref([
  { name: 'Tempo Resposta (ms)', data: [120, 115, 130, 125, 118, 122, 119] },
  { name: 'Throughput (req/min)', data: [450, 460, 440, 470, 465, 475, 468] },
  { name: 'Taxa Erro (%)', data: [2.1, 1.8, 2.5, 1.9, 1.7, 2.0, 1.8] }
])

const chartRecursosOptions = ref({
  chart: { type: 'area', toolbar: { show: false }, background: 'transparent' },
  theme: { mode: 'dark' },
  colors: ['#8B5CF6', '#06B6D4'],
  fill: { type: 'gradient', gradient: { opacityFrom: 0.6, opacityTo: 0.1 } },
  stroke: { curve: 'smooth', width: 2 },
  xaxis: { 
    categories: ['6h', '5h', '4h', '3h', '2h', '1h', 'Agora'],
    labels: { style: { colors: '#9CA3AF' } }
  },
  yaxis: { 
    labels: { style: { colors: '#9CA3AF' } },
    min: 0,
    max: 100
  },
  grid: { borderColor: '#374151' },
  legend: { labels: { colors: '#9CA3AF' } }
})

const chartRecursosSeries = ref([
  { name: 'CPU %', data: [45, 48, 52, 49, 47, 51, 50] },
  { name: 'Memória %', data: [65, 67, 70, 68, 66, 69, 68] }
])

// Funções utilitárias
const getTendencia = (valor) => {
  if (!valor) return 'Estável'
  return valor > 0 ? `↗ +${valor}%` : valor < 0 ? `↘ ${valor}%` : 'Estável'
}

const getAlertaSeverityClass = (severity) => {
  switch (severity) {
    case 'critical': return 'border-red-500 bg-red-900/20'
    case 'warning': return 'border-yellow-500 bg-yellow-900/20'
    case 'info': return 'border-blue-500 bg-blue-900/20'
    default: return 'border-gray-500 bg-gray-900/20'
  }
}

const getSeverityBadgeClass = (severity) => {
  switch (severity) {
    case 'critical': return 'bg-red-900 text-red-200'
    case 'warning': return 'bg-yellow-900 text-yellow-200'
    case 'info': return 'bg-blue-900 text-blue-200'
    default: return 'bg-gray-900 text-gray-200'
  }
}

const getIncidenteStatusClass = (status) => {
  switch (status) {
    case 'resolved': return 'bg-green-900 text-green-200'
    case 'investigating': return 'bg-yellow-900 text-yellow-200'
    case 'active': return 'bg-red-900 text-red-200'
    default: return 'bg-orange-900 text-orange-200'
  }
}

const getEntityIcon = (tipo) => {
  switch (tipo) {
    case 'APPLICATION': return ['fas', 'cube']
    case 'HOST': return ['fas', 'server']
    case 'BROWSER': return ['fas', 'globe']
    case 'MOBILE': return ['fas', 'mobile-alt']
    default: return ['fas', 'cog']
  }
}

const getEntityStatusClass = (status) => {
  switch (status) {
    case 'healthy': return 'bg-green-900 text-green-200'
    case 'warning': return 'bg-yellow-900 text-yellow-200'
    case 'critical': return 'bg-red-900 text-red-200'
    default: return 'bg-gray-900 text-gray-200'
  }
}

const getLogLevelClass = (level) => {
  switch (level) {
    case 'ERROR': return 'bg-red-900/30 border-l-4 border-red-500'
    case 'WARN': return 'bg-yellow-900/30 border-l-4 border-yellow-500'
    case 'INFO': return 'bg-blue-900/30 border-l-4 border-blue-500'
    default: return 'bg-gray-900/30 border-l-4 border-gray-500'
  }
}

const formatarMetrica = (valor, unidade = '') => {
  if (valor === null || valor === undefined || valor === 'N/A') return 'N/A'
  if (typeof valor === 'number') {
    return `${valor.toFixed(2)}${unidade}`
  }
  return `${valor}${unidade}`
}

const formatarTempo = (timestamp) => {
  if (!timestamp) return 'N/A'
  try {
    const data = new Date(timestamp)
    return data.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return 'N/A'
  }
}

// Função utilitária para gerar um session_id único
function gerarNovoSessionId() {
  return 'sess_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
}
// session_id persistente por usuário
let session_id = localStorage.getItem('session_id');
if (!session_id) {
  session_id = gerarNovoSessionId();
  localStorage.setItem('session_id', session_id);
}

// Carrega entidades usando o endpoint correto do Agno
const carregarEntidades = async () => {
  carregando.value = true;
  try {
    // Coleta todas as entidades monitoradas
    const resp = await coletarNewRelic({ periodo: periodoSelecionado.value, tipo: 'entidades' });
    if (resp && resp.dados && Array.isArray(resp.dados)) {
      entidades.value = resp.dados;
      if (resp.dados.length > 0 && !entidadeSelecionada.value) {
        entidadeSelecionada.value = resp.dados[0].guid || resp.dados[0].id || resp.dados[0].name;
      }
    } else {
      erro.value = true;
      mensagemErro.value = 'Nenhuma entidade encontrada.';
    }
  } catch (e) {
    erro.value = true;
    mensagemErro.value = 'Erro ao carregar entidades.';
  } finally {
    carregando.value = false;
  }
}

// Carrega dados completos do backend para o dashboard operacional usando Agno
const carregarDadosAvancados = async () => {
  if (!entidadeSelecionada.value) return;
  carregando.value = true;
  erro.value = false;
  mensagemErro.value = '';
  try {
    // Coletar métricas e dados avançados da entidade selecionada
    const dadosResp = await coletarNewRelic({ entidade: entidadeSelecionada.value, periodo: periodoSelecionado.value, tipo: 'metricas' });
    if (dadosResp && dadosResp.dados) {
      dadosAvancados.value = dadosResp.dados;
      // Exemplo: se dadosResp.dados traz alertas, incidentes, logs, etc
      alertas.value = Array.isArray(dadosResp.dados.alertas) ? dadosResp.dados.alertas : [];
      incidentes.value = Array.isArray(dadosResp.dados.incidentes) ? dadosResp.dados.incidentes : [];
      logs.value = Array.isArray(dadosResp.dados.logs) ? dadosResp.dados.logs : [];
      kpis.value = dadosResp.dados.metricas || {};
      entidadeInfo.value = dadosResp.dados.entidade || null;
    } else {
      erro.value = true;
      mensagemErro.value = 'Dados indisponíveis para a entidade/período.';
    }
  } catch (e) {
    erro.value = true;
    mensagemErro.value = 'Erro ao buscar dados do backend.';
  } finally {
    carregando.value = false;
  }
}

onMounted(async () => {
  await carregarEntidades()
  await carregarDadosAvancados()
})
</script>

<style scoped>
/* Estilos específicos se necessário */
</style>
