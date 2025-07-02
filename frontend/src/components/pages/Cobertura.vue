<template>
  <div class="py-8">
    <div v-if="erroCobertura" class="flex flex-col items-center justify-center h-96">
      <font-awesome-icon icon="exclamation-triangle" class="text-yellow-400 text-3xl mb-2" />
      <span class="text-yellow-300 text-lg">{{ mensagemErroCobertura || 'Erro ao carregar dados de cobertura.' }}</span>
      <button @click="fetchCobertura" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Tentar novamente</button>
    </div>
    <div v-else>
      <!-- Resumo Executivo de Cobertura -->
      <div class="bg-gradient-to-r from-indigo-900 to-indigo-800 rounded-xl p-6 mb-6 shadow-xl border border-indigo-700">
        <div class="flex items-center gap-4 mb-3">
          <div class="p-3 rounded-full bg-indigo-700">
            <font-awesome-icon icon="shield-alt" class="text-white text-xl" />
          </div>
          <h3 class="text-xl font-bold text-white">Resumo de Cobertura</h3>
        </div>
        
        <div class="text-white text-opacity-90 mb-4">
          <p>{{ getCoberturaExecutiveSummary() }}</p>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mt-5 pt-4 border-t border-indigo-700">
          <div>
            <div class="text-xs text-indigo-300">Entidades Totais</div>
            <div class="text-2xl font-bold text-white">{{ getTotalEntidades() }}</div>
          </div>
          <div>
            <div class="text-xs text-indigo-300">Com Monitoramento</div>
            <div class="text-2xl font-bold text-green-400">{{ getEntidadesMonitoradas() }}</div>
          </div>
          <div>
            <div class="text-xs text-indigo-300">Cobertura Atual</div>
            <div class="text-2xl font-bold text-white">{{ data.coberturaGeral }}%</div>
          </div>
          <div>
            <div class="text-xs text-indigo-300">Tendência</div>
            <div class="text-2xl font-bold" :class="data.coberturaGeralTrend > 0 ? 'text-green-400' : 'text-red-400'">
              {{ data.coberturaGeralTrend > 0 ? '+' : '' }}{{ data.coberturaGeralTrend || 0 }}%
            </div>
          </div>
        </div>
      </div>

      <!-- Cards de cobertura por domínio do New Relic -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        <div class="rounded-xl shadow-lg p-6 bg-gradient-to-br from-gray-900 to-gray-800 text-white border border-green-900/50 transform transition-all hover:scale-[1.02] hover:shadow-2xl">
          <div class="flex items-center mb-4">
            <div class="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center mr-3">
              <font-awesome-icon icon="tachometer-alt" class="text-green-400"/>
            </div>
            <h3 class="text-lg font-semibold">Cobertura Geral</h3>
          </div>
          <div class="flex justify-between items-center">
            <div class="text-4xl font-bold">{{ data.coberturaGeral }}%</div>
            <div class="text-sm bg-green-900/40 text-green-400 px-2 py-1 rounded-lg">
              <font-awesome-icon icon="arrow-up" class="mr-1" v-if="data.coberturaGeralTrend > 0"/>
              <font-awesome-icon icon="arrow-down" class="mr-1" v-else/>
              {{ data.coberturaGeralTrend || 0 }}% últimos 30d
            </div>
          </div>
          <div class="mt-3 bg-gray-700/50 h-3 rounded-full overflow-hidden">
            <div class="bg-gradient-to-r from-green-600 to-green-400 h-full" :style="`width: ${data.coberturaGeral}%`"></div>
          </div>
        </div>
        <div class="rounded-xl shadow-lg p-6 bg-gradient-to-br from-gray-900 to-gray-800 text-white border border-blue-900/50 transform transition-all hover:scale-[1.02] hover:shadow-2xl">
          <div class="flex items-center mb-4">
            <div class="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center mr-3">
              <font-awesome-icon icon="server" class="text-blue-400"/>
            </div>
            <h3 class="text-lg font-semibold">APM</h3>
          </div>
          <div class="flex justify-between items-center">
            <div class="text-4xl font-bold">{{ getCoberturaPorDominio('APM') }}%</div>
            <div class="text-sm bg-blue-900/40 text-blue-400 px-2 py-1 rounded-lg">
              {{ getEntidadesPorDominio('APM') }} entidades
            </div>
          </div>
          <div class="mt-3 bg-gray-700/50 h-3 rounded-full overflow-hidden">
            <div class="bg-gradient-to-r from-blue-600 to-blue-400 h-full" :style="`width: ${getCoberturaPorDominio('APM')}%`"></div>
          </div>
          <div class="text-xs text-gray-400 mt-3">
            Aplicações e serviços
          </div>
        </div>
        
        <div class="rounded-xl shadow-lg p-6 bg-gradient-to-br from-gray-900 to-gray-800 text-white border border-purple-900/50 transform transition-all hover:scale-[1.02] hover:shadow-2xl">
          <div class="flex items-center mb-4">
            <div class="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center mr-3">
              <font-awesome-icon icon="globe" class="text-purple-400"/>
            </div>
            <h3 class="text-lg font-semibold">Browser</h3>
          </div>
          <div class="flex justify-between items-center">
            <div class="text-4xl font-bold">{{ getCoberturaPorDominio('BROWSER') }}%</div>
            <div class="text-sm bg-purple-900/40 text-purple-400 px-2 py-1 rounded-lg">
              {{ getEntidadesPorDominio('BROWSER') }} entidades
            </div>
          </div>
          <div class="mt-3 bg-gray-700/50 h-3 rounded-full overflow-hidden">
            <div class="bg-gradient-to-r from-purple-600 to-purple-400 h-full" :style="`width: ${getCoberturaPorDominio('BROWSER')}%`"></div>
          </div>
          <div class="text-xs text-gray-400 mt-3">
            Frontend e experiência do usuário
          </div>
        </div>
        
        <div class="rounded-xl shadow-lg p-6 bg-gradient-to-br from-gray-900 to-gray-800 text-white border border-amber-900/50 transform transition-all hover:scale-[1.02] hover:shadow-2xl">
          <div class="flex items-center mb-4">
            <div class="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center mr-3">
              <font-awesome-icon icon="hdd" class="text-amber-400"/>
            </div>
            <h3 class="text-lg font-semibold">Infraestrutura</h3>
          </div>
          <div class="flex justify-between items-center">
            <div class="text-4xl font-bold">{{ getCoberturaPorDominio('INFRA') }}%</div>
            <div class="text-sm bg-amber-900/40 text-amber-400 px-2 py-1 rounded-lg">
              {{ getEntidadesPorDominio('INFRA') }} entidades
            </div>
          </div>
          <div class="mt-3 bg-gray-700/50 h-3 rounded-full overflow-hidden">
            <div class="bg-gradient-to-r from-amber-600 to-amber-400 h-full" :style="`width: ${getCoberturaPorDominio('INFRA')}%`"></div>
          </div>
          <div class="text-xs text-gray-400 mt-3">
            Servidores e recursos computacionais
          </div>
        </div>
      </div>

      <!-- Métricas por Domínio -->
      <div class="rounded-xl shadow-lg p-6 mb-8 bg-gradient-to-br from-gray-900 to-gray-800 text-white border border-gray-700">
        <div class="flex items-center mb-6">
          <div class="p-2 rounded-full bg-blue-700 mr-3">
            <font-awesome-icon icon="chart-bar" class="text-white" />
          </div>
          <h3 class="text-xl font-semibold">Métricas por Domínio</h3>
          <div class="ml-auto">
            <button class="bg-gray-800 hover:bg-gray-700 rounded-lg px-3 py-1 text-sm flex items-center">
              <font-awesome-icon icon="filter" class="text-blue-400 mr-2" />
              Filtrar
            </button>
          </div>
        </div>
        <DomainMetrics :entities="todosRecursos" :loading="loading" />
      </div>

      <!-- Distribuição de recursos -->
      <div class="rounded-xl shadow-lg p-6 mb-8 bg-gradient-to-br from-gray-900 to-gray-800 text-white border border-gray-700">
        <div class="flex items-center mb-6">
          <div class="p-2 rounded-full bg-purple-700 mr-3">
            <font-awesome-icon icon="chart-pie" class="text-white" />
          </div>
          <h3 class="text-xl font-semibold">Distribuição de Recursos Monitorados</h3>
          <div class="ml-auto">
            <span class="text-sm text-gray-400">Última atualização: {{ new Date().toLocaleDateString() }}</span>
          </div>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="flex items-center justify-center">
            <SafeApexChart 
              type="pie" 
              height="300" 
              :options="chartOptions" 
              :series="chartSeries"
              noDataMessage="Nenhum dado de distribuição disponível"
              noDataIcon="pie-chart" />
          </div>
          <SafeDataDisplay :data="dominiosDisponiveis" noDataMessage="Nenhum domínio disponível" noDataIcon="cubes">
            <div class="flex flex-col justify-center bg-gray-800/50 rounded-xl p-5">
              <h4 class="text-lg font-medium mb-4">Detalhes por Domínio</h4>
              <div v-for="domain in dominiosDisponiveis" :key="domain" class="flex items-center mb-4">
                <div :class="`w-4 h-4 rounded-full mr-3 ${getDomainColor(domain)}`"></div>
                <div class="text-base font-medium">{{ getDomainLabel(domain) }}</div>
                <div class="ml-auto text-xl font-semibold">{{ getEntidadesPorDominio(domain) }}</div>
              </div>
              <div class="mt-5 pt-4 border-t border-gray-700 flex justify-between items-center">
                <span class="text-gray-300">Total de recursos:</span>
                <span class="text-xl font-bold">{{ data.totalRecursos || 0 }}</span>
              </div>
            </div>
          </SafeDataDisplay>
        </div>
      </div>

      <!-- Recursos sem cobertura -->
      <div class="rounded-xl shadow-lg p-6 mb-8 bg-gradient-to-br from-gray-900 to-gray-800 text-white border border-red-900/30">
        <div class="flex items-center mb-6">
          <div class="p-2 rounded-full bg-red-700/60 mr-3">
            <font-awesome-icon icon="exclamation-triangle" class="text-yellow-300" />
          </div>
          <h3 class="text-xl font-semibold">Recursos Sem Cobertura</h3>
          <div class="ml-auto flex items-center">
            <div class="bg-red-900/30 text-red-300 px-3 py-1 rounded-lg mr-3">
              {{ getRecursosSemCobertura().length }} recursos
            </div>
            <button class="bg-gray-800 hover:bg-gray-700 rounded-lg px-3 py-1 text-sm flex items-center">
              <font-awesome-icon icon="eye" class="mr-2" />
              Ver todos
            </button>
          </div>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="text-left text-sm text-gray-400">
                <th class="pb-4">Nome do Recurso</th>
                <th class="pb-4">Domínio</th>
                <th class="pb-4">Tipo</th>
                <th class="pb-4">Status</th>
                <th class="pb-4">Ação</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-800">
              <tr v-for="(recurso, index) in recursosSemCobertura || []" :key="index" class="hover:bg-gray-800/40 transition-colors">
                <td class="py-3 font-medium">
                  <div class="flex items-center">
                    <div class="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center mr-2">
                      <font-awesome-icon :icon="getIconForResourceType(recurso.type)" class="text-gray-400" />
                    </div>
                    {{ recurso.name || 'Sem nome' }}
                  </div>
                </td>
                <td class="py-3">
                  <span :class="`px-2 py-1 rounded-lg text-xs ${getDomainBadgeClass(recurso.domain)}`">
                    {{ getDomainLabel(recurso.domain) }}
                  </span>
                </td>
                <td class="py-3">{{ formatResourceType(recurso.type) || 'Desconhecido' }}</td>
                <td class="py-3">
                  <span class="px-2 py-1 rounded-lg text-xs bg-red-900/40 text-red-300 border border-red-800/30">
                    <font-awesome-icon icon="exclamation-circle" class="mr-1" />
                    Sem métricas
                  </span>
                </td>
                <td class="py-3">
                  <button class="bg-blue-900/30 hover:bg-blue-800/50 text-blue-400 hover:text-blue-300 px-3 py-1 rounded-lg text-sm transition-colors">
                    <font-awesome-icon icon="wrench" class="mr-1" />
                    Configurar
                  </button>
                </td>
              </tr>
              <tr v-if="(recursosSemCobertura || []).length === 0">
                <td colspan="5" class="py-8 text-center">
                  <div class="flex flex-col items-center">
                    <font-awesome-icon icon="check-circle" class="text-green-400 text-3xl mb-2" />
                    <span class="text-green-300">Todos os recursos estão com métricas configuradas!</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Ações recomendadas -->
      <div class="rounded-xl shadow-lg p-6 bg-gradient-to-br from-indigo-900/30 to-gray-900 text-white border border-indigo-800/30">
        <div class="flex items-center mb-6">
          <div class="p-2 rounded-full bg-indigo-700/60 mr-3">
            <font-awesome-icon icon="lightbulb" class="text-yellow-300" />
          </div>
          <h3 class="text-xl font-semibold">Ações Recomendadas</h3>
          <div class="ml-auto">
            <span class="text-xs px-2 py-1 bg-indigo-900/40 text-indigo-300 rounded-lg">Prioridade Alta</span>
          </div>
        </div>
        <div class="space-y-4">
          <div v-for="(acao, index) in acoesRecomendadas || []" :key="index" 
               class="p-5 rounded-xl bg-gradient-to-r from-gray-800 to-gray-900 border border-indigo-800/20 hover:border-indigo-700/40 transition-all shadow-lg hover:shadow-xl">
            <div class="flex items-start">
              <div class="mr-4 flex-shrink-0">
                <div class="w-12 h-12 bg-indigo-900/50 rounded-xl flex items-center justify-center shadow-inner">
                  <font-awesome-icon icon="check-circle" class="text-2xl text-indigo-300" />
                </div>
              </div>
              <div class="flex-grow">
                <div class="flex items-center mb-2">
                  <h4 class="font-semibold text-lg">{{ acao.titulo }}</h4>
                  <div class="ml-auto">
                    <span class="text-xs px-2 py-1 bg-blue-900/30 text-blue-300 rounded-lg">{{ acao.impacto || 'Médio' }}</span>
                  </div>
                </div>
                <p class="text-gray-300 mb-4">{{ acao.descricao }}</p>
                <div class="flex items-center">
                  <button class="px-4 py-2 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-sm transition-all shadow">
                    <font-awesome-icon icon="play" class="mr-2" />
                    Executar
                  </button>
                  <button class="ml-3 px-3 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 hover:text-white transition-colors">
                    Detalhes
                  </button>
                </div>
              </div>
            </div>
          </div>
          <div v-if="(acoesRecomendadas || []).length === 0" class="text-center py-10">
            <font-awesome-icon icon="check-circle" class="text-green-400 text-4xl mb-3" />
            <p class="text-lg">Não há ações recomendadas no momento.</p>
            <p class="text-sm text-gray-400 mt-1">A cobertura atual está em bom estado.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { getCobertura, getEntidades } from '../../api/backend.js'
import DomainMetrics from '../DomainMetrics.vue'
import SafeApexChart from '../SafeApexChart.vue'
import SafeDataDisplay from '../SafeDataDisplay.vue'
import { createSafeApexSeries, createSafeApexOptions } from '../../utils/nullDataHandler.js'

const data = ref({})
const loading = ref(true)
const error = ref(false)
const todosRecursos = ref([])
const recursosSemCobertura = ref([])
const acoesRecomendadas = ref([]) // Inicializa como array vazio
const erroCobertura = ref(false)
const mensagemErroCobertura = ref('')

// Obtém ícone específico para cada tipo de recurso
const getIconForResourceType = (type) => {
  const icons = {
    'APPLICATION': 'cube',
    'HOST': 'server',
    'SERVICE': 'cogs',
    'CONTAINER': 'box',
    'BROWSER': 'globe',
    'MOBILE': 'mobile-alt',
    'DATABASE': 'database'
  }
  return icons[type] || 'question-circle'
}

// Formata o tipo de recurso para exibição
const formatResourceType = (type) => {
  if (!type) return 'Desconhecido'
  
  // Converte snake_case ou SCREAMING_SNAKE para Title Case
  return type.toLowerCase()
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

// Retorna a classe CSS para o badge do domínio
const getDomainBadgeClass = (domain) => {
  const classes = {
    'APM': 'bg-blue-900/40 text-blue-300 border border-blue-800/30',
    'BROWSER': 'bg-purple-900/40 text-purple-300 border border-purple-800/30', 
    'INFRA': 'bg-amber-900/40 text-amber-300 border border-amber-800/30',
    'MOBILE': 'bg-green-900/40 text-green-300 border border-green-800/30',
    'SYNTH': 'bg-indigo-900/40 text-indigo-300 border border-indigo-800/30'
  }
  return classes[domain] || 'bg-gray-800 text-gray-300'
}

// Retorna o resumo executivo da cobertura em linguagem natural
const getCoberturaExecutiveSummary = () => {
  if (loading.value) return 'Carregando dados de cobertura...'
  
  const cobertura = data.value.coberturaGeral || 0
  const trend = data.value.coberturaGeralTrend || 0
  const semCobertura = getRecursosSemCobertura().length
  const totalRecursos = data.value.totalRecursos || 0
  
  if (cobertura >= 90) {
    return `Excelente nível de cobertura: ${cobertura}% dos recursos estão sendo monitorados adequadamente. ${trend > 0 ? `Houve um aumento de ${trend}% em relação ao mês anterior.` : ''} Apenas ${semCobertura} de ${totalRecursos} recursos estão sem métricas configuradas.`
  } else if (cobertura >= 70) {
    return `Boa cobertura: ${cobertura}% dos recursos estão sendo monitorados adequadamente. ${trend > 0 ? `Houve um aumento de ${trend}% em relação ao mês anterior.` : ''} Existem ${semCobertura} recursos que precisam de configuração de monitoramento.`
  } else {
    return `Atenção: A cobertura de monitoramento está em ${cobertura}%, abaixo do recomendado. ${semCobertura} recursos não estão sendo monitorados adequadamente. Recomendamos configurar métricas para os recursos listados abaixo.`
  }
}

// Retorna o total de entidades
const getTotalEntidades = () => {
  return data.value.totalRecursos || 0
}

// Retorna o número de entidades monitoradas
const getEntidadesMonitoradas = () => {
  const total = getTotalEntidades()
  const semCobertura = getRecursosSemCobertura().length
  return total - semCobertura
}

// Retorna recursos sem cobertura
const getRecursosSemCobertura = () => {
  return recursosSemCobertura.value || []
}

const domainColors = {
  'APM': 'bg-green-500',
  'BROWSER': 'bg-blue-500',
  'INFRA': 'bg-yellow-500',
  'DB': 'bg-purple-500',
  'MOBILE': 'bg-red-500',
  'IOT': 'bg-indigo-500',
  'SERVERLESS': 'bg-pink-500',
  'EXT': 'bg-gray-500',
  'SYNTH': 'bg-teal-500'
}

const chartOptions = {
  chart: {
    type: 'pie',
    foreColor: '#cbd5e0',
  },
  labels: [],
  theme: {
    mode: 'dark'
  },
  legend: {
    position: 'bottom'
  },
  colors: [],
  responsive: [{
    breakpoint: 480,
    options: {
      chart: {
        width: 200
      },
      legend: {
        position: 'bottom'
      }
    }
  }]
}
const chartSeries = ref([])
const dominiosDisponiveis = computed(() => {
  const domains = new Set()
  todosRecursos.value.forEach(entity => {
    if (entity.domain) {
      domains.add(entity.domain)
    }
  })
  return Array.from(domains)
})

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

const getDomainColor = (domain) => {
  return domainColors[domain] || 'bg-gray-500'
}

const getEntidadesPorDominio = (domain) => {
  return todosRecursos.value.filter(entidade => entidade.domain === domain).length
}

const getCoberturaPorDominio = (domain) => {
  const entidades = todosRecursos.value.filter(entidade => entidade.domain === domain)
  if (entidades.length === 0) return 0
  const comMetricas = entidades.filter(entidade => 
    entidade.metricas && Object.keys(entidade.metricas).length > 0
  )
  return Math.round((comMetricas.length / entidades.length) * 100)
}

const fetchData = async () => {
  loading.value = true
  error.value = false
  try {
    const [coberturaResponse, entidadesResponse] = await Promise.all([
      getCobertura(),
      getEntidades()
    ])
    data.value = coberturaResponse.data || {
      coberturaGeral: 0,
      coberturaGeralTrend: 0,
      totalRecursos: 0,
      acoesRecomendadas: []
    }
    todosRecursos.value = entidadesResponse.data?.entidades || []
    recursosSemCobertura.value = todosRecursos.value.filter(entidade => 
      !entidade.metricas || Object.keys(entidade.metricas).length === 0
    )
    acoesRecomendadas.value = coberturaResponse.data?.acoesRecomendadas || []
    updateChartData()
  } catch (e) {
    console.error("Erro ao carregar dados de cobertura:", e)
    error.value = true
    data.value = {
      coberturaGeral: 0,
      coberturaGeralTrend: 0,
      totalRecursos: 0,
      acoesRecomendadas: []
    }
    todosRecursos.value = []
    recursosSemCobertura.value = []
    acoesRecomendadas.value = []
  } finally {
    loading.value = false
  }
}

const fetchCobertura = async () => {
  erroCobertura.value = false
  mensagemErroCobertura.value = ''
  try {
    const cobertura = await getCobertura()
    if (cobertura && cobertura.erro) {
      erroCobertura.value = true
      mensagemErroCobertura.value = cobertura.mensagem || 'Nenhum dado real de cobertura disponível.'
    } else {
      data.value = cobertura
    }
  } catch (e) {
    erroCobertura.value = true
    mensagemErroCobertura.value = 'Erro ao acessar o backend.'
  }
}

const updateChartData = () => {
  const labels = []
  const series = []
  const colors = []
  
  if (dominiosDisponiveis.value.length === 0) {
    chartSeries.value = [1] // Dados de fallback para exibição
    chartOptions.labels = ['Sem domínios disponíveis']
    chartOptions.colors = ['#666666']
    return
  }
  
  dominiosDisponiveis.value.forEach(domain => {
    const count = getEntidadesPorDominio(domain)
    if (count > 0) {
      labels.push(getDomainLabel(domain))
      series.push(count)
      // Extrai a cor correta do estilo CSS
      let color = domainColors[domain] || 'bg-gray-500'
      // Converte bg-blue-500 para #3b82f6 (exemplo)
      const colorMap = {
        'green': '#10b981',
        'blue': '#3b82f6',
        'yellow': '#f59e0b',
        'red': '#ef4444',
        'purple': '#8b5cf6',
        'indigo': '#6366f1',
        'pink': '#ec4899',
        'teal': '#14b8a6',
        'gray': '#6b7280'
      }
      
      const colorName = color.replace('bg-', '').split('-')[0]
      colors.push(colorMap[colorName] || '#6b7280')
    }
  })
  
  if (series.length === 0) {
    // Fallback para quando não há dados
    chartSeries.value = [1]
    chartOptions.labels = ['Sem dados']
    chartOptions.colors = ['#6b7280']
  } else {
    chartOptions.labels = labels
    chartOptions.colors = colors
    chartSeries.value = series
  }
}
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
</style>
