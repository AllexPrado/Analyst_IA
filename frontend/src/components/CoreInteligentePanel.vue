<template>
  <div class="py-8">
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
        <div class="text-xl font-semibold">{{ dados.status }}</div>
        <div class="text-sm text-gray-400 mt-1">Última verificação: {{ formatarTempo(dados.ultimaVerificacao) }}</div>
      </div>

      <div class="rounded-xl shadow-lg p-5 bg-gray-900 text-white">
        <h3 class="text-sm text-gray-400 mb-2">Versão</h3>
        <div class="text-xl font-semibold">{{ dados.versao }}</div>
        <div class="text-sm text-gray-400 mt-1">Build {{ dados.build }}</div>
      </div>

      <div class="rounded-xl shadow-lg p-5 bg-gray-900 text-white">
        <h3 class="text-sm text-gray-400 mb-2">Uso de CPU</h3>
        <div class="flex items-end">
          <div class="text-xl font-semibold">{{ dados.cpu }}%</div>
          <div :class="`ml-2 text-sm ${dados.cpuTendencia > 0 ? 'text-red-400' : 'text-green-400'}`">
            {{ dados.cpuTendencia > 0 ? '↑' : '↓' }} {{ Math.abs(dados.cpuTendencia) }}%
          </div>
        </div>
        <div class="w-full bg-gray-700 h-1.5 mt-2 rounded-full">
          <div class="h-full rounded-full" 
               :class="`${dados.cpu > 80 ? 'bg-red-500' : dados.cpu > 60 ? 'bg-yellow-500' : 'bg-green-500'}`"
               :style="`width: ${dados.cpu}%`"></div>
        </div>
      </div>

      <div class="rounded-xl shadow-lg p-5 bg-gray-900 text-white">
        <h3 class="text-sm text-gray-400 mb-2">Memória</h3>
        <div class="flex items-end">
          <div class="text-xl font-semibold">{{ dados.memoria }}%</div>
          <div :class="`ml-2 text-sm ${dados.memoriaTendencia > 0 ? 'text-red-400' : 'text-green-400'}`">
            {{ dados.memoriaTendencia > 0 ? '↑' : '↓' }} {{ Math.abs(dados.memoriaTendencia) }}%
          </div>
        </div>
        <div class="w-full bg-gray-700 h-1.5 mt-2 rounded-full">
          <div class="h-full rounded-full" 
               :class="`${dados.memoria > 80 ? 'bg-red-500' : dados.memoria > 60 ? 'bg-yellow-500' : 'bg-green-500'}`"
               :style="`width: ${dados.memoria}%`"></div>
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
            <div class="text-xl font-semibold">{{ dados.taxaProcessamento }} /s</div>
            <div :class="`text-xs ${
              dados.taxaProcessamentoChange > 0 ? 'text-green-400' : 
              dados.taxaProcessamentoChange < 0 ? 'text-red-400' : 
              'text-gray-400'
            }`">
              {{ dados.taxaProcessamentoChange > 0 ? '↑' : dados.taxaProcessamentoChange < 0 ? '↓' : '→' }}
              {{ Math.abs(dados.taxaProcessamentoChange) }}% vs média
            </div>
          </div>

          <div class="p-3 bg-gray-800 rounded-lg">
            <div class="text-sm text-gray-400 mb-1">Latência Média</div>
            <div class="text-xl font-semibold">{{ dados.latenciaMedia }}ms</div>
            <div :class="`text-xs ${
              dados.latenciaMediaChange < 0 ? 'text-green-400' : 
              dados.latenciaMediaChange > 0 ? 'text-red-400' : 
              'text-gray-400'
            }`">
              {{ dados.latenciaMediaChange < 0 ? '↓' : dados.latenciaMediaChange > 0 ? '↑' : '→' }}
              {{ Math.abs(dados.latenciaMediaChange) }}% vs média
            </div>
          </div>

          <div class="p-3 bg-gray-800 rounded-lg">
            <div class="text-sm text-gray-400 mb-1">Precisão</div>
            <div class="text-xl font-semibold">{{ dados.precisao }}%</div>
            <div :class="`text-xs ${
              dados.precisaoChange > 0 ? 'text-green-400' : 
              dados.precisaoChange < 0 ? 'text-red-400' : 
              'text-gray-400'
            }`">
              {{ dados.precisaoChange > 0 ? '↑' : dados.precisaoChange < 0 ? '↓' : '→' }}
              {{ Math.abs(dados.precisaoChange) }}% vs baseline
            </div>
          </div>

          <div class="p-3 bg-gray-800 rounded-lg">
            <div class="text-sm text-gray-400 mb-1">Cache Hit Rate</div>
            <div class="text-xl font-semibold">{{ dados.cacheHitRate }}%</div>
            <div :class="`text-xs ${
              dados.cacheHitRateChange > 0 ? 'text-green-400' : 
              dados.cacheHitRateChange < 0 ? 'text-red-400' : 
              'text-gray-400'
            }`">
              {{ dados.cacheHitRateChange > 0 ? '↑' : dados.cacheHitRateChange < 0 ? '↓' : '→' }}
              {{ Math.abs(dados.cacheHitRateChange) }}% vs média
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
            <tr v-for="(componente, idx) in dados.componentes" :key="idx" class="border-b border-gray-800">
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
        <div v-for="(tarefa, idx) in dados.tarefas" :key="idx" class="p-3 border border-gray-700 rounded-lg bg-gray-800">
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
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api/backend.js'

const nivelLog = ref('todos')

const dados = ref({
  status: 'Operacional',
  versao: '2.5.3',
  build: '20230815.125',
  cpu: 42,
  cpuTendencia: -3,
  memoria: 68,
  memoriaTendencia: 5,
  ultimaVerificacao: new Date(),
  taxaProcessamento: 125,
  taxaProcessamentoChange: 12,
  latenciaMedia: 85,
  latenciaMediaChange: -8,
  precisao: 98.5,
  precisaoChange: 0.7,
  cacheHitRate: 75,
  cacheHitRateChange: 5,
  componentes: [
    {
      nome: 'Modelo de Correlação',
      tipo: 'modelo',
      versao: '1.2.0',
      status: 'Ativo',
      utilizacao: 78,
      ultimaAtualizacao: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000)
    },
    {
      nome: 'Processador de Regras',
      tipo: 'regras',
      versao: '2.1.5',
      status: 'Ativo',
      utilizacao: 45,
      ultimaAtualizacao: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
    },
    {
      nome: 'Motor de Correlação',
      tipo: 'correlacao',
      versao: '3.0.1',
      status: 'Ativo',
      utilizacao: 62,
      ultimaAtualizacao: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000)
    },
    {
      nome: 'Analisador Preditivo',
      tipo: 'modelo',
      versao: '1.8.2',
      status: 'Ativo',
      utilizacao: 82,
      ultimaAtualizacao: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000)
    },
    {
      nome: 'Extrator de Features',
      tipo: 'processor',
      versao: '2.2.0',
      status: 'Ativo',
      utilizacao: 35,
      ultimaAtualizacao: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000)
    }
  ],
  logs: [
    { nivel: 'INFO', timestamp: '2023-08-15 10:15:22', mensagem: 'Sistema iniciado com sucesso' },
    { nivel: 'INFO', timestamp: '2023-08-15 10:15:45', mensagem: 'Carregando modelos de ML...' },
    { nivel: 'INFO', timestamp: '2023-08-15 10:16:12', mensagem: '5 modelos carregados com sucesso' },
    { nivel: 'WARNING', timestamp: '2023-08-15 10:16:30', mensagem: 'Cache com capacidade acima de 70%' },
    { nivel: 'INFO', timestamp: '2023-08-15 10:17:02', mensagem: 'Conectado ao serviço de métricas' },
    { nivel: 'ERROR', timestamp: '2023-08-15 10:17:45', mensagem: 'Falha ao carregar dados históricos: timeout' },
    { nivel: 'INFO', timestamp: '2023-08-15 10:18:22', mensagem: 'Tentativa de reconexão automática' },
    { nivel: 'INFO', timestamp: '2023-08-15 10:18:55', mensagem: 'Reconexão bem sucedida' },
    { nivel: 'WARNING', timestamp: '2023-08-15 10:19:45', mensagem: 'Latência acima do esperado: 120ms' },
    { nivel: 'INFO', timestamp: '2023-08-15 10:20:15', mensagem: 'Iniciando processamento em batch' }
  ],
  tarefas: [
    {
      nome: 'Atualização do Modelo Preditivo',
      descricao: 'Retreinar o modelo com os dados mais recentes para melhorar a precisão',
      prioridade: 'Alta',
      data: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000)
    },
    {
      nome: 'Limpeza de Cache',
      descricao: 'Remover entradas expiradas e otimizar o armazenamento',
      prioridade: 'Baixa',
      data: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000)
    },
    {
      nome: 'Backup de Configuração',
      descricao: 'Exportar configurações do sistema para backup',
      prioridade: 'Média',
      data: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000)
    },
    {
      nome: 'Verificação de Integridade',
      descricao: 'Validar integridade dos dados e corrigir inconsistências',
      prioridade: 'Média',
      data: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000)
    }
  ]
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

onMounted(async () => {
  try {
    // Aqui faria a chamada para API
    // const response = await api.get('/core-inteligente')
    // dados.value = { ...dados.value, ...response.data }
    
    // Por enquanto, mantendo os dados de exemplo
  } catch (error) {
    console.error('Erro ao carregar dados do Core Inteligente:', error)
  }
})
</script>

<style scoped>
</style>
