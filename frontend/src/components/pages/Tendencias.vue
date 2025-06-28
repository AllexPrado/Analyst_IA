<template>
  <div class="py-8">
    <!-- Seleção de períodos e filtros -->
    <div class="mb-6 flex space-x-2">
      <button v-for="periodo in ['7d', '30d', '90d', '12m']" :key="periodo" 
              class="px-4 py-1 rounded-md"
              :class="periodoSelecionado === periodo ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-300'"
              @click="periodoSelecionado = periodo">
        {{ periodo }}
      </button>
      <div class="ml-auto flex space-x-2">
        <select v-model="tipoGrafico" class="bg-gray-800 text-gray-300 py-1 px-3 rounded-md border-none">
          <option value="linha">Gráfico de Linha</option>
          <option value="barra">Gráfico de Barras</option>
          <option value="area">Gráfico de Área</option>
        </select>
        <select v-model="recursoFiltrado" class="bg-gray-800 text-gray-300 py-1 px-3 rounded-md border-none">
          <option value="todos">Todos os recursos</option>
          <option v-for="recurso in dados.recursos" :key="recurso.id" :value="recurso.id">
            {{ recurso.nome }}
          </option>
        </select>
      </div>
    </div>

    <!-- Removido botão Atualizar para evitar consumo de tokens -->
    <div class="flex justify-end items-center mb-4">
      <span class="text-sm text-gray-400">
        Última atualização: {{ ultimaAtualizacao }}
      </span>
    </div>

    <!-- Gráfico principal de tendências -->
    <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white mb-8">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-xl font-semibold">Tendências de Desempenho</h3>
        <div class="flex space-x-2">
          <div v-for="(metrica, idx) in metricas" :key="idx" 
               class="flex items-center cursor-pointer" 
               @click="toggleMetrica(metrica.id)">
            <div :class="`w-3 h-3 rounded-full mr-1 ${metrica.cor}`"></div>
            <div :class="metricasSelecionadas.includes(metrica.id) ? 'text-white' : 'text-gray-500'">
              {{ metrica.nome }}
            </div>
          </div>
        </div>
      </div>
      <div class="h-80">
        <SafeApexChart 
          type="line"
          height="100%"
          :options="chartOptions"
          :series="seriesData"
          noDataMessage="Nenhum dado de tendência disponível"
          noDataIcon="chart-line">
        </SafeApexChart>
      </div>
    </div>

    <!-- Anomalias detectadas -->
    <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white mb-8">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-xl font-semibold">Anomalias Detectadas</h3>
        <button class="px-3 py-1 bg-blue-600 text-white text-sm rounded">Ver histórico</button>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-left text-sm text-gray-400 border-b border-gray-700">
              <th class="pb-2">Data/Hora</th>
              <th class="pb-2">Recurso</th>
              <th class="pb-2">Métrica</th>
              <th class="pb-2">Desvio</th>
              <th class="pb-2">Duração</th>
              <th class="pb-2">Severidade</th>
              <th class="pb-2">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(anomalia, idx) in dados.anomaliasRecentes" :key="idx" class="border-b border-gray-800">
              <td class="py-3">{{ anomalia.dataHora }}</td>
              <td class="py-3 font-medium">{{ anomalia.recurso }}</td>
              <td class="py-3">{{ anomalia.metrica }}</td>
              <td class="py-3">{{ anomalia.desvio }}%</td>
              <td class="py-3">{{ anomalia.duracao }}</td>
              <td class="py-3">
                <span :class="`px-2 py-1 rounded text-xs ${
                  anomalia.severidade === 'Baixa' ? 'bg-blue-900 text-blue-200' : 
                  anomalia.severidade === 'Média' ? 'bg-yellow-900 text-yellow-200' :
                  'bg-red-900 text-red-200'
                }`">{{ anomalia.severidade }}</span>
              </td>
              <td class="py-3">
                <span :class="`px-2 py-1 rounded text-xs ${
                  anomalia.status === 'Resolvido' ? 'bg-green-900 text-green-200' : 
                  anomalia.status === 'Em Análise' ? 'bg-yellow-900 text-yellow-200' :
                  'bg-red-900 text-red-200'
                }`">{{ anomalia.status }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Projeções e Previsões -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
      <!-- Previsões futuras -->
      <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
        <h3 class="text-xl font-semibold mb-4">Previsões para os próximos 30 dias</h3>
        <div class="h-64">
          <SafeApexChart 
            type="area"
            height="100%"
            :options="previsaoOptions"
            :series="previsaoSeries"
            noDataMessage="Nenhuma previsão disponível"
            noDataIcon="crystal-ball">
          </SafeApexChart>
        </div>
        <div class="mt-4 p-4 border border-gray-700 rounded-lg bg-gray-800">
          <div class="font-semibold mb-2">Análise Preditiva:</div>
          <ul class="text-sm text-gray-300 space-y-1">
            <li v-for="(previsao, idx) in dados.previsoes" :key="idx">
              <span :class="`mr-2 ${
                previsao.tendencia === 'positiva' ? 'text-green-400' : 
                previsao.tendencia === 'negativa' ? 'text-red-400' : 
                'text-yellow-400'
              }`">{{ previsao.tendencia === 'positiva' ? '↑' : previsao.tendencia === 'negativa' ? '↓' : '⚠' }}</span>
              {{ previsao.texto }}
            </li>
          </ul>
        </div>
      </div>

      <!-- Análise de Padrões -->
      <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
        <h3 class="text-xl font-semibold mb-4">Análise de Padrões</h3>
        <div class="mb-4">
          <div class="flex justify-between text-sm mb-1">
            <div>Padrões Sazonais</div>
            <div>Confiança: 87%</div>
          </div>
          <div class="h-28 mb-4">
            <SafeApexChart 
              type="heatmap"
              height="100%"
              :options="padraoOptions"
              :series="padraoSeries"
              noDataMessage="Nenhum padrão identificado"
              noDataIcon="th">
            </SafeApexChart>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div v-for="(padrao, idx) in dados.padroes" :key="idx" class="p-3 border border-gray-700 rounded-lg">
            <div class="font-medium mb-1">{{ padrao.titulo }}</div>
            <div class="text-gray-400">{{ padrao.descricao }}</div>
            <div :class="`mt-2 text-xs font-medium ${
              padrao.impacto === 'Positivo' ? 'text-green-400' : 
              padrao.impacto === 'Negativo' ? 'text-red-400' : 
              'text-yellow-400'
            }`">Impacto: {{ padrao.impacto }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recomendações baseadas em tendências -->
    <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
      <h3 class="text-xl font-semibold mb-4">Recomendações Baseadas em Tendências</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div v-for="(recomendacao, idx) in dados.recomendacoes" :key="idx" class="p-4 border border-gray-700 rounded-lg">
          <div :class="`h-10 w-10 rounded-full mb-3 flex items-center justify-center ${
            recomendacao.categoria === 'performance' ? 'bg-blue-900 text-blue-200' : 
            recomendacao.categoria === 'capacidade' ? 'bg-purple-900 text-purple-200' :
            'bg-green-900 text-green-200'
          }`">
            <i :class="`fas ${
              recomendacao.categoria === 'performance' ? 'fa-bolt' : 
              recomendacao.categoria === 'capacidade' ? 'fa-server' :
              'fa-chart-line'
            }`"></i>
          </div>
          <h4 class="font-semibold mb-2">{{ recomendacao.titulo }}</h4>
          <p class="text-sm text-gray-400 mb-4">{{ recomendacao.descricao }}</p>
          <div class="flex justify-between text-xs">
            <div>{{ recomendacao.impacto }}</div>
            <div :class="`font-medium ${
              recomendacao.urgencia === 'Alta' ? 'text-red-400' : 
              recomendacao.urgencia === 'Média' ? 'text-yellow-400' :
              'text-blue-400'
            }`">Urgência: {{ recomendacao.urgencia }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Resumo Executivo -->
    <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
      <h3 class="text-xl font-semibold mb-4">Resumo Executivo</h3>
      <p class="text-sm text-gray-300">
        {{ getTendenciasExecutiveSummary() }}
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getTendencias } from '../../api/backend.js'
import SafeApexChart from '../SafeApexChart.vue'
import { createSafeApexSeries, createSafeApexOptions } from '../../utils/nullDataHandler.js'

const periodoSelecionado = ref('30d')
const tipoGrafico = ref('linha')
const recursoFiltrado = ref('todos')
const ultimaAtualizacao = ref('')

const metricas = [
  { id: 'cpu', nome: 'CPU', cor: 'bg-blue-500' },
  { id: 'memoria', nome: 'Memória', cor: 'bg-green-500' },
  { id: 'latencia', nome: 'Latência', cor: 'bg-yellow-500' },
  { id: 'erros', nome: 'Erros', cor: 'bg-red-500' },
  { id: 'qps', nome: 'QPS', cor: 'bg-purple-500' }
]

const metricasSelecionadas = ref(['cpu', 'memoria', 'latencia'])
const dados = ref({})

const toggleMetrica = (id) => {
  if (metricasSelecionadas.value.includes(id)) {
    metricasSelecionadas.value = metricasSelecionadas.value.filter(m => m !== id)
  } else {
    metricasSelecionadas.value.push(id)
  }
}

// Configuração do gráfico principal
const chartOptions = {
  chart: {
    type: 'line',
    toolbar: {
      show: true,
      tools: {
        download: true,
        selection: true,
        zoom: true,
        zoomin: true,
        zoomout: true,
        pan: true,
      }
    },
    background: '#111827',
  },
  colors: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'],
  stroke: {
    curve: 'smooth',
    width: 2
  },
  grid: {
    borderColor: '#374151',
    strokeDashArray: 5
  },
  markers: {
    size: 3,
    strokeWidth: 0
  },
  xaxis: {
    categories: [],
    labels: {
      style: {
        colors: '#9ca3af'
      }
    },
    axisBorder: {
      color: '#374151'
    },
    axisTicks: {
      color: '#374151'
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

// Séries de dados para o gráfico principal
const seriesData = computed(() => {
  if (!dados.value.metricas) return []
  return metricas
    .filter(m => metricasSelecionadas.value.includes(m.id))
    .map(m => ({
      name: m.nome,
      data: dados.value.metricas[m.id] || []
    }))
})

// Configuração para o gráfico de previsão
const previsaoOptions = {
  chart: {
    type: 'area',
    toolbar: {
      show: false
    },
    background: '#111827',
  },
  colors: ['#3b82f6', '#ef4444'],
  stroke: {
    curve: 'smooth',
    width: 2,
    dashArray: [0, 5]
  },
  fill: {
    type: 'gradient',
    gradient: {
      shadeIntensity: 1,
      opacityFrom: 0.4,
      opacityTo: 0.1,
      stops: [0, 100]
    }
  },
  grid: {
    borderColor: '#374151',
    strokeDashArray: 5
  },
  markers: {
    size: 0
  },
  xaxis: {
    categories: Array.from({ length: 30 }, (_, i) => `D+${i+1}`),
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

// Séries para o gráfico de previsão
const previsaoSeries = [
  {
    name: 'Utilização de CPU',
    data: [58, 60, 63, 65, 68, 70, 73, 75, 78, 80, 82, 84, 85, 87, 88, 90, 92, 93, 94, 95, 96, 97, 98, 99, 98, 97, 96, 95, 94, 93]
  },
  {
    name: 'Previsão com otimização',
    data: [58, 59, 61, 62, 64, 65, 67, 68, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 84, 83, 82, 81, 80, 79]
  }
]

// Configurações para o gráfico de padrões
const padraoOptions = {
  chart: {
    type: 'heatmap',
    toolbar: {
      show: false
    },
    background: '#111827',
  },
  dataLabels: {
    enabled: false
  },
  colors: ["#3b82f6"],
  xaxis: {
    categories: ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab'],
    labels: {
      style: {
        colors: '#9ca3af'
      }
    }
  },
  tooltip: {
    theme: 'dark'
  }
}

// Séries para o gráfico de padrões
const padraoSeries = [
  {
    name: '00:00-04:00',
    data: [{ x: 'Dom', y: 25 }, { x: 'Seg', y: 15 }, { x: 'Ter', y: 15 }, { x: 'Qua', y: 15 }, { x: 'Qui', y: 15 }, { x: 'Sex', y: 15 }, { x: 'Sab', y: 20 }]
  },
  {
    name: '04:00-08:00',
    data: [{ x: 'Dom', y: 15 }, { x: 'Seg', y: 30 }, { x: 'Ter', y: 35 }, { x: 'Qua', y: 35 }, { x: 'Qui', y: 30 }, { x: 'Sex', y: 30 }, { x: 'Sab', y: 10 }]
  },
  {
    name: '08:00-12:00',
    data: [{ x: 'Dom', y: 20 }, { x: 'Seg', y: 80 }, { x: 'Ter', y: 85 }, { x: 'Qua', y: 90 }, { x: 'Qui', y: 85 }, { x: 'Sex', y: 80 }, { x: 'Sab', y: 25 }]
  },
  {
    name: '12:00-16:00',
    data: [{ x: 'Dom', y: 30 }, { x: 'Seg', y: 70 }, { x: 'Ter', y: 75 }, { x: 'Qua', y: 80 }, { x: 'Qui', y: 75 }, { x: 'Sex', y: 70 }, { x: 'Sab', y: 35 }]
  },
  {
    name: '16:00-20:00',
    data: [{ x: 'Dom', y: 35 }, { x: 'Seg', y: 50 }, { x: 'Ter', y: 55 }, { x: 'Qua', y: 60 }, { x: 'Qui', y: 55 }, { x: 'Sex', y: 50 }, { x: 'Sab', y: 40 }]
  },
  {
    name: '20:00-00:00',
    data: [{ x: 'Dom', y: 30 }, { x: 'Seg', y: 25 }, { x: 'Ter', y: 30 }, { x: 'Qua', y: 30 }, { x: 'Qui', y: 30 }, { x: 'Sex', y: 40 }, { x: 'Sab', y: 45 }]
  }
]

onMounted(async () => {
  try {
    const { data } = await getTendencias()
    dados.value = data || { metricas: {} }
    ultimaAtualizacao.value = new Date().toLocaleString()
  } catch (e) {
    console.error("Erro ao carregar tendências:", e)
    dados.value = { metricas: {} }
    ultimaAtualizacao.value = "Erro na atualização"
  }
})

// Função para gerar um resumo executivo das tendências
function getTendenciasExecutiveSummary() {
  if (!dados.value || !dados.value.metricas) {
    return "Não há dados suficientes para gerar um resumo das tendências."
  }
  
  // Identificar as métricas com maior crescimento e declínio
  const metricasComTendencia = metricasSelecionadas.value.filter(metricaId => {
    const metricaData = dados.value.metricas[metricaId]
    return Array.isArray(metricaData) && metricaData.length > 1
  })
  
  if (metricasComTendencia.length === 0) {
    return "Não há dados de tendência suficientes para análise."
  }
  
  // Calcular tendências para cada métrica
  const tendencias = metricasComTendencia.map(metricaId => {
    const metrica = metricas.find(m => m.id === metricaId)
    const dados = dados.value.metricas[metricaId]
    const primeiro = dados[0]
    const ultimo = dados[dados.length - 1]
    const variacao = ultimo - primeiro
    const percentual = (variacao / Math.abs(primeiro)) * 100
    
    return {
      nome: metrica.nome,
      variacao,
      percentual
    }
  })
  
  // Ordenar por maior variação percentual (absoluta)
  tendencias.sort((a, b) => Math.abs(b.percentual) - Math.abs(a.percentual))
  
  // Gerar texto do resumo
  let resumo = `Análise do período ${periodoSelecionado.value}: `
  
  if (tendencias.length > 0) {
    const maiorAlta = tendencias.find(t => t.percentual > 0)
    const maiorBaixa = tendencias.find(t => t.percentual < 0)
    
    if (maiorAlta) {
      resumo += `${maiorAlta.nome} apresenta a maior alta (${maiorAlta.percentual.toFixed(1)}%). `
    }
    
    if (maiorBaixa) {
      resumo += `${maiorBaixa.nome} mostra queda de ${Math.abs(maiorBaixa.percentual).toFixed(1)}%. `
    }
    
    // Adicionar informações sobre anomalias se disponíveis
    if (dados.value.anomaliasRecentes && dados.value.anomaliasRecentes.length > 0) {
      resumo += `Detectadas ${dados.value.anomaliasRecentes.length} anomalias no período.`
    }
  } else {
    resumo += "Não foram detectadas variações significativas nas métricas analisadas."
  }
  
  return resumo
}
</script>

<style scoped>
</style>
