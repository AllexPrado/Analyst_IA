<template>  <div class="p-6 bg-gradient-to-br from-blue-50 to-white min-h-screen">
    <div v-if="erroDashboard" class="flex flex-col items-center justify-center h-96">
      <font-awesome-icon icon="exclamation-triangle" class="text-yellow-400 text-3xl mb-2" />
      <span class="text-yellow-300 text-lg">{{ mensagemErroDashboard || 'Erro ao carregar dados do dashboard.' }}</span>
      <button @click="fetchDashboard" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Tentar novamente</button>
    </div>
    <div v-else>
      <h1 class="text-5xl font-extrabold text-blue-700 text-center mb-10 drop-shadow-lg">Analyst_IA Dashboard</h1>
      
      <!-- Banner de status do sistema -->
      <div v-if="systemHealth && systemHealth.fallback_mode" class="mb-6 bg-amber-50 border-l-4 border-amber-400 p-4 rounded-r-lg">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-amber-400" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <p class="text-sm text-amber-700">
              <strong>Modo Fallback Ativado:</strong> O sistema está utilizando dados em cache devido a limitações da API do New Relic.
              <span v-if="systemHealth.newrelic_collector && systemHealth.newrelic_collector.circuit_breaker">
                Status: {{ systemHealth.newrelic_collector.circuit_breaker.circuit_state }}
              </span>
            </p>
          </div>
        </div>
      </div>
      
      <div v-if="carregando" class="flex justify-center mb-8">
        <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        <span class="ml-3 text-blue-600">Carregando dados...</span>
      </div>
      <div v-if="diagnostico && diagnostico.metricas && Array.isArray(diagnostico.metricas) && diagnostico.metricas.length > 0" class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="bg-white rounded-xl shadow-lg p-6 flex flex-col items-center border-t-4" 
             :class="{'border-blue-500': statusGeral.status === 'OK', 'border-yellow-500': statusGeral.status === 'ALERTA', 'border-red-500': statusGeral.status === 'CRÍTICO'}">
          <span class="text-2xl font-bold text-blue-600 mb-2">Status Geral</span>
          <span class="text-4xl font-extrabold" :class="statusGeral.classe">{{ statusGeral.texto }}</span>
          <span class="text-gray-500 mt-2">{{ statusGeral.descricao }}</span>
        </div>
        <div class="bg-white rounded-xl shadow-lg p-6 flex flex-col items-center border-t-4 border-yellow-500">
          <span class="text-2xl font-bold text-yellow-600 mb-2">Alertas Recentes</span>
          <span class="text-4xl font-extrabold text-yellow-500">{{ resumoIncidentes.total_alertas || 0 }}</span>
          <span class="text-gray-500 mt-2" v-if="alertas && alertas.length > 0">
            {{ alertas.length > 1 ? `${alertas[0]?.name || 'Alerta'} e mais ${alertas.length - 1}` : (alertas[0]?.name || 'Alerta') }}
          </span>
          <span class="text-gray-500 mt-2" v-else>Nenhum alerta recente</span>
        </div>
        <div class="bg-white rounded-xl shadow-lg p-6 flex flex-col items-center border-t-4 border-red-500">
          <span class="text-2xl font-bold text-red-600 mb-2">Erros Críticos</span>
          <span class="text-4xl font-extrabold text-red-500">{{ resumoIncidentes.severidade_critica || 0 }}</span>
          <span class="text-gray-500 mt-2">{{ (resumoIncidentes.severidade_critica || 0) > 0 ? 'Verifique os alertas críticos' : 'Nenhum erro crítico' }}</span>
        </div>
      </div>
      <div v-else class="mb-8">
        <div class="bg-white rounded-xl shadow-lg p-6 flex items-center justify-center min-h-[120px]">
          <span class="text-gray-400">Nenhum dado real disponível para exibir os cards principais.</span>
        </div>
      </div>
      <div v-if="diagnostico && diagnostico.metricas && Array.isArray(diagnostico.metricas) && diagnostico.metricas.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        <div class="bg-white rounded-xl shadow-lg p-6">
          <SafeApexChart 
            type="bar" 
            height="300" 
            :options="barOptions" 
            :series="barSeries"
            noDataMessage="Dados insuficientes para gráfico de barras"
            noDataIcon="chart-bar"
          />
        </div>
        <div class="bg-white rounded-xl shadow-lg p-6">
          <SafeApexChart 
            type="line" 
            height="300" 
            :options="lineOptions" 
            :series="lineSeries"
            noDataMessage="Dados insuficientes para gráfico de linha" 
            noDataIcon="chart-line"
          />
        </div>
      </div>
      <div v-else class="mb-8">
        <div class="bg-white rounded-xl shadow-lg p-6 flex items-center justify-center min-h-[120px]">
          <span class="text-gray-400">Nenhum dado real disponível para exibir os gráficos.</span>
        </div>
      </div>
      <!-- Diagnóstico detalhado -->
      <div class="bg-white rounded-xl shadow-lg p-8 mt-8 border-l-8 border-blue-600">
        <h2 class="text-2xl font-bold text-blue-700 mb-4">Diagnóstico da IA</h2>
        <div v-if="diagnostico && diagnostico.metricas && diagnostico.metricas.length">
          <p class="text-gray-700 text-lg leading-relaxed mb-2">
            <span class="font-semibold text-blue-600">Explicação:</span> {{ diagnostico.explicacao }}
          </p>
          <p class="text-gray-700 text-lg leading-relaxed mb-2">
            <span class="font-semibold text-yellow-600">Impacto:</span> {{ diagnostico.impacto }}
          </p>
          <p class="text-gray-700 text-lg leading-relaxed mb-2">
            <span class="font-semibold text-green-600">Recomendação Técnica:</span> {{ diagnostico.recomendacao_tecnica }}
          </p>
          <p class="text-gray-700 text-lg leading-relaxed mb-2">
            <span class="font-semibold text-purple-600">Recomendação Executiva:</span> {{ diagnostico.recomendacao_executiva }}
          </p>
          <div v-if="diagnostico && diagnostico.metricas && Array.isArray(diagnostico.metricas) && diagnostico.metricas.length > 0">
            <h3 class="text-lg font-bold text-blue-700 mt-4 mb-2">Métricas Detalhadas</h3>
            <table class="min-w-full text-sm text-gray-700">
              <thead>
                <tr>
                  <th class="px-2 py-1">Entidade</th>
                  <th class="px-2 py-1">Domínio</th>
                  <th class="px-2 py-1">Métrica</th>
                  <th class="px-2 py-1">Valor</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(met, idx) in diagnostico.metricas" :key="idx" v-if="met && typeof met === 'object'">
                  <td class="px-2 py-1">{{ met.entidade || 'N/A' }}</td>
                  <td class="px-2 py-1">{{ met.dominio || 'N/A' }}</td>
                  <td class="px-2 py-1">{{ met.nome || 'N/A' }}</td>
                  <td class="px-2 py-1">{{ met.valor !== null && met.valor !== undefined ? met.valor : 'N/A' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="diagnostico && diagnostico.metricas && Array.isArray(diagnostico.metricas) && diagnostico.metricas.length > 0">
            <h3 class="text-lg font-bold text-blue-700 mt-6 mb-2">Detalhes Avançados</h3>
            <div v-for="(met, idx) in diagnostico.metricas" :key="'detalhe-' + idx" v-if="met && met.detalhes && typeof met.detalhes === 'object'">
              <div class="bg-gray-50 rounded p-3 mb-2">
                <div class="font-semibold text-blue-800">{{ met.entidade || 'N/A' }} ({{ met.dominio || 'N/A' }})</div>
                <div v-if="met.detalhes.erros_detalhados && Array.isArray(met.detalhes.erros_detalhados) && met.detalhes.erros_detalhados.length > 0">
                  <div class="text-sm font-bold text-red-700 mt-2">Erros Detalhados:</div>
                  <ul class="list-disc ml-6">
                    <li v-for="(err, i) in met.detalhes.erros_detalhados" :key="'err-' + i">
                      {{ (err && typeof err === 'object') ? (err.message || err.errorClass || JSON.stringify(err)) : (err || 'Erro não especificado') }}
                    </li>
                  </ul>
                </div>
                <div v-if="met.detalhes.queries_sql && Array.isArray(met.detalhes.queries_sql) && met.detalhes.queries_sql.length > 0">
                  <div class="text-sm font-bold text-green-700 mt-2">Queries SQL:</div>
                  <ul class="list-disc ml-6">
                    <li v-for="(q, i) in met.detalhes.queries_sql" :key="'q-' + i">
                      {{ (q && typeof q === 'object') ? (q.query || 'Query não especificada') : (q || 'Query não especificada') }}
                      <span v-if="q && q.backtrace">(Backtrace: {{ q.backtrace }})</span>
                    </li>
                  </ul>
                </div>
                <div v-if="met.detalhes.logs && Array.isArray(met.detalhes.logs) && met.detalhes.logs.length > 0">
                  <div class="text-sm font-bold text-gray-700 mt-2">Logs:</div>
                  <ul class="list-disc ml-6">
                    <li v-for="(log, i) in met.detalhes.logs" :key="'log-' + i">
                      {{ (log && typeof log === 'object') ? (log.message || JSON.stringify(log)) : (log || 'Log não especificado') }}
                    </li>
                  </ul>
                </div>
                <div v-if="met.detalhes.traces && Array.isArray(met.detalhes.traces) && met.detalhes.traces.length > 0">
                  <div class="text-sm font-bold text-purple-700 mt-2">Traces:</div>
                  <ul class="list-disc ml-6">
                    <li v-for="(trace, i) in met.detalhes.traces" :key="'trace-' + i">
                      {{ (trace && typeof trace === 'object') ? (trace.name || trace.id || JSON.stringify(trace)) : (trace || 'Trace não especificado') }}
                    </li>
                  </ul>
                </div>
                <div v-if="met.detalhes.attributes && Array.isArray(met.detalhes.attributes) && met.detalhes.attributes.length > 0">
                  <div class="text-sm font-bold text-blue-700 mt-2">Atributos:</div>
                  <ul class="list-disc ml-6">
                    <li v-for="(attr, i) in met.detalhes.attributes" :key="'attr-' + i">
                      {{ (attr && typeof attr === 'object') ? JSON.stringify(attr) : (attr || 'Atributo não especificado') }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-else>
          <span class="text-gray-500">Nenhum diagnóstico disponível com dados reais.</span>
        </div>
      </div>

      <!-- Chat da IA -->
      <div class="max-w-2xl mx-auto mt-12">
        <div class="bg-white rounded-xl shadow-lg p-6">
          <h2 class="text-xl font-bold text-blue-700 mb-4">Converse com a IA</h2>
          <ChatPanel @submit="handleChat" />
          <div v-if="chatResposta" class="mt-4 p-4 bg-blue-50 rounded text-gray-800">
            <span class="font-semibold text-blue-600">Resposta da IA:</span>
            <div class="mt-2">{{ chatResposta }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import ChatPanel from './ChatPanel.vue'
import VueApexCharts from "vue3-apexcharts"
import SafeApexChart from './SafeApexChart.vue'
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { getResumoGeral } from '../api/backend.js'

const diagnostico = ref(null)
const carregando = ref(true)
const chatResposta = ref('')
const systemHealth = ref(null)
const erroDashboard = ref(false)
const mensagemErroDashboard = ref('')

const statusGeral = computed(() => {
  if (!diagnostico.value || !diagnostico.value.metricas || !Array.isArray(diagnostico.value.metricas) || diagnostico.value.metricas.length === 0) {
    return { 
      status: 'UNKNOWN', 
      texto: 'Indeterminado', 
      descricao: 'Dados não disponíveis', 
      classe: 'text-gray-500' 
    }
  }
  
  const severidadeCritica = (diagnostico.value.severidade_critica && typeof diagnostico.value.severidade_critica === 'number') ? diagnostico.value.severidade_critica : 0
  const totalAlertas = (diagnostico.value.total_alertas && typeof diagnostico.value.total_alertas === 'number') ? diagnostico.value.total_alertas : 0
  
  const severidade = severidadeCritica > 0 ? 'CRÍTICO' : (totalAlertas > 0 ? 'ALERTA' : 'OK')
  const textoStatus = {
    'CRÍTICO': 'Crítico',
    'ALERTA': 'Atenção',
    'OK': 'Normal'
  }[severidade]

  return {
    status: severidade,
    texto: textoStatus,
    descricao: severidade === 'CRÍTICO' ? 'Verifique os alertas críticos imediatamente!' : (severidade === 'ALERTA' ? 'Existem alertas que requerem atenção.' : 'Tudo está funcionando normalmente.'),
    classe: severidade === 'CRÍTICO' ? 'text-red-500' : (severidade === 'ALERTA' ? 'text-yellow-500' : 'text-green-500')
  }
})

// Cards dinâmicos com proteção robusta
const totalEntidades = computed(() => {
  if (!diagnostico.value?.metricas || !Array.isArray(diagnostico.value.metricas)) return 0
  return diagnostico.value.metricas.length
})

const entidadesComMetricas = computed(() => {
  if (!diagnostico.value?.metricas || !Array.isArray(diagnostico.value.metricas)) return 0
  return diagnostico.value.metricas.filter(m => 
    m && m.valor !== null && m.valor !== undefined && m.valor !== '' && !isNaN(m.valor)
  ).length
})

const resumoIncidentes = computed(() => {
  if (!diagnostico.value || typeof diagnostico.value !== 'object') {
    return { total_alertas: 0, severidade_critica: 0 }
  }
  
  return {
    total_alertas: (diagnostico.value.total_alertas && typeof diagnostico.value.total_alertas === 'number') ? diagnostico.value.total_alertas : 0,
    severidade_critica: (diagnostico.value.severidade_critica && typeof diagnostico.value.severidade_critica === 'number') ? diagnostico.value.severidade_critica : 0
  }
})

const alertas = computed(() => {
  if (!diagnostico.value?.alertas || !Array.isArray(diagnostico.value.alertas)) return []
  return diagnostico.value.alertas.filter(a => a && typeof a === 'object')
})

// Função para fallback de valor
function safeValue(val, fallback = 'N/A') {
  if (val === null || val === undefined || val === '' || (Array.isArray(val) && val.length === 0)) return fallback
  return val
}

// Gráficos dinâmicos com proteção robusta contra dados nulos
const barOptions = computed(() => {
  const hasData = diagnostico.value?.metricas && Array.isArray(diagnostico.value.metricas) && diagnostico.value.metricas.length > 0
  
  return {
    chart: { id: 'apm-bar', toolbar: { show: false } },
    xaxis: { 
      categories: hasData ? 
        diagnostico.value.metricas.map(m => (m && m.entidade) ? m.entidade.substring(0, 20) : 'N/A') : 
        ['Sem dados']
    },
    title: { text: 'Tempo Máximo (s)', align: 'center', style: { fontSize: '18px' } },
    colors: ['#2563eb'],
    dataLabels: { enabled: false },
    plotOptions: {
      bar: {
        horizontal: false,
        columnWidth: '55%',
      }
    }
  }
})

const barSeries = computed(() => {
  const hasData = diagnostico.value?.metricas && Array.isArray(diagnostico.value.metricas) && diagnostico.value.metricas.length > 0
  
  return [{
    name: 'Tempo Máximo (s)',
    data: hasData ? 
      diagnostico.value.metricas.map(m => {
        if (!m || m.valor === null || m.valor === undefined) return 0
        return typeof m.valor === 'number' && !isNaN(m.valor) ? Math.max(0, m.valor) : 0
      }) :
      [0]
  }]
})

const lineOptions = computed(() => {
  const hasData = diagnostico.value?.metricas && Array.isArray(diagnostico.value.metricas) && diagnostico.value.metricas.length > 0
  
  return {
    chart: { id: 'latency-line', toolbar: { show: false } },
    xaxis: { 
      categories: hasData ? 
        diagnostico.value.metricas.map(m => (m && m.entidade) ? m.entidade.substring(0, 20) : 'N/A') : 
        ['Sem dados']
    },
    title: { text: 'Latência', align: 'center', style: { fontSize: '18px' } },
    colors: ['#f59e42'],
    dataLabels: { enabled: false },
    stroke: {
      curve: 'smooth',
      width: 2
    }
  }
})

const lineSeries = computed(() => {
  const hasData = diagnostico.value?.metricas && Array.isArray(diagnostico.value.metricas) && diagnostico.value.metricas.length > 0
  
  return [{
    name: 'Latência (ms)',
    data: hasData ? 
      diagnostico.value.metricas.map(m => {
        if (!m || !m.nome || m.valor === null || m.valor === undefined) return 0
        
        if (m.nome === 'response_time_max' && typeof m.valor === 'number' && !isNaN(m.valor)) {
          return Math.max(0, m.valor * 1000) // Convert to ms
        }
        
        // Fallback para outras métricas de tempo
        if (typeof m.valor === 'number' && !isNaN(m.valor) && m.nome.includes('time')) {
          return Math.max(0, m.valor)
        }
        
        return 0
      }) :
      [0]
  }]
})
onMounted(async () => {
  carregando.value = true
  
  try {
    // Carrega dados do diagnóstico - usa endpoint correto
    console.log('Carregando diagnóstico...')
    const res = await axios.get('/api/diagnostico', { timeout: 30000 })
    
    if (res && res.data && typeof res.data === 'object') {
      diagnostico.value = res.data
      console.log('Diagnóstico carregado:', diagnostico.value)
    } else {
      console.warn('Resposta do diagnóstico inválida:', res)
      diagnostico.value = null
    }
    
    // Carrega status de saúde do sistema
    try {
      console.log('Carregando status de saúde...')
      const healthRes = await axios.get('/api/health', { timeout: 10000 })
      
      if (healthRes && healthRes.data && typeof healthRes.data === 'object') {
        systemHealth.value = healthRes.data
        console.log('Status de saúde carregado:', systemHealth.value)
      } else {
        console.warn('Resposta de saúde inválida:', healthRes)
        systemHealth.value = { fallback_mode: true, status: 'unknown' }
      }
    } catch (healthError) {
      console.warn('Erro ao carregar status de saúde:', healthError)
      systemHealth.value = { fallback_mode: true, status: 'unknown' }
    }
  } catch (error) {
    console.error('Erro ao carregar diagnóstico:', error)
    diagnostico.value = null
    
    // Tenta carregar pelo menos o health check
    try {
      const healthRes = await axios.get('/api/health', { timeout: 10000 })
      systemHealth.value = healthRes.data
    } catch (healthError) {
      console.warn('Erro ao carregar health após falha principal:', healthError)
      systemHealth.value = { fallback_mode: true, status: 'error' }
    }
  } finally {
    carregando.value = false
    console.log('Carregamento finalizado')
  }
})

async function handleChat({ pergunta }) {
  if (!pergunta || typeof pergunta !== 'string') {
    chatResposta.value = 'Erro: Pergunta inválida.'
    return
  }
  chatResposta.value = ''
  try {
    const data = await getChatResposta(pergunta)
    if (data && !data.erro) {
      chatResposta.value = data.resposta || 'Resposta vazia da IA.'
    } else {
      chatResposta.value = data?.mensagem || 'Erro: Resposta inválida da IA.'
    }
  } catch (error) {
    console.error('Erro no chat:', error)
    let mensagemErro = 'Erro ao processar a pergunta.'
    if (error?.mensagem) {
      mensagemErro = error.mensagem
    } else if (error?.message) {
      mensagemErro = error.message
    }
    chatResposta.value = mensagemErro
  }
}

async function fetchDashboard() {
  erroDashboard.value = false
  mensagemErroDashboard.value = ''
  try {
    const resumo = await getResumoGeral()
    if (resumo && resumo.erro) {
      erroDashboard.value = true
      mensagemErroDashboard.value = resumo.mensagem || 'Nenhum dado real disponível para o dashboard.'
    } else {
      diagnostico.value = resumo
    }
  } catch (e) {
    erroDashboard.value = true
    mensagemErroDashboard.value = 'Erro ao acessar o backend.'
  }
}
</script>

<script>
export default {
  components: {
    apexchart: VueApexCharts,
    SafeApexChart
  }
}
</script>

<style scoped>
/* Adicione efeitos de hover e responsividade extra se desejar */
</style>