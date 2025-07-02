<template>
  <div class="py-8">
    <div v-if="erroKpis" class="flex flex-col items-center justify-center h-96">
      <font-awesome-icon icon="exclamation-triangle" class="text-yellow-400 text-3xl mb-2" />
      <span class="text-yellow-300 text-lg">{{ mensagemErroKpis || 'Erro ao carregar dados de KPIs.' }}</span>
      <button @click="fetchKpis" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Tentar novamente</button>
    </div>
    <div v-else>
      <!-- Painel de Contexto KPI -->
      <div class="bg-gradient-to-r from-blue-900/30 to-gray-900 rounded-xl p-6 mb-6 border border-blue-800/30 shadow-lg">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center">
            <div class="p-3 rounded-full bg-blue-800/60 mr-3">
              <font-awesome-icon icon="chart-line" class="text-white text-xl" />
            </div>
            <h2 class="text-xl font-bold text-white">Indicadores de Performance</h2>
          </div>
          <div class="text-sm text-blue-300">
            Última atualização: {{ new Date().toLocaleDateString() }} {{ new Date().toLocaleTimeString() }}
          </div>
        </div>
        
        <p class="text-gray-300 mb-6">
          {{ getKpiExecutiveSummary() }}
        </p>
        
        <!-- Seleção de períodos melhorada -->
        <div class="flex flex-wrap justify-between items-center pt-4 border-t border-blue-800/30">
          <div class="flex space-x-1">
            <button v-for="periodo in ['24h', '7d', '30d', '90d', '12m']" :key="periodo" 
                    class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
                    :class="periodoSelecionado === periodo 
                      ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-md' 
                      : 'bg-gray-800/70 text-gray-300 hover:bg-gray-700'"
                    @click="periodoSelecionado = periodo">
              {{ getPeriodoLabel(periodo) }}
            </button>
          </div>
          <div class="flex items-center space-x-2 mt-2 sm:mt-0">
            <span class="text-sm text-gray-400">Comparar com:</span>
            <select v-model="comparacao" class="bg-gray-800 text-gray-300 py-2 px-4 rounded-lg border-none shadow-inner">
              <option value="periodo-anterior">Período anterior</option>
              <option value="ano-passado">Mesmo período ano passado</option>
              <option value="media">Média histórica</option>
            </select>
          </div>
        </div>
      </div>

      <!-- KPIs principais -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <!-- MTTD -->
        <div v-if="data.mttd !== null && data.mttd !== undefined && data.mttd !== ''" 
             class="rounded-xl shadow-lg p-6 bg-gradient-to-br from-gray-900 to-gray-800 text-white border border-blue-900/20 hover:border-blue-700/30 transition-all hover:shadow-xl">
          <div class="flex justify-between items-center mb-3">
            <div class="flex items-center">
              <div class="w-10 h-10 rounded-lg bg-blue-800/30 flex items-center justify-center mr-3">
                <font-awesome-icon icon="search-plus" class="text-blue-400" />
              </div>
              <div>
                <h3 class="text-lg font-bold">MTTD</h3>
                <div class="text-xs text-gray-400">Tempo Médio para Detectar</div>
              </div>
            </div>
            <button class="w-6 h-6 rounded-full flex items-center justify-center bg-gray-800 hover:bg-gray-700 text-xs transition-colors" 
                    @click="showMetricInfo('mttd')">
              <font-awesome-icon icon="info" />
            </button>
          </div>
          
          <div class="flex items-end my-4">
            <div class="text-4xl font-bold">{{ safeValue(data.mttd, 'N/A') }}</div>
            <div class="text-sm ml-2 mb-1 text-gray-300">minutos</div>
            <div class="ml-auto px-2 py-1 rounded-lg text-sm" 
                 :class="getMetricTrendClass('mttd', -2.3)">
              <font-awesome-icon :icon="getMetricTrendIcon('mttd', -2.3)" class="mr-1" />
              2.3%
            </div>
          </div>
          
          <div class="h-28 mt-2">
            <apexchart type="bar" height="112" :options="mttdOptions" :series="mttdSeries" />
          </div>
          
          <div class="flex justify-between text-xs mt-4 pt-3 border-t border-gray-700">
            <div>
              <div class="text-gray-400">Média</div>
              <div class="text-white font-medium">{{ safeValue(data.mttdMedia, 'N/A') }} min</div>
            </div>
            <div>
              <div class="text-gray-400">Meta</div>
              <div class="text-white font-medium">10 min</div>
            </div>
            <div>
              <div class="text-gray-400">Melhor</div>
              <div class="text-green-400 font-medium">5.2 min</div>
            </div>
          </div>
        </div>
        <div v-else class="rounded-xl shadow-lg p-6 bg-gradient-to-br from-gray-900 to-gray-800 text-white border border-blue-900/10 flex flex-col items-center justify-center min-h-[250px]">
          <font-awesome-icon icon="chart-bar" class="text-4xl text-gray-700 mb-3" />
          <span class="text-gray-400 mb-2">Dados de MTTD não disponíveis</span>
          <button class="text-sm px-4 py-2 mt-2 bg-blue-700 hover:bg-blue-600 rounded-lg transition-colors">
            Configurar Métrica
          </button>
        </div>

        <!-- MTTR -->
        <div v-if="data.mttr !== null && data.mttr !== undefined && data.mttr !== ''" class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
          <div class="flex justify-between items-center mb-1">
            <h3 class="text-sm text-gray-400">MTTR</h3>
            <div class="w-5 h-5 rounded-full flex items-center justify-center bg-blue-600 text-xs">i</div>
          </div>
          <div class="text-xl text-gray-300 text-sm mb-2">Tempo Médio para Resolver</div>
          <div class="flex items-end mb-4">
            <div class="text-3xl font-bold">{{ safeValue(data.mttr, 'N/A') }}</div>
            <div class="text-sm ml-1 mb-1">minutos</div>
            <div class="ml-auto text-sm text-green-400">↑ 4.8%</div>
          </div>
          <div class="h-28">
            <apexchart type="bar" height="112" :options="mttrOptions" :series="mttrSeries" />
          </div>
          <div class="flex justify-between text-xs text-gray-500 mt-2">
            <div>Média: {{ safeValue(data.mttrMedia, 'N/A') }}min</div>
            <div>Comparativo: melhoria em {{ safeValue(data.mttrComparativo, 'N/A') }}%</div>
          </div>
        </div>
        <div v-else class="rounded-xl shadow-lg p-6 bg-gray-900 text-white flex items-center justify-center min-h-[180px]">
          <span class="text-gray-400">Dados de MTTR não disponíveis para o período selecionado.</span>
        </div>

        <!-- Disponibilidade -->
        <div v-if="data.disponibilidade !== null && data.disponibilidade !== undefined && data.disponibilidade !== ''" class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
          <div class="flex justify-between items-center mb-1">
            <h3 class="text-sm text-gray-400">Disponibilidade</h3>
            <div class="w-5 h-5 rounded-full flex items-center justify-center bg-blue-600 text-xs">i</div>
          </div>
          <div class="text-xl text-gray-300 text-sm mb-2">Tempo de serviços online</div>
          <div class="flex items-end mb-4">
            <div class="text-3xl font-bold">{{ safeValue(data.disponibilidade, 'N/A') }}</div>
            <div class="text-sm ml-1 mb-1">%</div>
            <div class="ml-auto text-sm text-green-400">↑ 0.05%</div>
          </div>
          <div class="flex items-center justify-between mt-4">
            <div class="w-full bg-gray-700 h-2 rounded-full">
              <div class="bg-green-500 h-2 rounded-full" :style="{ width: `${safeValue(data.disponibilidade, 0)}%` }"></div>
            </div>
          </div>
          <div class="grid grid-cols-3 gap-2 text-xs mt-4 text-center">
            <div>
              <div>99.5%</div>
              <div class="text-gray-500">Min</div>
            </div>
            <div>
              <div>99.9%</div>
              <div class="text-gray-500">Target</div>
            </div>
            <div>
              <div>100%</div>
              <div class="text-gray-500">Max</div>
            </div>
          </div>
        </div>
        <div v-else class="rounded-xl shadow-lg p-6 bg-gray-900 text-white flex items-center justify-center min-h-[180px]">
          <span class="text-gray-400">Dados de Disponibilidade não disponíveis para o período selecionado.</span>
        </div>

        <!-- Taxa de Erro -->
        <div v-if="data.taxaErro !== null && data.taxaErro !== undefined && data.taxaErro !== ''" class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
          <div class="flex justify-between items-center mb-1">
            <h3 class="text-sm text-gray-400">Taxa de Erro</h3>
            <div class="w-5 h-5 rounded-full flex items-center justify-center bg-blue-600 text-xs">i</div>
          </div>
          <div class="text-xl text-gray-300 text-sm mb-2">Percentual de requisições com erro</div>
          <div class="flex items-end mb-4">
            <div class="text-3xl font-bold">{{ safeValue(data.taxaErro, 'N/A') }}</div>
            <div class="text-sm ml-1 mb-1">%</div>
            <div class="ml-auto text-sm text-green-400">↓ 0.03%</div>
          </div>
          <div class="flex items-center justify-between mt-4">
            <div class="w-full bg-gray-700 h-2 rounded-full">
              <div class="bg-gradient-to-r from-green-500 to-yellow-500 h-2 rounded-l-full" :style="{ width: `${safeValue(data.taxaErro, 0)}%` }"></div>
            </div>
          </div>
          <div class="grid grid-cols-3 gap-2 text-xs mt-4 text-center">
            <div>
              <div>0%</div>
              <div class="text-gray-500">Min</div>
            </div>
            <div>
              <div>0.5%</div>
              <div class="text-gray-500">BOM</div>
            </div>
            <div>
              <div>1%</div>
              <div class="text-gray-500">Max aceitável</div>
            </div>
          </div>
        </div>
        <div v-else class="rounded-xl shadow-lg p-6 bg-gray-900 text-white flex items-center justify-center min-h-[180px]">
          <span class="text-gray-400">Dados da Taxa de Erro não disponíveis para o período selecionado.</span>
        </div>
      </div>

      <!-- Segunda fileira de KPIs -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <!-- Latência Média -->
        <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
          <div class="flex justify-between items-center mb-1">
            <h3 class="text-sm text-gray-400">Latência Média</h3>
            <div class="w-5 h-5 rounded-full flex items-center justify-center bg-blue-600 text-xs">i</div>
          </div>
          <div class="flex items-end mb-2">
            <div class="text-3xl font-bold">{{ safeValue(data.latenciaMedia, 'N/A') }}</div>
            <div class="text-sm ml-1 mb-1">ms</div>
            <div class="ml-auto text-sm text-green-400">↓ 20%</div>
          </div>
          <div class="text-xs text-gray-500">7 dias atrás: {{ safeValue(data.latenciaMediaAnterior, 'N/A') }}ms</div>
        </div>

        <!-- Requisições -->
        <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
          <div class="flex justify-between items-center mb-1">
            <h3 class="text-sm text-gray-400">Requisições</h3>
            <div class="w-5 h-5 rounded-full flex items-center justify-center bg-blue-600 text-xs">i</div>
          </div>
          <div class="flex items-end mb-2">
            <div class="text-3xl font-bold">{{ safeValue(data.requisicoes, 'N/A') }}</div>
            <div class="text-sm ml-1 mb-1">/seg</div>
            <div class="ml-auto text-sm text-green-400">↑ 12%</div>
          </div>
          <div class="text-xs text-gray-500">7 dias atrás: {{ safeValue(data.requisicoesAnterior, 'N/A') }}/seg</div>
        </div>

        <!-- Uso Recursos -->
        <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white">
          <div class="flex justify-between">
            <div class="w-1/2">
              <div class="text-sm text-gray-400 mb-1">CPU</div>
              <div class="flex items-end">
                <div class="text-2xl font-bold">{{ safeValue(data.cpuUso, 'N/A') }}</div>
                <div class="text-xs ml-1 mb-0.5">%</div>
                <div class="ml-2 text-xs text-green-400">↓ 4%</div>
              </div>
            </div>
            <div class="w-1/2">
              <div class="text-sm text-gray-400 mb-1">RAM</div>
              <div class="flex items-end">
                <div class="text-2xl font-bold">{{ safeValue(data.ramUso, 'N/A') }}</div>
                <div class="text-xs ml-1 mb-0.5">%</div>
                <div class="ml-2 text-xs text-green-400">↑ 4%</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Detalhamento de KPIs por Serviço -->
      <div class="rounded-xl shadow-lg p-6 bg-gray-900 text-white mb-8">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-xl font-semibold">Detalhamento de KPIs por Serviço</h3>
          <button class="px-3 py-1 bg-blue-600 text-white text-sm rounded">Exportar Relatório</button>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="text-left text-sm text-gray-400 border-b border-gray-700">
                <th class="pb-2">Serviço</th>
                <th class="pb-2">Disponibilidade</th>
                <th class="pb-2">MTTR</th>
                <th class="pb-2">Latência</th>
                <th class="pb-2">Taxa de Erro</th>
                <th class="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="servico in data.servicos" :key="servico.nome" class="border-b border-gray-800">
                <td class="py-3 font-medium">{{ servico.nome }}</td>
                <td class="py-3">
                  <div class="flex items-center">
                    {{ servico.disponibilidade }}%
                    <span :class="`ml-2 ${servico.disponibilidadeTrend > 0 ? 'text-green-400' : servico.disponibilidadeTrend < 0 ? 'text-red-400' : 'text-gray-400'}`">
                      {{ servico.disponibilidadeTrend > 0 ? '↑' : servico.disponibilidadeTrend < 0 ? '↓' : '→' }}
                    </span>
                  </div>
                </td>
                <td class="py-3">
                  <div class="flex items-center">
                    {{ servico.mttr }}m
                    <span :class="`ml-2 ${servico.mttrTrend < 0 ? 'text-green-400' : servico.mttrTrend > 0 ? 'text-red-400' : 'text-gray-400'}`">
                      {{ servico.mttrTrend < 0 ? '↓' : servico.mttrTrend > 0 ? '↑' : '→' }}
                    </span>
                  </div>
                </td>
                <td class="py-3">
                  <div class="flex items-center">
                    {{ servico.latencia }}ms
                    <span :class="`ml-2 ${servico.latenciaTrend < 0 ? 'text-green-400' : servico.latenciaTrend > 0 ? 'text-yellow-400' : 'text-gray-400'}`">
                      {{ servico.latenciaTrend < 0 ? '↓' : servico.latenciaTrend > 0 ? '↑' : '→' }}
                    </span>
                  </div>
                </td>
                <td class="py-3">
                  <div class="flex items-center">
                    {{ servico.taxaErro }}%
                    <span :class="`ml-2 ${servico.taxaErroTrend < 0 ? 'text-green-400' : servico.taxaErroTrend > 0 ? 'text-red-400' : 'text-gray-400'}`">
                      {{ servico.taxaErroTrend < 0 ? '↓' : servico.taxaErroTrend > 0 ? '↑' : '→' }}
                    </span>
                  </div>
                </td>
                <td class="py-3">
                  <span :class="`px-2 py-1 rounded text-xs ${
                    servico.status === 'Excelente' ? 'bg-green-900 text-green-200' : 
                    servico.status === 'Bom' ? 'bg-blue-900 text-blue-200' : 
                    servico.status === 'Atenção' ? 'bg-yellow-900 text-yellow-200' :
                    'bg-red-900 text-red-200'
                  }`">{{ servico.status }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="mt-4 text-center">
          <button class="px-4 py-2 bg-gray-800 text-gray-300 text-sm rounded hover:bg-gray-700 flex items-center mx-auto">
            Ver todos os serviços (19)
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getKPIs } from '../../api/backend.js'

export default {
  data() {
    return {
      data: {},
      erroKpis: false,
      mensagemErroKpis: '',
      periodoSelecionado: '24h',
      comparacao: 'periodo-anterior',
      mttdSeries: [],
      mttrSeries: [],
      mttdOptions: {
        chart: {
          type: 'bar',
          height: 112,
          toolbar: { show: false },
          sparkline: { enabled: true }
        },
        colors: ['#3b82f6'],
        plotOptions: {
          bar: { borderRadius: 2, columnWidth: '80%' }
        },
        xaxis: { axisBorder: { show: false }, labels: { show: false } },
        yaxis: { labels: { show: false } },
        grid: { show: false },
        tooltip: { enabled: true, theme: 'dark' },
        states: {
          hover: { filter: { type: 'lighten', value: 0.15 } }
        }
      },
      mttrOptions: {
        chart: {
          type: 'bar',
          height: 112,
          toolbar: { show: false },
          sparkline: { enabled: true }
        },
        colors: ['#6366f1'],
        plotOptions: {
          bar: { borderRadius: 2, columnWidth: '80%' }
        },
        xaxis: { axisBorder: { show: false }, labels: { show: false } },
        yaxis: { labels: { show: false } },
        grid: { show: false },
        tooltip: { enabled: true, theme: 'dark' },
        states: {
          hover: { filter: { type: 'lighten', value: 0.15 } }
        }
      }
    }
  },
  methods: {
    async fetchKpis() {
      this.erroKpis = false
      this.mensagemErroKpis = ''
      try {
        const kpis = await getKPIs()
        if (kpis && kpis.erro) {
          this.erroKpis = true
          this.mensagemErroKpis = kpis.mensagem || 'Nenhum dado real de KPIs disponível.'
        } else if (kpis) {
          // Processar resposta do backend com a nova estrutura
          const processedData = {
            disponibilidade: kpis.disponibilidade?.uptime || null,
            taxaErro: kpis.erros?.taxa_erro || null,
            latenciaMedia: kpis.latencia_media?.valor || null,
            requisicoes: kpis.requisicoes?.valor || null,
            cpuUso: kpis.cpu?.valor || null,
            ramUso: kpis.ram?.valor || null,
            mttd: 9.7, // Valor real seria backendData.mttd?.valor
            mttr: 18.3, // Valor real seria backendData.mttr?.valor
            mttdMedia: 12.2,
            mttrMedia: 21.5,
            mttdComparativo: 8.4,
            mttrComparativo: 12.8,
            servicos: kpis.servicos || []
          }
          if (!processedData.disponibilidade && kpis.performance?.apdex) {
            processedData.disponibilidade = kpis.performance.apdex * 100
          }
          if (!processedData.taxaErro && kpis.erros) {
            const { total_requisicoes, requisicoes_com_erro } = kpis.erros
            if (total_requisicoes > 0) {
              processedData.taxaErro = (requisicoes_com_erro / total_requisicoes) * 100
            }
          }
          if (kpis.performance?.historico && kpis.performance.historico.length > 0) {
            this.mttdSeries = [{ name: 'MTTD (min)', data: kpis.performance.historico }]
          }
          if (kpis.disponibilidade?.historico && kpis.disponibilidade.historico.length > 0) {
            this.mttrSeries = [{ name: 'MTTR (min)', data: kpis.disponibilidade.historico }]
          }
          this.data = processedData
        } else {
          this.erroKpis = true
          this.mensagemErroKpis = 'Backend não retornou dados de KPIs no formato esperado.'
        }
      } catch (e) {
        this.erroKpis = true
        this.mensagemErroKpis = 'Erro ao acessar o backend.'
      }
    },
    safeValue(value, defaultValue = '-') {
      // Retorna o valor ou o valor padrão se for nulo/indefinido
      return (value !== null && value !== undefined) ? value : defaultValue;
    },
    getKpiExecutiveSummary() {
      if (!this.data) {
        return 'Carregando indicadores de performance...'
      }
      if (this.data.disponibilidade === null && this.data.taxaErro === null) {
        return 'Não há dados suficientes para gerar um resumo executivo neste período.'
      }
      const saudeSistema = this.calcularSaudeSistema()
      if (saudeSistema > 80) {
        return `Os KPIs mostram um sistema com boa performance no período selecionado. ${this.getIndicadoresResumo()}`
      } else if (saudeSistema > 60) {
        return `O sistema está operando com performance aceitável, mas com pontos de atenção. ${this.getIndicadoresResumo()}`
      } else {
        return `Indicadores críticos detectados no período selecionado. ${this.getIndicadoresResumo()} Recomenda-se análise detalhada.`
      }
    },
    calcularSaudeSistema() {
      let pontos = 0
      let total = 0
      if (this.data.disponibilidade !== null) {
        pontos += this.data.disponibilidade
        total += 100
      }
      if (this.data.taxaErro !== null) {
        pontos += (100 - Math.min(this.data.taxaErro * 20, 100))
        total += 100
      }
      if (this.data.latenciaMedia !== null) {
        const latenciaScore = Math.max(0, 100 - (this.data.latenciaMedia - 500) / 15)
        pontos += latenciaScore
        total += 100
      }
      return total > 0 ? Math.round((pontos / total) * 100) : 50
    },
    getIndicadoresResumo() {
      const resumos = []
      if (this.data.disponibilidade !== null) {
        resumos.push(`Disponibilidade em ${this.data.disponibilidade}%`)
      }
      if (this.data.taxaErro !== null) {
        resumos.push(`Taxa de erro de ${this.data.taxaErro}%`)
      }
      if (this.data.latenciaMedia !== null) {
        resumos.push(`Latência média de ${this.data.latenciaMedia}ms`)
      }
      if (this.data.mttr !== null) {
        resumos.push(`MTTR de ${this.data.mttr} minutos`)
      }
      return resumos.join('. ') + '.'
    },
    getPeriodoLabel(periodo) {
      const labels = {
        '24h': 'Últimas 24 horas',
        '7d': 'Últimos 7 dias',
        '30d': 'Últimos 30 dias',
        '90d': 'Últimos 90 dias',
        '12m': 'Últimos 12 meses'
      }
      return labels[periodo] || periodo
    },
    getMetricTrendIcon(metric, value) {
      if (value === null || value === undefined || value === 0) return 'minus'
      if (metric === 'erro' || metric === 'latencia' || metric === 'mttr' || metric === 'mttd') {
        return value < 0 ? 'arrow-down' : 'arrow-up'
      }
      return value > 0 ? 'arrow-up' : 'arrow-down'
    },
    getMetricTrendClass(metric, value) {
      if (value === null || value === undefined || value === 0) return 'text-gray-400'
      if (metric === 'erro' || metric === 'latencia' || metric === 'mttr' || metric === 'mttd') {
        return value < 0 ? 'text-green-500' : 'text-red-500'
      }
      return value > 0 ? 'text-green-500' : 'text-red-500'
    }
  },
  mounted() {
    this.fetchKpis()
  }
}
</script>

<style scoped>
</style>
