<template>
  <div class="py-8">
    <div v-if="erroPainel" class="bg-yellow-900 text-yellow-200 p-4 rounded mb-6 text-center">
      {{ erroPainel }}
    </div>
    <div v-else>
      <div class="mb-6">
        <h2 class="text-2xl font-bold text-white mb-4">Core Inteligente</h2>
        <p class="text-gray-300">Painel de administração do sistema de inteligência artificial e processamento cognitivo.</p>
      </div>

      <!-- Status e Métricas do Core -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div class="rounded-xl shadow-lg p-5 bg-gray-900 text-white">
          <div class="flex justify-between items-center mb-2">
            <h3 class="text-sm text-gray-400">Status</h3>
            <div :class="`w-3 h-3 rounded-full ${statusColor}`"></div>
          </div>
          <div class="text-xl font-semibold">{{ dados.value.status }}</div>
          <div class="text-sm text-gray-400 mt-1">Última verificação: {{ formatarTempo(dados.value.ultimaVerificacao) }}</div>
        </div>

        <div class="rounded-xl shadow-lg p-5 bg-gray-900 text-white">
          <h3 class="text-sm text-gray-400 mb-2">Versão</h3>
          <div class="text-xl font-semibold">{{ dados.value.versao }}</div>
          <div class="text-sm text-gray-400 mt-1">Build {{ dados.value.build }}</div>
        </div>

        <div class="rounded-xl shadow-lg p-5 bg-gray-900 text-white">
          <h3 class="text-sm text-gray-400 mb-2">Uso de CPU</h3>
          <div class="flex items-end">
            <div class="text-xl font-semibold">{{ dados.value.cpu }}%</div>
            <div :class="`ml-2 text-sm ${dados.value.cpuTendencia > 0 ? 'text-red-400' : 'text-green-400'}`">
              {{ dados.value.cpuTendencia > 0 ? '↑' : '↓' }} {{ Math.abs(dados.value.cpuTendencia) }}%
            </div>
          </div>
          <div class="w-full bg-gray-700 h-1.5 mt-2 rounded-full">
            <div class="h-full rounded-full" 
                 :class="`${dados.value.cpu > 80 ? 'bg-red-500' : dados.value.cpu > 60 ? 'bg-yellow-500' : 'bg-green-500'}`"
                 :style="`width: ${dados.value.cpu}%`"></div>
          </div>
        </div>

        <div class="rounded-xl shadow-lg p-5 bg-gray-900 text-white">
          <h3 class="text-sm text-gray-400 mb-2">Memória</h3>
          <div class="flex items-end">
            <div class="text-xl font-semibold">{{ dados.value.memoria }}%</div>
            <div :class="`ml-2 text-sm ${dados.value.memoriaTendencia > 0 ? 'text-red-400' : 'text-green-400'}`">
              {{ dados.value.memoriaTendencia > 0 ? '↑' : '↓' }} {{ Math.abs(dados.value.memoriaTendencia) }}%
            </div>
          </div>
          <div class="w-full bg-gray-700 h-1.5 mt-2 rounded-full">
            <div class="h-full rounded-full" 
                 :class="`${dados.value.memoria > 80 ? 'bg-red-500' : dados.value.memoria > 60 ? 'bg-yellow-500' : 'bg-green-500'}`"
                 :style="`width: ${dados.value.memoria}%`"></div>
          </div>
        </div>
      </div>

      <!-- Métricas de desempenho -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        <!-- Gráfico de Desempenho -->
        <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
          <h3 class="text-lg font-semibold mb-4">Desempenho do Core</h3>
          <div class="h-64">
            <apexchart
              type="line"
              height="100%"
              :options="chartOptions"
              :series="chartSeries">
            </apexchart>
          </div>
        </div>

        <!-- Processamento de Eventos -->
        <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
          <h3 class="text-lg font-semibold mb-4">Processamento de Eventos</h3>
          <div class="grid grid-cols-2 gap-4">
            <div class="p-3 bg-gray-800 rounded-lg">
              <div class="text-sm text-gray-400 mb-1">Taxa de Processamento</div>
              <div class="text-xl font-semibold">{{ dados.value.taxaProcessamento }} /s</div>
              <div :class="`text-xs ${
                dados.value.taxaProcessamentoChange > 0 ? 'text-green-400' : 
                dados.value.taxaProcessamentoChange < 0 ? 'text-red-400' : 
                'text-gray-400'
              }`">
                {{ dados.value.taxaProcessamentoChange > 0 ? '↑' : dados.value.taxaProcessamentoChange < 0 ? '↓' : '→' }}
                {{ Math.abs(dados.value.taxaProcessamentoChange) }}% vs média
              </div>
            </div>

            <div class="p-3 bg-gray-800 rounded-lg">
              <div class="text-sm text-gray-400 mb-1">Latência Média</div>
              <div class="text-xl font-semibold">{{ dados.value.latenciaMedia }}ms</div>
              <div :class="`text-xs ${
                dados.value.latenciaMediaChange < 0 ? 'text-green-400' : 
                dados.value.latenciaMediaChange > 0 ? 'text-red-400' : 
                'text-gray-400'
              }`">
                {{ dados.value.latenciaMediaChange < 0 ? '↓' : dados.value.latenciaMediaChange > 0 ? '↑' : '→' }}
                {{ Math.abs(dados.value.latenciaMediaChange) }}% vs média
              </div>
            </div>

            <div class="p-3 bg-gray-800 rounded-lg">
              <div class="text-sm text-gray-400 mb-1">Precisão</div>
              <div class="text-xl font-semibold">{{ dados.value.precisao }}%</div>
              <div :class="`text-xs ${
                dados.value.precisaoChange > 0 ? 'text-green-400' : 
                dados.value.precisaoChange < 0 ? 'text-red-400' : 
                'text-gray-400'
              }`">
                {{ dados.value.precisaoChange > 0 ? '↑' : dados.value.precisaoChange < 0 ? '↓' : '→' }}
                {{ Math.abs(dados.value.precisaoChange) }}% vs baseline
              </div>
            </div>

            <div class="p-3 bg-gray-800 rounded-lg">
              <div class="text-sm text-gray-400 mb-1">Cache Hit Rate</div>
              <div class="text-xl font-semibold">{{ dados.value.cacheHitRate }}%</div>
              <div :class="`text-xs ${
                dados.value.cacheHitRateChange > 0 ? 'text-green-400' : 
                dados.value.cacheHitRateChange < 0 ? 'text-red-400' : 
                'text-gray-400'
              }`">
                {{ dados.value.cacheHitRateChange > 0 ? '↑' : dados.value.cacheHitRateChange < 0 ? '↓' : '→' }}
                {{ Math.abs(dados.value.cacheHitRateChange) }}% vs média
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Modelos e Componentes -->
      <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white mb-8">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold">Modelos e Componentes</h3>
          <button class="px-3 py-1 bg-blue-600 text-sm rounded">Atualizar Modelos</button>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="text-left text-sm text-gray-400 border-b border-gray-700">
                <th class="pb-2 pl-4">Componente</th>
                <th class="pb-2">Versão</th>
                <th class="pb-2">Status</th>
                <th class="pb-2">Utilização</th>
                <th class="pb-2">Última Atualização</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(componente, idx) in dados.value.componentes" :key="idx" class="border-b border-gray-800">
                <td class="py-3 pl-4">
                  <div class="flex items-center">
                    <i :class="`fas ${
                      componente.tipo === 'modelo' ? 'fa-brain' : 
                      componente.tipo === 'regras' ? 'fa-cogs' : 
                      componente.tipo === 'correlacao' ? 'fa-link' : 
                      'fa-microchip'
                    } mr-3 text-blue-400`"></i>
                    <span>{{ componente.nome }}</span>
                  </div>
                </td>
                <td class="py-3">{{ componente.versao }}</td>
                <td class="py-3">
                  <span :class="`px-2 py-1 rounded text-xs ${
                    componente.status === 'Ativo' ? 'bg-green-900 text-green-200' : 
                    componente.status === 'Carregando' ? 'bg-blue-900 text-blue-200' : 
                    'bg-red-900 text-red-200'
                  }`">{{ componente.status }}</span>
                </td>
                <td class="py-3">
                  <div class="flex items-center">
                    <div class="w-24 bg-gray-700 h-1.5 rounded-full mr-2">
                      <div class="h-full rounded-full bg-blue-500" :style="`width: ${componente.utilizacao}%`"></div>
                    </div>
                    <span>{{ componente.utilizacao }}%</span>
                  </div>
                </td>
                <td class="py-3 text-sm text-gray-400">{{ formatarData(componente.ultimaAtualizacao) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Ações e Controle -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <!-- Logs do Sistema -->
        <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white md:col-span-2">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-semibold">Logs do Sistema</h3>
            <select v-model="nivelLog" class="bg-gray-800 text-gray-300 py-1 px-3 rounded-md text-sm">
              <option value="todos">Todos os níveis</option>
              <option value="info">Informações</option>
              <option value="warning">Avisos</option>
              <option value="error">Erros</option>
            </select>
          </div>
          <div class="bg-gray-800 rounded-md p-3 font-mono text-sm h-64 overflow-y-auto">
            <div v-for="(log, idx) in logsFiltrados" :key="idx" class="mb-2">
              <span :class="`mr-2 ${
                log.nivel === 'ERROR' ? 'text-red-400' : 
                log.nivel === 'WARNING' ? 'text-yellow-400' : 
                'text-blue-400'
              }`">
                [{{ log.nivel }}]
              </span>
              <span class="text-gray-400">{{ log.timestamp }} - </span>
              <span>{{ log.mensagem }}</span>
            </div>
          </div>
        </div>

        <!-- Ações Rápidas -->
        <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
          <h3 class="text-lg font-semibold mb-4">Ações Rápidas</h3>
          <div class="space-y-3">
            <button class="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 rounded flex items-center justify-center">
              <i class="fas fa-sync-alt mr-2"></i>
              Reiniciar Core
            </button>
            <button class="w-full py-2 px-4 bg-gray-800 hover:bg-gray-700 rounded flex items-center justify-center">
              <i class="fas fa-broom mr-2"></i>
              Limpar Cache
            </button>
            <button class="w-full py-2 px-4 bg-gray-800 hover:bg-gray-700 rounded flex items-center justify-center">
              <i class="fas fa-download mr-2"></i>
              Backup de Configuração
            </button>
            <button class="w-full py-2 px-4 bg-gray-800 hover:bg-gray-700 rounded flex items-center justify-center">
              <i class="fas fa-file-export mr-2"></i>
              Exportar Métricas
            </button>
            <button class="w-full py-2 px-4 bg-gray-800 hover:bg-gray-700 rounded flex items-center justify-center">
              <i class="fas fa-cogs mr-2"></i>
              Configurações Avançadas
            </button>
          </div>
        </div>
      </div>

      <!-- Tarefas Pendentes -->
      <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
        <h3 class="text-lg font-semibold mb-4">Tarefas de Manutenção Pendentes</h3>
        <div class="space-y-3">
          <div v-for="(tarefa, idx) in dados.value.tarefas" :key="idx" class="p-3 border border-gray-700 rounded-lg bg-gray-800">
            <div class="flex justify-between">
              <div class="font-medium">{{ tarefa.nome }}</div>
              <div :class="`text-xs px-2 py-0.5 rounded-full ${
                tarefa.prioridade === 'Alta' ? 'bg-red-900 text-red-200' : 
                tarefa.prioridade === 'Média' ? 'bg-yellow-900 text-yellow-200' : 
                'bg-blue-900 text-blue-200'
              }`">{{ tarefa.prioridade }}</div>
            </div>
            <div class="text-sm text-gray-400 mt-1 mb-2">{{ tarefa.descricao }}</div>
            <div class="flex justify-between items-center text-xs">
              <div>{{ formatarData(tarefa.data) }}</div>
              <button class="px-2 py-1 bg-blue-700 hover:bg-blue-600 rounded">Executar</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api/backend.js'

const nivelLog = ref('todos')
const dados = ref(null)
const erroPainel = ref(null)

onMounted(async () => {
  try {
    const response = await api.get('/core-inteligente')
    if (response && response.erro) {
      erroPainel.value = response.mensagem || 'Dados indisponíveis no momento.'
      dados.value = null
    } else {
      dados.value = response
      erroPainel.value = null
    }
  } catch (error) {
    erroPainel.value = 'Erro ao acessar dados do backend.'
    dados.value = null
  }
})

const statusColor = computed(() => {
  if (dados.value.status === 'Operacional') return 'bg-green-500'
  if (dados.value.status === 'Atenção') return 'bg-yellow-500'
  if (dados.value.status === 'Problemas Parciais') return 'bg-yellow-500'
  return 'bg-red-500'
})

const logsFiltrados = computed(() => {
  if (nivelLog.value === 'todos') return dados.value.logs
  
  const nivelParaFiltrar = nivelLog.value.toUpperCase()
  return dados.value.logs.filter(log => {
    if (nivelLog.value === 'warning') return ['WARNING', 'ERROR'].includes(log.nivel)
    return log.nivel === nivelParaFiltrar
  })
})

const chartOptions = {
  chart: {
    type: 'line',
    toolbar: {
      show: false
    },
    background: '#111827',
  },
  stroke: {
    curve: 'smooth',
    width: 2
  },
  colors: ['#3b82f6', '#10b981', '#f59e0b'],
  grid: {
    borderColor: '#374151'
  },
  xaxis: {
    categories: ['1h', '2h', '3h', '4h', '5h', '6h', '7h', '8h', '9h', '10h', '11h', '12h'],
    labels: {
      style: {
        colors: '#9ca3af'
      }
    }
  },
  yaxis: {
    labels: {
      style: {
        colors: '#9ca3af'
      }
    }
  },
  tooltip: {
    theme: 'dark'
  },
  legend: {
    labels: {
      colors: '#e5e7eb'
    }
  }
}

const chartSeries = [
  {
    name: 'CPU',
    data: [35, 41, 36, 26, 45, 48, 52, 53, 41, 30, 42, 42]
  },
  {
    name: 'Memória',
    data: [50, 55, 60, 65, 70, 75, 70, 65, 60, 65, 70, 68]
  },
  {
    name: 'Latência',
    data: [90, 85, 95, 115, 95, 85, 80, 85, 90, 95, 85, 85]
  }
]

const formatarTempo = (data) => {
  if (!data) return ''
  
  if (typeof data === 'string') {
    data = new Date(data)
  }
  
  return data.toLocaleString('pt-BR', { 
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const formatarData = (data) => {
  if (!data) return ''
  
  if (typeof data === 'string') {
    data = new Date(data)
  }
  
  return data.toLocaleString('pt-BR', { 
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}
</script>

<style scoped>
</style>
