<template>
  <div class="py-8">
    <!-- Cabeçalho e filtros -->
    <div class="mb-6 flex flex-wrap justify-between items-center">
      <h2 class="text-2xl font-bold text-white mb-4 md:mb-0">Insights Executivos</h2>
      <div class="flex space-x-2">
        <button v-for="periodo in ['7d', '30d', '90d', '12m']" :key="periodo" 
                class="px-4 py-1 rounded-md"
                :class="periodoSelecionado === periodo ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-300'"
                @click="periodoSelecionado = periodo">
          {{ periodo }}
        </button>
        <select v-model="categoriaFiltrada" class="bg-gray-800 text-gray-300 py-1 px-3 rounded-md border-none ml-2">
          <option value="todos">Todas categorias</option>
          <option value="eficiencia">Eficiência</option>
          <option value="custo">Economia</option>
          <option value="performance">Performance</option>
          <option value="seguranca">Segurança</option>
        </select>
      </div>
    </div>

    <!-- Resumo de indicadores principais -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      <!-- ROI Monitoramento -->
      <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
        <div class="flex justify-between items-center mb-1">
          <h3 class="text-sm text-gray-400">ROI Monitoramento</h3>
          <div class="w-5 h-5 rounded-full flex items-center justify-center bg-blue-600 text-xs">i</div>
        </div>
        <div class="text-3xl font-bold mb-2">{{ dados.roiMonitoramento }}x</div>
        <div class="flex items-center">
          <div class="text-green-400 text-sm">↑ {{ dados.roiAumento }}% vs período anterior</div>
        </div>
        <div class="mt-3 text-xs text-gray-400">
          Cada R$1 investido retorna R${{ dados.roiMonitoramento }} em prevenção
        </div>
      </div>

      <!-- Produtividade -->
      <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
        <div class="flex justify-between items-center mb-1">
          <h3 class="text-sm text-gray-400">Aumento de Produtividade</h3>
          <div class="w-5 h-5 rounded-full flex items-center justify-center bg-blue-600 text-xs">i</div>
        </div>
        <div class="text-3xl font-bold mb-2">{{ dados.aumentoProdutividade }}%</div>
        <div class="flex items-center">
          <div class="text-green-400 text-sm">↑ {{ dados.produtividadeComparativo }}% vs período anterior</div>
        </div>
        <div class="mt-3 text-xs text-gray-400">
          {{ dados.horasEconomizadas }} horas/mês economizadas em operações
        </div>
      </div>

      <!-- Economia de Custos -->
      <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
        <div class="flex justify-between items-center mb-1">
          <h3 class="text-sm text-gray-400">Economia de Custos</h3>
          <div class="w-5 h-5 rounded-full flex items-center justify-center bg-blue-600 text-xs">i</div>
        </div>
        <div class="text-3xl font-bold mb-2">R$ {{ formatNumber(dados.economiaTotal) }}</div>
        <div class="flex items-center">
          <div class="text-green-400 text-sm">↑ {{ dados.economiaAumento }}% vs período anterior</div>
        </div>
        <div class="mt-3 text-xs text-gray-400">
          Redução de {{ dados.incidentesEvitados }} incidentes críticos
        </div>
      </div>

      <!-- Satisfação -->
      <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
        <div class="flex justify-between items-center mb-1">
          <h3 class="text-sm text-gray-400">Satisfação</h3>
          <div class="w-5 h-5 rounded-full flex items-center justify-center bg-blue-600 text-xs">i</div>
        </div>
        <div class="text-3xl font-bold mb-2">{{ dados.satisfacao }}/10</div>
        <div class="flex items-center">
          <div class="text-green-400 text-sm">↑ {{ dados.satisfacaoAumento }} vs período anterior</div>
        </div>
        <div class="mt-3 text-xs text-gray-400">
          Baseado em {{ dados.avaliacoes }} avaliações internas
        </div>
      </div>
    </div>

    <!-- Gráfico de impacto financeiro -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      <!-- Impacto financeiro -->
      <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
        <h3 class="text-xl font-semibold mb-4">Impacto Financeiro</h3>
        <div class="h-64">
          <SafeApexChart
            type="bar"
            height="100%"
            :options="impactoOptions"
            :series="impactoSeries"
            noDataMessage="Nenhum dado de impacto disponível"
            noDataIcon="chart-bar">
          </SafeApexChart>
        </div>
      </div>

      <!-- Tendência de problemas evitados -->
      <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
        <h3 class="text-xl font-semibold mb-4">Problemas Evitados</h3>
        <div class="h-64">
          <SafeApexChart
            type="area"
            height="100%"
            :options="problemasOptions"
            :series="problemasSeries"
            noDataMessage="Nenhum dado de problemas disponível"
            noDataIcon="bug">
          </SafeApexChart>
        </div>
      </div>
    </div>

    <!-- Recomendações estratégicas -->
    <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white mb-8">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-xl font-semibold">Recomendações Estratégicas</h3>
        <button class="px-3 py-1 bg-blue-600 text-white text-sm rounded">Ver todas</button>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="(recomendacao, idx) in dados.recomendacoes || []" :key="idx" class="p-4 border border-gray-700 rounded-lg bg-gray-800">
          <div class="flex items-center mb-3">
            <div :class="`w-10 h-10 rounded-full flex items-center justify-center mr-3 ${
              recomendacao.categoria === 'eficiencia' ? 'bg-green-900 text-green-200' : 
              recomendacao.categoria === 'custo' ? 'bg-blue-900 text-blue-200' : 
              recomendacao.categoria === 'seguranca' ? 'bg-red-900 text-red-200' : 
              'bg-purple-900 text-purple-200'
            }`">
              <i :class="`fas ${
                recomendacao.categoria === 'eficiencia' ? 'fa-chart-line' : 
                recomendacao.categoria === 'custo' ? 'fa-dollar-sign' : 
                recomendacao.categoria === 'seguranca' ? 'fa-shield-alt' : 
                'fa-tachometer-alt'
              }`"></i>
            </div>
            <h4 class="font-medium">{{ recomendacao.titulo }}</h4>
          </div>
          <p class="text-sm text-gray-400 mb-3">{{ recomendacao.descricao }}</p>
          <div class="flex justify-between text-xs">
            <div :class="`font-medium ${
              recomendacao.prioridade === 'Alta' ? 'text-red-400' : 
              recomendacao.prioridade === 'Média' ? 'text-yellow-400' : 
              'text-blue-400'
            }`">Prioridade: {{ recomendacao.prioridade }}</div>
            <div>ROI: {{ recomendacao.roi }}x</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tabela de oportunidades de otimização -->
    <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white mb-8">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-xl font-semibold">Oportunidades de Otimização</h3>
        <div class="flex items-center">
          <span class="mr-2 text-sm">Ordenar por:</span>
          <select v-model="ordenacao" class="bg-gray-800 text-gray-300 py-1 px-3 rounded-md border-none">
            <option value="impacto">Impacto</option>
            <option value="roi">ROI</option>
            <option value="facilidade">Facilidade</option>
            <option value="custo">Menor Custo</option>
          </select>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="text-left text-sm text-gray-400 border-b border-gray-700">
              <th class="pb-2">Oportunidade</th>
              <th class="pb-2">Categoria</th>
              <th class="pb-2">Impacto</th>
              <th class="pb-2">Esforço</th>
              <th class="pb-2">ROI</th>
              <th class="pb-2">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(oportunidade, idx) in dados.oportunidades || []" :key="idx" class="border-b border-gray-800">
              <td class="py-3 font-medium">{{ oportunidade.nome }}</td>
              <td class="py-3">
                <span :class="`px-2 py-1 rounded text-xs ${
                  oportunidade.categoria === 'Infraestrutura' ? 'bg-blue-900 text-blue-200' : 
                  oportunidade.categoria === 'Código' ? 'bg-green-900 text-green-200' : 
                  oportunidade.categoria === 'Processo' ? 'bg-yellow-900 text-yellow-200' : 
                  'bg-purple-900 text-purple-200'
                }`">{{ oportunidade.categoria }}</span>
              </td>
              <td class="py-3">
                <div class="flex items-center">
                  <div class="relative w-20 bg-gray-700 h-2 rounded-full overflow-hidden">
                    <div :class="`absolute top-0 left-0 h-full ${
                      oportunidade.impacto >= 8 ? 'bg-green-500' : 
                      oportunidade.impacto >= 5 ? 'bg-yellow-500' : 
                      'bg-red-500'
                    }`" :style="`width: ${oportunidade.impacto * 10}%`"></div>
                  </div>
                  <span class="ml-2">{{ oportunidade.impacto }}/10</span>
                </div>
              </td>
              <td class="py-3">
                <div class="flex items-center">
                  <div class="relative w-20 bg-gray-700 h-2 rounded-full overflow-hidden">
                    <div :class="`absolute top-0 left-0 h-full ${
                      oportunidade.esforco <= 3 ? 'bg-green-500' : 
                      oportunidade.esforco <= 7 ? 'bg-yellow-500' : 
                      'bg-red-500'
                    }`" :style="`width: ${oportunidade.esforco * 10}%`"></div>
                  </div>
                  <span class="ml-2">{{ oportunidade.esforco }}/10</span>
                </div>
              </td>
              <td class="py-3">{{ oportunidade.roi }}x</td>
              <td class="py-3">
                <span :class="`px-2 py-1 rounded text-xs ${
                  oportunidade.status === 'Implementado' ? 'bg-green-900 text-green-200' : 
                  oportunidade.status === 'Em progresso' ? 'bg-blue-900 text-blue-200' : 
                  oportunidade.status === 'Planejado' ? 'bg-yellow-900 text-yellow-200' : 
                  'bg-gray-700 text-gray-400'
                }`">{{ oportunidade.status }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Resumo Executivo -->
    <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
      <h3 class="text-xl font-semibold mb-4">Resumo Executivo</h3>
      <SafeDataDisplay :data="dados.resumoExecutivo" noDataMessage="Resumo executivo não disponível" noDataIcon="file-alt">
        <div class="border border-gray-700 rounded-lg p-4 bg-gray-800">
          <p class="mb-4">{{ dados.resumoExecutivo?.introducao || '' }}</p>
          
          <div class="mb-4">
            <h4 class="text-lg font-medium mb-2">Principais destaques:</h4>
            <ul class="list-disc pl-5 space-y-1">
              <li v-for="(destaque, idx) in dados.resumoExecutivo?.destaques || []" :key="idx">
                {{ destaque }}
              </li>
            </ul>
          </div>
          
          <div class="mb-4">
            <h4 class="text-lg font-medium mb-2">Possíveis riscos:</h4>
            <ul class="list-disc pl-5 space-y-1">
              <li v-for="(risco, idx) in dados.resumoExecutivo?.riscos || []" :key="idx" class="text-yellow-400">
                {{ risco }}
              </li>
            </ul>
          </div>

          <p>{{ dados.resumoExecutivo?.conclusao || '' }}</p>
        </div>
      </SafeDataDisplay>
      <div class="mt-4 flex justify-center">
        <button class="px-4 py-2 bg-blue-600 text-white rounded flex items-center">
          <i class="fas fa-file-pdf mr-2"></i>
          Exportar Relatório Completo
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getInsights } from '../../api/backend.js'
import SafeApexChart from '../SafeApexChart.vue'
import SafeDataDisplay from '../SafeDataDisplay.vue'
import { createSafeApexSeries, createSafeApexOptions } from '../../utils/nullDataHandler.js'

const periodoSelecionado = ref('30d')
const categoriaFiltrada = ref('todos')
const ordenacao = ref('impacto')

const formatNumber = (value) => {
  return new Intl.NumberFormat('pt-BR').format(value)
}

const dados = ref({
  roiMonitoramento: 0,
  roiAumento: 0,
  aumentoProdutividade: 0,
  produtividadeComparativo: 0,
  horasEconomizadas: 0,
  economiaTotal: 0,
  economiaAumento: 0,
  incidentesEvitados: 0,
  satisfacao: 0,
  satisfacaoAumento: 0,
  avaliacoes: 0,
  recomendacoes: [],
  oportunidades: [],
  resumoExecutivo: {
    introducao: '',
    destaques: [],
    riscos: [],
    conclusao: ''
  }
})
const impactoOptions = {
  chart: {
    type: 'bar',
    toolbar: { show: false },
    background: '#111827',
  },
  plotOptions: {
    bar: {
      horizontal: true,
      barHeight: '70%',
      borderRadius: 4
    }
  },
  colors: ['#3b82f6', '#10b981'],
  grid: {
    borderColor: '#374151',
    strokeDashArray: 5
  },
  xaxis: {
    categories: [],
    labels: {
      style: { colors: '#9ca3af' },
      formatter: function (value) {
        return 'R$ ' + new Intl.NumberFormat('pt-BR').format(value)
      }
    }
  },
  yaxis: {
    labels: { style: { colors: '#9ca3af' } }
  },
  tooltip: {
    theme: 'dark',
    y: {
      formatter: function (value) {
        return 'R$ ' + new Intl.NumberFormat('pt-BR').format(value)
      }
    }
  },
  legend: {
    labels: { colors: '#e5e7eb' }
  }
}
const impactoSeries = ref([])
const problemasOptions = {
  chart: {
    type: 'area',
    toolbar: { show: false },
    background: '#111827',
  },
  colors: ['#ef4444', '#10b981'],
  dataLabels: { enabled: false },
  stroke: { curve: 'smooth', width: 2 },
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
  xaxis: {
    categories: [],
    labels: { style: { colors: '#9ca3af' } }
  },
  yaxis: {
    labels: { style: { colors: '#9ca3af' } }
  },
  tooltip: { theme: 'dark' },
  legend: { labels: { colors: '#e5e7eb' } }
}
const problemasSeries = ref([])

// Método para gerar resumo executivo baseado nos dados disponíveis
function generateExecutiveSummary() {
  if (!dados.value || Object.keys(dados.value).length === 0) {
    return {
      introducao: "Não há dados suficientes para gerar um resumo executivo.",
      destaques: [],
      riscos: [],
      conclusao: "Aguardando dados para análise."
    }
  }
  
  const resumo = {
    introducao: "",
    destaques: [],
    riscos: [],
    conclusao: ""
  }
  
  // Gerar introdução
  resumo.introducao = `Relatório de desempenho do período ${periodoSelecionado.value}. `
  
  if (dados.value.roiMonitoramento) {
    resumo.introducao += `O ROI do monitoramento está em ${dados.value.roiMonitoramento}x, `
    resumo.introducao += dados.value.roiAumento > 0 
      ? `representando um aumento de ${dados.value.roiAumento}% em relação ao período anterior.`
      : `permanecendo estável em relação ao período anterior.`
  }
  
  // Gerar destaques
  if (dados.value.economiaTotal) {
    resumo.destaques.push(`Economia total de R$ ${formatNumber(dados.value.economiaTotal)} no período.`)
  }
  
  if (dados.value.horasEconomizadas) {
    resumo.destaques.push(`Economia de ${dados.value.horasEconomizadas} horas/mês em operações.`)
  }
  
  if (dados.value.incidentesEvitados) {
    resumo.destaques.push(`${dados.value.incidentesEvitados} incidentes críticos evitados.`)
  }
  
  // Adicionar destaques baseados nas recomendações de alta prioridade
  if (dados.value.recomendacoes && dados.value.recomendacoes.length > 0) {
    const recomendacoesAlta = dados.value.recomendacoes.filter(r => r.prioridade === 'Alta')
    if (recomendacoesAlta.length > 0) {
      resumo.destaques.push(`${recomendacoesAlta.length} recomendações de alta prioridade identificadas.`)
    }
  }
  
  // Gerar riscos
  if (dados.value.oportunidades && dados.value.oportunidades.length > 0) {
    const oportunidadesNaoImplementadas = dados.value.oportunidades.filter(o => o.status !== 'Implementado')
    if (oportunidadesNaoImplementadas.length > 0) {
      resumo.riscos.push(`${oportunidadesNaoImplementadas.length} oportunidades de otimização ainda não implementadas.`)
      
      // Adicionar os riscos das oportunidades de alto impacto
      const altoImpacto = oportunidadesNaoImplementadas.filter(o => o.impacto >= 8)
      if (altoImpacto.length > 0) {
        resumo.riscos.push(`${altoImpacto.length} oportunidades de alto impacto que requerem atenção imediata.`)
      }
    }
  }
  
  // Gerar conclusão
  resumo.conclusao = `Recomendamos focar nas ações de ${dados.value.recomendacoes?.length > 0 ? 
                      dados.value.recomendacoes[0]?.categoria || 'otimização' : 'otimização'} 
                      para maximizar o retorno sobre investimento no próximo período.`
  
  return resumo
}

onMounted(async () => {
  try {
    const { data: backendData } = await getInsights()
    
    // Se não tiver resumo executivo, gerar um baseado nos dados
    if (backendData && (!backendData.resumoExecutivo || Object.keys(backendData.resumoExecutivo).length === 0)) {
      dados.value = { ...backendData }
      dados.value.resumoExecutivo = generateExecutiveSummary()
    } else {
      dados.value = backendData || {}
    }
    
    // Atualiza gráficos se vierem do backend
    if (backendData && backendData.impactoSeries) {
      impactoSeries.value = backendData.impactoSeries
    } else {
      // Dados fallback para visualização
      impactoSeries.value = [
        {
          name: 'Atual',
          data: [15000, 25000, 35000, 18000, 29000]
        },
        {
          name: 'Potencial com otimizações',
          data: [18000, 32000, 42000, 24000, 38000]
        }
      ]
    }
    
    if (backendData && backendData.problemasSeries) {
      problemasSeries.value = backendData.problemasSeries
    } else {
      // Dados fallback para visualização
      problemasSeries.value = [
        {
          name: 'Incidentes Ocorridos',
          data: [18, 15, 12, 8, 7, 5, 4]
        },
        {
          name: 'Incidentes Evitados',
          data: [5, 8, 12, 15, 18, 22, 25]
        }
      ]
    }
    
    if (backendData && backendData.impactoCategorias) {
      impactoOptions.xaxis.categories = backendData.impactoCategorias
    } else {
      impactoOptions.xaxis.categories = ['Infraestrutura', 'Segurança', 'Desenvolvimento', 'Operações', 'Treinamento']
    }
    
    if (backendData && backendData.problemasCategorias) {
      problemasOptions.xaxis.categories = backendData.problemasCategorias
    } else {
      problemasOptions.xaxis.categories = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul']
    }
  } catch (e) {
    console.error("Erro ao carregar insights:", e)
    // Gera um resumo com mensagem de erro
    dados.value.resumoExecutivo = {
      introducao: "Não foi possível carregar os dados do servidor.",
      destaques: [],
      riscos: ["Possível problema de conexão com o servidor."],
      conclusao: "Tente novamente mais tarde ou contate o suporte."
    }
  }
})
</script>

<style scoped>
</style>
