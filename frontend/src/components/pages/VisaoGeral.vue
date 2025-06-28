<template>
  <div class="py-8">
    <!-- Removido botão Atualizar para evitar consumo de tokens -->
    <div class="flex justify-end items-center mb-4">
      <span class="text-sm text-gray-400">Última atualização: {{ ultimaAtualizacao }}</span>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div class="rounded-xl shadow-lg p-6 flex flex-col items-center border-l-8 border-green-500 bg-gradient-to-br from-gray-900 to-gray-800 text-white transform transition-all hover:scale-[1.02] hover:shadow-2xl">
        <div class="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mb-3">
          <font-awesome-icon icon="circle" class="text-3xl text-green-400"/>
        </div>
        <span class="text-2xl font-bold mb-1">Status Geral</span>
        <span class="text-4xl font-extrabold text-green-400">{{ statusGeral.status }}</span>
        <span class="mt-3 text-gray-300 text-center">{{ statusGeral.descricao }}</span>
        <div class="mt-4 pt-3 border-t border-gray-700 w-full">
          <div class="text-sm flex justify-between">
            <span>Disponibilidade:</span>
            <span class="font-bold text-green-400">{{ statusGeral.disponibilidade || '99.9' }}%</span>
          </div>
        </div>
      </div>
      
      <div class="rounded-xl shadow-lg p-6 flex flex-col items-center border-l-8 border-yellow-500 bg-gradient-to-br from-gray-900 to-gray-800 text-white transform transition-all hover:scale-[1.02] hover:shadow-2xl">
        <div class="w-16 h-16 rounded-full bg-yellow-500/20 flex items-center justify-center mb-3">
          <font-awesome-icon icon="exclamation-triangle" class="text-3xl text-yellow-300"/>
        </div>
        <span class="text-2xl font-bold mb-1">Alertas</span>
        <span class="text-4xl font-extrabold text-yellow-300">{{ statusGeral.alertas }}</span>
        <span class="mt-3 text-gray-300 text-center">{{ statusGeral.alertasDescricao }}</span>
        <div class="mt-4 pt-3 border-t border-gray-700 w-full">
          <div class="text-sm flex justify-between">
            <span>Última atualização:</span>
            <span class="font-mono">{{ statusGeral.ultimoAlertaEm || 'Hoje 10:45' }}</span>
          </div>
        </div>
      </div>
      
      <div class="rounded-xl shadow-lg p-6 flex flex-col items-center border-l-8 border-red-500 bg-gradient-to-br from-gray-900 to-gray-800 text-white transform transition-all hover:scale-[1.02] hover:shadow-2xl">
        <div class="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mb-3">
          <font-awesome-icon icon="times-circle" class="text-3xl text-red-400"/>
        </div>
        <span class="text-2xl font-bold mb-1">Erros Críticos</span>
        <span class="text-4xl font-extrabold text-red-400">{{ statusGeral.errosCriticos }}</span>
        <span class="mt-3 text-gray-300 text-center">{{ statusGeral.errosDescricao }}</span>
        <div class="mt-4 pt-3 border-t border-gray-700 w-full">
          <div class="text-sm flex justify-between">
            <span>Serviços afetados:</span>
            <span class="font-bold">{{ statusGeral.servicosAfetados || 0 }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Domain Cards -->
    <div class="mb-8">
      <h3 class="text-xl font-bold text-white mb-4">Status por Domínio</h3>

      <!-- Resumo Executivo -->
      <div class="bg-gradient-to-r from-blue-900 to-blue-800 rounded-xl p-6 mb-6 shadow-xl border border-blue-700">
        <div class="flex items-center gap-4 mb-3">
          <div class="p-3 rounded-full bg-blue-700">
            <font-awesome-icon icon="chart-pie" class="text-white text-xl" />
          </div>
          <h3 class="text-xl font-bold text-white">Resumo Executivo</h3>
        </div>
        
        <div class="text-white text-opacity-90">
          <p>{{ getExecutiveSummary() }}</p>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4 pt-4 border-t border-blue-700">
            <div>
              <div class="text-xs text-blue-300">Entidades Monitoradas</div>
              <div class="text-2xl font-bold">{{ getTotalEntities() }}</div>
            </div>
            <div>
              <div class="text-xs text-blue-300">Alertas Ativos</div>
              <div class="text-2xl font-bold">{{ getTotalAlerts() }}</div>
            </div>
            <div>
              <div class="text-xs text-blue-300">Saúde Geral</div>
              <div class="text-2xl font-bold">{{ getOverallHealth() }}%</div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4">
        <div v-for="(data, domain) in statusGeral.dominios" :key="domain" 
             class="rounded-xl shadow-lg p-5 bg-gradient-to-br from-gray-800 to-gray-900 text-white border-l-4 transform transition-all hover:scale-[1.02] hover:shadow-xl"
             :class="getDomainBorderClass(data)">
          <div class="flex justify-between items-center mb-3">
            <div class="flex items-center">
              <div class="w-8 h-8 rounded-full flex items-center justify-center mr-2"
                   :class="getDomainIconClass(data)">
                <font-awesome-icon :icon="getDomainIcon(domain)" />
              </div>
              <span class="font-bold text-lg">{{ getDomainLabel(domain) }}</span>
            </div>
            <span class="text-sm rounded-full px-3 py-1 font-medium" 
                  :class="getDomainStatusClass(data)">{{ data.status }}</span>
          </div>
          
          <div class="my-4">
            <div class="w-full bg-gray-700 rounded-full h-2 mb-4">
              <div class="h-2 rounded-full" 
                   :style="{width: getDomainHealthPercentage(data) + '%'}"
                   :class="getDomainHealthClass(data)"></div>
            </div>
          </div>
          
          <div class="grid grid-cols-3 gap-1 text-center mt-4 pt-3 border-t border-gray-700">
            <div>
              <div class="text-xs text-gray-400">Entidades</div>
              <div class="font-bold">{{ data.count }}</div>
            </div>
            <div>
              <div class="text-xs text-gray-400">Alertas</div>
              <div class="font-bold" :class="{'text-yellow-300': data.alertas > 0}">{{ data.alertas }}</div>
            </div>
            <div>
              <div class="text-xs text-gray-400">Erros</div>
              <div class="font-bold" :class="{'text-red-400': data.erros > 0}">{{ data.erros }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
      <div class="rounded-xl shadow-lg p-6 bg-gray-800">
        <SafeApexChart 
          type="bar" 
          height="300" 
          :options="barOptions" 
          :series="barSeries" 
          noDataMessage="Nenhum dado de incidentes disponível"
          noDataIcon="exclamation-triangle" />
      </div>
      <div class="rounded-xl shadow-lg p-6 bg-gray-800">
        <SafeApexChart 
          type="line" 
          height="300" 
          :options="lineOptions" 
          :series="lineSeries" 
          noDataMessage="Nenhum dado de latência disponível"
          noDataIcon="clock" />
      </div>
    </div>
    <SafeDataDisplay 
      :data="statusGeral.diagnostico" 
      noDataMessage="Diagnóstico não disponível"
      noDataIcon="brain">
      <div class="rounded-xl shadow-lg p-8 mt-8 border-l-8 border-blue-600 bg-gray-900 text-white">
        <h2 class="text-2xl font-bold text-blue-300 mb-4">Diagnóstico da IA</h2>
        <p class="text-lg leading-relaxed">
          <span class="font-semibold text-blue-200">Causa Raiz:</span> {{ statusGeral.diagnostico }}
        </p>
        <ul class="mt-4 list-disc list-inside text-gray-300">
          <li v-for="item in statusGeral.recomendacoes || []" :key="item">{{ item }}</li>
        </ul>
      </div>
    </SafeDataDisplay>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { getStatus } from '../../api/backend.js'
import SafeApexChart from '../SafeApexChart.vue'
import SafeDataDisplay from '../SafeDataDisplay.vue'
import { createSafeApexSeries, createSafeApexOptions } from '../../utils/nullDataHandler.js'

const statusGeral = ref({
  status: '',
  descricao: '',
  alertas: 0,
  alertasDescricao: '',
  errosCriticos: 0,
  errosDescricao: '',
  diagnostico: '',
  recomendacoes: [],
  dominios: {}
})
const barOptions = { 
  chart: { toolbar: { show: false } }, 
  xaxis: { categories: [] }, 
  colors: ['#60a5fa'],
  theme: { mode: 'dark' },
  title: { text: 'Incidentes por Domínio', style: { color: '#fff' } }
}
const barSeries = [{ name: 'Incidentes', data: [] }]
const lineOptions = { 
  chart: { toolbar: { show: false } }, 
  xaxis: { categories: [] }, 
  colors: ['#fbbf24'],
  theme: { mode: 'dark' },
  title: { text: 'Latência Média (ms)', style: { color: '#fff' } }
}
const lineSeries = [{ name: 'Latência (ms)', data: [] }]
const ultimaAtualizacao = ref('')

// Mapeia os domínios para nomes mais amigáveis
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

// Determina classe CSS de cor baseada no status
const getDomainBorderClass = (data) => {
  if (data.erros > 0) return 'border-red-500'
  if (data.alertas > 0) return 'border-yellow-400'
  return 'border-green-400'
}

// Determina classe CSS para o badge de status
const getDomainStatusClass = (data) => {
  if (data.erros > 0) return 'bg-red-900 text-red-300'
  if (data.alertas > 0) return 'bg-yellow-900 text-yellow-300'
  return 'bg-green-900 text-green-300'
}

// Determina o ícone para cada domínio
const getDomainIcon = (domain) => {
  const icons = {
    'APM': 'tachometer-alt',
    'BROWSER': 'globe',
    'INFRA': 'server',
    'MOBILE': 'mobile-alt',
    'SYNTH': 'robot',
    'EXT': 'plug',
    'DATABASE': 'database',
    'DASHBOARD': 'chart-line'
  }
  return icons[domain] || 'cube'
}

// Determina a classe CSS para o ícone do domínio
const getDomainIconClass = (data) => {
  if (data.erros > 0) return 'bg-red-500/20 text-red-400'
  if (data.alertas > 0) return 'bg-yellow-500/20 text-yellow-300'
  return 'bg-green-500/20 text-green-400'
}

// Calcula a porcentagem de saúde do domínio
const getDomainHealthPercentage = (data) => {
  // Fórmula simples: 100% - (% de erros + % de alertas)
  // Cada erro conta como 20%, cada alerta como 10%
  const errorImpact = Math.min(data.erros * 20, 80)
  const alertImpact = Math.min(data.alertas * 10, 60)
  return Math.max(100 - errorImpact - alertImpact, 10) // mínimo de 10% para visualização
}

// Determina a classe CSS para a barra de saúde
const getDomainHealthClass = (data) => {
  if (data.erros > 0) return 'bg-red-500'
  if (data.alertas > 0) return 'bg-yellow-400'
  return 'bg-green-400'
}

// Retorna um resumo executivo em linguagem natural
const getExecutiveSummary = () => {
  if (!statusGeral.value || !statusGeral.value.dominios) {
    return "Os dados estão sendo carregados. Por favor, aguarde um momento."
  }

  const totalDominios = Object.keys(statusGeral.value.dominios).length
  const dominiosComProblemas = Object.values(statusGeral.value.dominios).filter(d => d.erros > 0 || d.alertas > 0).length
  const totalAlertas = statusGeral.value.alertas || 0
  const totalErros = statusGeral.value.errosCriticos || 0

  if (totalErros > 0) {
    return `Atenção: O sistema apresenta ${totalErros} erros críticos que requerem ação imediata. ${totalAlertas} alertas ativos foram detectados em ${dominiosComProblemas} de ${totalDominios} domínios monitorados. Recomenda-se verificar os detalhes em Erros Críticos.`
  } else if (totalAlertas > 0) {
    return `O sistema está operando com ${totalAlertas} alertas ativos em ${dominiosComProblemas} de ${totalDominios} domínios monitorados. Não há erros críticos no momento, mas os alertas devem ser investigados para prevenir possíveis problemas.`
  } else {
    return `Todos os sistemas estão operando normalmente. Os ${totalDominios} domínios monitorados não apresentam alertas ou erros. A disponibilidade dos serviços está dentro dos níveis esperados.`
  }
}

// Calcula o total de entidades
const getTotalEntities = () => {
  if (!statusGeral.value || !statusGeral.value.dominios) return 0
  return Object.values(statusGeral.value.dominios).reduce((sum, domain) => sum + (domain.count || 0), 0)
}

// Calcula o total de alertas
const getTotalAlerts = () => {
  return statusGeral.value?.alertas || 0
}

// Calcula a saúde geral do sistema (%)
const getOverallHealth = () => {
  if (!statusGeral.value) return 99
  
  // Se há erros críticos, reduz a saúde significativamente
  if (statusGeral.value.errosCriticos > 0) {
    return Math.max(70 - statusGeral.value.errosCriticos * 10, 20)
  }
  
  // Se há apenas alertas, reduz a saúde moderadamente
  if (statusGeral.value.alertas > 0) {
    return Math.max(95 - statusGeral.value.alertas * 2, 75)
  }
  
  // Sem problemas
  return 99
}

onMounted(async () => {
  try {
    const { data } = await getStatus()
    statusGeral.value = data || {
      status: 'Desconhecido',
      descricao: 'Dados não disponíveis',
      alertas: 0,
      alertasDescricao: 'Não foi possível obter informações sobre alertas',
      errosCriticos: 0,
      errosDescricao: 'Não foi possível obter informações sobre erros',
      diagnostico: '',
      recomendacoes: [],
      dominios: {}
    }
    ultimaAtualizacao.value = new Date().toLocaleString()

    // Atualiza gráficos com dados reais
    if (data?.dominios && Object.keys(data.dominios).length > 0) {
      updateCharts(data)
    } else {
      // Dados de fallback para visualização
      fallbackChartData()
    }
  } catch (e) {
    console.error("Erro ao carregar status:", e)
    statusGeral.value = {
      status: 'Erro',
      descricao: 'Erro ao carregar dados do backend.',
      alertas: 0,
      alertasDescricao: 'Não foi possível obter informações sobre alertas',
      errosCriticos: 0,
      errosDescricao: 'Não foi possível obter informações sobre erros',
      diagnostico: 'Possível problema de conexão com o serviço backend.',
      recomendacoes: [
        'Verifique se o serviço backend está em execução',
        'Verifique a conectividade de rede',
        'Consulte os logs do sistema para mais detalhes'
      ],
      dominios: {}
    }
    fallbackChartData()
  }
})

const fallbackChartData = () => {
  // Dados de fallback para visualizar os gráficos quando não há dados
  const domains = ['APM', 'BROWSER', 'INFRA', 'DB', 'MOBILE']
  barOptions.xaxis.categories = domains.map(getDomainLabel)
  barSeries[0].data = [0, 0, 0, 0, 0]
  
  lineOptions.xaxis.categories = domains.map(getDomainLabel)
  lineSeries[0].data = [0, 0, 0, 0, 0]
}

const updateCharts = (data) => {
  if (data.dominios) {
    const domains = Object.keys(data.dominios)
    const alertCounts = domains.map(d => data.dominios[d].alertas || 0)
    const latencyData = domains.map(d => data.dominios[d].latenciaMedia || 0)

    barOptions.xaxis.categories = domains.map(getDomainLabel)
    barSeries[0].data = alertCounts

    lineOptions.xaxis.categories = domains.map(getDomainLabel)
    lineSeries[0].data = latencyData
  }
}
</script>

<style scoped>
</style>
