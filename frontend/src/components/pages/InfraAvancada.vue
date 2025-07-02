<template>
  <div class="py-8">
    <div v-if="loading" class="flex items-center justify-center h-96">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
    </div>
    <div v-else-if="error" class="flex flex-col items-center justify-center h-96">
      <font-awesome-icon icon="exclamation-triangle" class="text-yellow-400 text-3xl mb-2" />
      <span class="text-yellow-300 text-lg">Erro ao carregar dados avançados.</span>
      <div class="text-red-300 text-sm mt-2 max-w-lg text-center">
        <p>Verifique se o servidor backend está em execução na porta 8000.</p>
        <p>URL da API: http://localhost:8000/api/avancado/kubernetes</p>
        <p>Abra o console do navegador (F12) para ver detalhes do erro.</p>
        <div class="mt-3 text-white bg-gray-800 p-3 rounded-md text-left">
          <p class="font-bold mb-1">Possíveis soluções:</p>
          <ol class="list-decimal list-inside ml-2 space-y-1 text-sm">
            <li>Verifique se o backend está em execução com <code class="bg-gray-700 px-1 rounded">python main.py</code></li>
            <li>Certifique-se que os arquivos de cache existem em <code class="bg-gray-700 px-1 rounded">backend/cache/</code></li>
            <li>Execute <code class="bg-gray-700 px-1 rounded">check_and_fix_cache.py</code> para regenerar dados</li>
            <li>Reinicie tanto o backend quanto o frontend</li>
          </ol>
        </div>
      </div>
      <button @click="fetchData" class="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Tentar novamente</button>
    </div>
    <div v-else>
      <!-- Navegação entre tipos de dados avançados -->
      <div class="flex mb-6 bg-gray-800 rounded-lg p-1 shadow-lg">
        <button 
          v-for="tab in tabs" 
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            'py-2 px-4 rounded-md transition-all duration-200 flex-grow text-center font-medium',
            activeTab === tab.id 
              ? 'bg-blue-600 text-white shadow-md' 
              : 'text-gray-300 hover:bg-gray-700'
          ]"
        >
          <font-awesome-icon :icon="tab.icon" class="mr-2" />
          {{ tab.name }}
        </button>
      </div>
      
      <!-- Conteúdo da aba Kubernetes -->
      <div v-if="activeTab === 'kubernetes'" class="space-y-8">
        <div class="bg-gradient-to-r from-indigo-900 to-indigo-800 rounded-xl p-6 mb-6 shadow-xl border border-indigo-700">
          <div class="flex items-center gap-4 mb-3">
            <div class="p-3 rounded-full bg-indigo-700">
              <font-awesome-icon :icon="['fas', 'cubes']" class="text-white text-xl" />
            </div>
            <h3 class="text-xl font-bold text-white">Kubernetes Overview</h3>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mt-5 pt-4 border-t border-indigo-700">
            <div>
              <div class="text-xs text-indigo-300">Clusters</div>
              <div class="text-2xl font-bold text-white">{{ kubernetesData.summary?.total_clusters || 0 }}</div>
            </div>
            <div>
              <div class="text-xs text-indigo-300">Nodes</div>
              <div class="text-2xl font-bold text-white">{{ kubernetesData.summary?.total_nodes || 0 }}</div>
            </div>
            <div>
              <div class="text-xs text-indigo-300">Pods</div>
              <div class="text-2xl font-bold text-white">{{ kubernetesData.summary?.total_pods || 0 }}</div>
            </div>
            <div>
              <div class="text-xs text-indigo-300">Healthy Pods</div>
              <div class="text-2xl font-bold text-green-400">{{ kubernetesData.summary?.healthy_pods_percent || 0 }}%</div>
            </div>
            <div>
              <div class="text-xs text-indigo-300">CPU Usage</div>
              <div class="text-2xl font-bold text-white">{{ kubernetesData.summary?.resource_usage?.cpu || 0 }}%</div>
            </div>
          </div>
        </div>
        
        <!-- Clusters -->
        <div class="bg-gray-900 rounded-xl p-6 shadow-lg">
          <h3 class="text-lg font-bold text-white mb-4">Clusters</h3>
          <div class="overflow-x-auto">
            <table class="w-full text-sm text-left text-gray-300">
              <thead class="text-xs text-gray-400 uppercase bg-gray-800">
                <tr>
                  <th class="px-4 py-3">Name</th>
                  <th class="px-4 py-3">Version</th>
                  <th class="px-4 py-3">Nodes</th>
                  <th class="px-4 py-3">Pods</th>
                  <th class="px-4 py-3">CPU Usage</th>
                  <th class="px-4 py-3">Memory Usage</th>
                  <th class="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="cluster in kubernetesData.clusters" :key="cluster.name" class="border-b border-gray-800">
                  <td class="px-4 py-3">{{ cluster.name }}</td>
                  <td class="px-4 py-3">{{ cluster.version }}</td>
                  <td class="px-4 py-3">{{ cluster.nodes }}</td>
                  <td class="px-4 py-3">{{ cluster.pods }}</td>
                  <td class="px-4 py-3">
                    <div class="w-full bg-gray-700 rounded-full h-2">
                      <div :style="`width: ${cluster.cpu_usage}%`" :class="`h-2 rounded-full ${getStatusColor(cluster.cpu_usage, true)}`"></div>
                    </div>
                    <span class="text-xs">{{ cluster.cpu_usage }}%</span>
                  </td>
                  <td class="px-4 py-3">
                    <div class="w-full bg-gray-700 rounded-full h-2">
                      <div :style="`width: ${cluster.memory_usage}%`" :class="`h-2 rounded-full ${getStatusColor(cluster.memory_usage, true)}`"></div>
                    </div>
                    <span class="text-xs">{{ cluster.memory_usage }}%</span>
                  </td>
                  <td class="px-4 py-3">
                    <span :class="`px-2 py-1 rounded text-xs font-medium ${getStatusBadgeColor(cluster.status)}`">
                      {{ cluster.status }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- Nodes & Pods -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="bg-gray-900 rounded-xl p-6 shadow-lg">
            <h3 class="text-lg font-bold text-white mb-4">Nodes (Top 5)</h3>
            <div class="space-y-4">
              <div v-for="node in kubernetesData.nodes.slice(0, 5)" :key="node.name" class="bg-gray-800 rounded-lg p-4">
                <div class="flex justify-between mb-2">
                  <span class="font-medium text-white">{{ node.name }}</span>
                  <span :class="`px-2 py-1 rounded text-xs font-medium ${getStatusBadgeColor(node.status)}`">
                    {{ node.status }}
                  </span>
                </div>
                <div class="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div class="text-gray-400 mb-1">CPU ({{ node.cpu.capacity }} cores)</div>
                    <div class="w-full bg-gray-700 rounded-full h-2">
                      <div :style="`width: ${node.cpu.usage_percent}%`" :class="`h-2 rounded-full ${getStatusColor(node.cpu.usage_percent, true)}`"></div>
                    </div>
                    <span class="text-xs">{{ node.cpu.usage_percent }}%</span>
                  </div>
                  <div>
                    <div class="text-gray-400 mb-1">Memory ({{ node.memory.capacity_gb }} GB)</div>
                    <div class="w-full bg-gray-700 rounded-full h-2">
                      <div :style="`width: ${node.memory.usage_percent}%`" :class="`h-2 rounded-full ${getStatusColor(node.memory.usage_percent, true)}`"></div>
                    </div>
                    <span class="text-xs">{{ node.memory.usage_percent }}%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="bg-gray-900 rounded-xl p-6 shadow-lg">
            <h3 class="text-lg font-bold text-white mb-4">Pods with Issues</h3>
            <div v-if="problematicPods.length === 0" class="text-center py-10 text-gray-400">
              <font-awesome-icon icon="check-circle" class="text-3xl text-green-500 mb-2" />
              <p>Nenhum pod com problemas encontrado</p>
            </div>
            <div v-else class="space-y-4">
              <div v-for="pod in problematicPods.slice(0, 5)" :key="pod.name" class="bg-gray-800 rounded-lg p-4">
                <div class="flex justify-between mb-2">
                  <span class="font-medium text-white">{{ pod.name }}</span>
                  <span :class="`px-2 py-1 rounded text-xs font-medium ${getStatusBadgeColor(pod.status)}`">
                    {{ pod.status }}
                  </span>
                </div>
                <div class="text-sm">
                  <div class="text-gray-400">Namespace: {{ pod.namespace }}</div>
                  <div class="text-gray-400">Cluster: {{ pod.cluster }}</div>
                  <div class="text-gray-400">Restarts: <span class="text-red-400">{{ pod.restarts }}</span></div>
                  <div class="text-gray-400">Issues: 
                    <span v-for="(issue, idx) in pod.issues" :key="idx" class="inline-block bg-red-900 text-red-300 rounded px-2 py-1 text-xs mr-1">
                      {{ issue }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Conteúdo da aba Infraestrutura -->
      <div v-if="activeTab === 'infrastructure'" class="space-y-8">
        <div class="bg-gradient-to-r from-blue-900 to-blue-800 rounded-xl p-6 mb-6 shadow-xl border border-blue-700">
          <div class="flex items-center gap-4 mb-3">
            <div class="p-3 rounded-full bg-blue-700">
              <font-awesome-icon icon="server" class="text-white text-xl" />
            </div>
            <h3 class="text-xl font-bold text-white">Infraestrutura Detalhada</h3>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mt-5 pt-4 border-t border-blue-700">
            <div>
              <div class="text-xs text-blue-300">Total Servers</div>
              <div class="text-2xl font-bold text-white">{{ infraData.summary?.total_servers || 0 }}</div>
            </div>
            <div>
              <div class="text-xs text-blue-300">Healthy Servers</div>
              <div class="text-2xl font-bold text-green-400">{{ infraData.summary?.healthy_percent || 0 }}%</div>
            </div>
            <div>
              <div class="text-xs text-blue-300">Regions</div>
              <div class="text-2xl font-bold text-white">{{ infraData.summary?.regions || 0 }}</div>
            </div>
            <div>
              <div class="text-xs text-blue-300">CPU Usage</div>
              <div class="text-2xl font-bold text-white">{{ infraData.summary?.resource_usage?.cpu || 0 }}%</div>
            </div>
            <div>
              <div class="text-xs text-blue-300">Memory Usage</div>
              <div class="text-2xl font-bold text-white">{{ infraData.summary?.resource_usage?.memory || 0 }}%</div>
            </div>
          </div>
        </div>
        
        <!-- Servidores -->
        <div class="bg-gray-900 rounded-xl p-6 shadow-lg">
          <h3 class="text-lg font-bold text-white mb-4">Servidores</h3>
          <div class="overflow-x-auto">
            <table class="w-full text-sm text-left text-gray-300">
              <thead class="text-xs text-gray-400 uppercase bg-gray-800">
                <tr>
                  <th class="px-4 py-3">Name</th>
                  <th class="px-4 py-3">Type</th>
                  <th class="px-4 py-3">Region</th>
                  <th class="px-4 py-3">CPU Usage</th>
                  <th class="px-4 py-3">Memory Usage</th>
                  <th class="px-4 py-3">Disk Usage</th>
                  <th class="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="server in infraData.servers" :key="server.id" class="border-b border-gray-800">
                  <td class="px-4 py-3">{{ server.name }}</td>
                  <td class="px-4 py-3">{{ server.type }}</td>
                  <td class="px-4 py-3">{{ server.region }}</td>
                  <td class="px-4 py-3">
                    <div class="w-full bg-gray-700 rounded-full h-2">
                      <div :style="`width: ${server.cpu.usage_percent}%`" :class="`h-2 rounded-full ${getStatusColor(server.cpu.usage_percent, true)}`"></div>
                    </div>
                    <span class="text-xs">{{ server.cpu.usage_percent }}%</span>
                  </td>
                  <td class="px-4 py-3">
                    <div class="w-full bg-gray-700 rounded-full h-2">
                      <div :style="`width: ${server.memory.usage_percent}%`" :class="`h-2 rounded-full ${getStatusColor(server.memory.usage_percent, true)}`"></div>
                    </div>
                    <span class="text-xs">{{ server.memory.usage_percent }}%</span>
                  </td>
                  <td class="px-4 py-3">
                    <div class="w-full bg-gray-700 rounded-full h-2">
                      <div :style="`width: ${server.disk.usage_percent}%`" :class="`h-2 rounded-full ${getStatusColor(server.disk.usage_percent, true)}`"></div>
                    </div>
                    <span class="text-xs">{{ server.disk.usage_percent }}%</span>
                  </td>
                  <td class="px-4 py-3">
                    <span :class="`px-2 py-1 rounded text-xs font-medium ${getStatusBadgeColor(server.status)}`">
                      {{ server.status }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- Alertas -->
        <div class="bg-gray-900 rounded-xl p-6 shadow-lg">
          <h3 class="text-lg font-bold text-white mb-4">Alertas Ativos</h3>
          <div v-if="infraData.alerts.length === 0" class="text-center py-10 text-gray-400">
            <font-awesome-icon icon="check-circle" class="text-3xl text-green-500 mb-2" />
            <p>Nenhum alerta ativo no momento</p>
          </div>
          <div v-else class="space-y-4">
            <div v-for="alert in infraData.alerts" :key="alert.id" :class="`bg-gray-800 rounded-lg p-4 border-l-4 ${alert.severity === 'critical' ? 'border-red-600' : 'border-yellow-600'}`">
              <div class="flex justify-between mb-2">
                <span class="font-medium text-white">{{ alert.message }}</span>
                <span :class="`px-2 py-1 rounded text-xs font-medium ${alert.severity === 'critical' ? 'bg-red-900 text-red-300' : 'bg-yellow-900 text-yellow-300'}`">
                  {{ alert.severity }}
                </span>
              </div>
              <div class="text-sm">
                <div class="text-gray-400">Servidor: {{ alert.server_name }}</div>
                <div class="text-gray-400">Tipo: {{ alert.type }}</div>
                <div class="text-gray-400">Duração: {{ alert.duration_minutes }} minutos</div>
                <div class="text-gray-400">Timestamp: {{ formatDate(alert.timestamp) }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Conteúdo da aba Topologia -->
      <div v-if="activeTab === 'topology'" class="space-y-8">
        <div class="bg-gradient-to-r from-green-900 to-green-800 rounded-xl p-6 mb-6 shadow-xl border border-green-700">
          <div class="flex items-center gap-4 mb-3">
            <div class="p-3 rounded-full bg-green-700">
              <font-awesome-icon icon="project-diagram" class="text-white text-xl" />
            </div>
            <h3 class="text-xl font-bold text-white">Topologia de Serviços</h3>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mt-5 pt-4 border-t border-green-700">
            <div>
              <div class="text-xs text-green-300">Total Services</div>
              <div class="text-2xl font-bold text-white">{{ topologyData.summary?.total_services || 0 }}</div>
            </div>
            <div>
              <div class="text-xs text-green-300">Healthy</div>
              <div class="text-2xl font-bold text-green-400">{{ topologyData.summary?.healthy_services || 0 }}</div>
            </div>
            <div>
              <div class="text-xs text-green-300">Degraded</div>
              <div class="text-2xl font-bold text-yellow-400">{{ topologyData.summary?.degraded_services || 0 }}</div>
            </div>
            <div>
              <div class="text-xs text-green-300">Critical</div>
              <div class="text-2xl font-bold text-red-400">{{ topologyData.summary?.critical_services || 0 }}</div>
            </div>
          </div>
        </div>
        
        <!-- Visualização da Topologia -->
        <div class="bg-gray-900 rounded-xl p-6 shadow-lg">
          <h3 class="text-lg font-bold text-white mb-4">Diagrama de Topologia</h3>
          <div class="h-96 border border-gray-700 rounded-lg bg-gray-800 p-4" ref="topologyContainer">
            <!-- D3.js vai renderizar o gráfico aqui -->
          </div>
        </div>
        
        <!-- Serviços -->
        <div class="bg-gray-900 rounded-xl p-6 shadow-lg">
          <h3 class="text-lg font-bold text-white mb-4">Serviços</h3>
          <div class="overflow-x-auto">
            <table class="w-full text-sm text-left text-gray-300">
              <thead class="text-xs text-gray-400 uppercase bg-gray-800">
                <tr>
                  <th class="px-4 py-3">Nome</th>
                  <th class="px-4 py-3">Apdex</th>
                  <th class="px-4 py-3">Tempo de Resposta</th>
                  <th class="px-4 py-3">Throughput</th>
                  <th class="px-4 py-3">Taxa de Erro</th>
                  <th class="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="service in topologyData.nodes" :key="service.id" class="border-b border-gray-800">
                  <td class="px-4 py-3">{{ service.name }}</td>
                  <td class="px-4 py-3">
                    <div class="w-full bg-gray-700 rounded-full h-2">
                      <div :style="`width: ${service.metrics.apdex * 100}%`" :class="`h-2 rounded-full ${getApdexColor(service.metrics.apdex)}`"></div>
                    </div>
                    <span class="text-xs">{{ service.metrics.apdex.toFixed(2) }}</span>
                  </td>
                  <td class="px-4 py-3">{{ service.metrics.response_time.toFixed(1) }} ms</td>
                  <td class="px-4 py-3">{{ service.metrics.throughput }} rpm</td>
                  <td class="px-4 py-3">
                    <div class="w-full bg-gray-700 rounded-full h-2">
                      <div :style="`width: ${Math.min(service.metrics.error_rate * 200, 100)}%`" :class="`h-2 rounded-full ${getErrorRateColor(service.metrics.error_rate)}`"></div>
                    </div>
                    <span class="text-xs">{{ (service.metrics.error_rate * 100).toFixed(2) }}%</span>
                  </td>
                  <td class="px-4 py-3">
                    <span :class="`px-2 py-1 rounded text-xs font-medium ${getStatusBadgeColor(service.status)}`">
                      {{ service.status }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- Dependências -->
        <div class="bg-gray-900 rounded-xl p-6 shadow-lg">
          <h3 class="text-lg font-bold text-white mb-4">Dependências entre Serviços</h3>
          <div class="overflow-x-auto">
            <table class="w-full text-sm text-left text-gray-300">
              <thead class="text-xs text-gray-400 uppercase bg-gray-800">
                <tr>
                  <th class="px-4 py-3">Origem</th>
                  <th class="px-4 py-3">Destino</th>
                  <th class="px-4 py-3">Chamadas/min</th>
                  <th class="px-4 py-3">Erros</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(link, index) in topologyData.links" :key="index" class="border-b border-gray-800">
                  <td class="px-4 py-3">{{ getServiceName(link.source) }}</td>
                  <td class="px-4 py-3">{{ getServiceName(link.target) }}</td>
                  <td class="px-4 py-3">{{ link.calls_per_minute }}</td>
                  <td class="px-4 py-3">
                    <span :class="link.errors > 0 ? 'text-red-400' : 'text-green-400'">
                      {{ link.errors }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import apiClient from '../../api/axios'
import advancedDataService from '../../api/advancedDataService'
import * as d3 from 'd3'
import { useTopologyGraph } from '../../utils/topologyGraph'

// Estado da página
const loading = ref(true)
const error = ref(false)
const activeTab = ref('kubernetes')
const kubernetesData = ref({ summary: {}, clusters: [], nodes: [], pods: [] })
const infraData = ref({ summary: {}, servers: [], alerts: [] })
const topologyData = ref({ summary: {}, nodes: [], links: [] })

// Tabs disponíveis
const tabs = [
  { id: 'kubernetes', name: 'Kubernetes', icon: ['fas', 'cubes'] },
  { id: 'infrastructure', name: 'Infraestrutura', icon: 'server' },
  { id: 'topology', name: 'Topologia', icon: 'project-diagram' }
]

// Computed properties
const problematicPods = computed(() => {
  return kubernetesData.value.pods?.filter(pod => pod.status !== 'Running') || []
})

// Métodos auxiliares
const getStatusColor = (value, isReverse = false) => {
  if (isReverse) {
    if (value < 60) return 'bg-green-500'
    if (value < 80) return 'bg-yellow-500'
    return 'bg-red-500'
  } else {
    if (value > 80) return 'bg-green-500'
    if (value > 60) return 'bg-yellow-500'
    return 'bg-red-500'
  }
}

const getStatusBadgeColor = (status) => {
  status = String(status).toLowerCase()
  if (['healthy', 'ready', 'running'].includes(status)) return 'bg-green-900 text-green-300'
  if (['degraded', 'warning', 'pending', 'cordoned'].includes(status)) return 'bg-yellow-900 text-yellow-300'
  return 'bg-red-900 text-red-300'
}

const getApdexColor = (apdex) => {
  if (apdex > 0.8) return 'bg-green-500'
  if (apdex > 0.6) return 'bg-yellow-500'
  return 'bg-red-500'
}

const getErrorRateColor = (rate) => {
  if (rate < 0.01) return 'bg-green-500'
  if (rate < 0.05) return 'bg-yellow-500'
  return 'bg-red-500'
}

const getServiceName = (serviceId) => {
  const service = topologyData.value.nodes.find(n => n.id === serviceId)
  return service ? service.name : serviceId
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short'
  }).format(date)
}

// Funções para carregar dados do backend
const getKubernetesData = async () => {
  try {
    const response = await apiClient.get('/avancado/kubernetes')
    
    // Verifica se os dados são válidos
    if (!response.data || typeof response.data !== 'object') {
      throw new Error('Dados inválidos recebidos do backend')
    }
    
    kubernetesData.value = response.data
  } catch (err) {
    console.error('Erro ao carregar dados do Kubernetes:', err)
    
    // Definir dados vazios para evitar erros de referência
    kubernetesData.value = { 
      summary: {},
      clusters: [],
      nodes: [],
      pods: []
    }
    
    throw err
  }
}

const getInfrastructureData = async () => {
  try {
    const response = await apiClient.get('/avancado/infraestrutura')
    
    // Verifica se os dados são válidos
    if (!response.data || typeof response.data !== 'object') {
      throw new Error('Dados inválidos recebidos do backend')
    }
    
    infraData.value = response.data
  } catch (err) {
    console.error('Erro ao carregar dados de Infraestrutura:', err)
    
    // Definir dados vazios para evitar erros de referência
    infraData.value = { 
      summary: {},
      servers: [],
      alerts: []
    }
    
    throw err
  }
}

const getTopologyData = async () => {
  try {
    const response = await apiClient.get('/avancado/topologia')
    
    // Verifica se os dados são válidos
    if (!response.data || typeof response.data !== 'object') {
      throw new Error('Dados inválidos recebidos do backend')
    }
    
    topologyData.value = response.data
  } catch (err) {
    console.error('Erro ao carregar dados de Topologia:', err)
    
    // Definir dados vazios para evitar erros de referência
    topologyData.value = { 
      summary: {},
      nodes: [],
      links: []
    }
    
    throw err
  }
}

// Testar conexão com o backend
const testBackendConnection = async () => {
  try {
    // Usar um endpoint simples como health check
    await apiClient.get('/health')
    console.log('Backend conectado com sucesso')
    return true
  } catch (err) {
    console.error('Erro ao conectar ao backend:', err)
    return false
  }
}

// Função principal para carregar todos os dados
const fetchData = async () => {
  loading.value = true
  error.value = false
  
  try {
    console.log('Verificando conexão com backend...')
    const isConnected = await testBackendConnection()
    
    if (!isConnected) {
      console.error('Falha na conexão com o backend')
      error.value = true
      return
    }
    
    console.log('Iniciando carregamento de dados avançados...')
    
    // Carregar cada tipo de dados separadamente para melhor diagnóstico
    let hasAnyData = false
    
    try {
      console.log('Buscando dados Kubernetes...')
      const k8sData = await advancedDataService.getKubernetesData(false) // forçar refresh
      kubernetesData.value = k8sData
      console.log('Dados Kubernetes carregados com sucesso:', kubernetesData.value)
      hasAnyData = true
    } catch (err) {
      console.error('Erro ao carregar dados Kubernetes:', err)
      // Manter erro específico, mas não falhar todo o componente
      console.warn('Continuando carregamento com dados Kubernetes vazios')
    }
    
    try {
      console.log('Buscando dados de Infraestrutura...')
      const infraDataResult = await advancedDataService.getInfrastructureData(false) // forçar refresh
      infraData.value = infraDataResult
      console.log('Dados de Infraestrutura carregados com sucesso:', infraData.value)
      hasAnyData = true
    } catch (err) {
      console.error('Erro ao carregar dados de Infraestrutura:', err)
      // Manter erro específico, mas não falhar todo o componente
      console.warn('Continuando carregamento com dados de Infraestrutura vazios')
    }
    
    try {
      console.log('Buscando dados de Topologia...')
      const topologyDataResult = await advancedDataService.getTopologyData(false) // forçar refresh
      topologyData.value = topologyDataResult
      console.log('Dados de Topologia carregados com sucesso:', topologyData.value)
      hasAnyData = true
    } catch (err) {
      console.error('Erro ao carregar dados de Topologia:', err)
      // Manter erro específico, mas não falhar todo o componente
      console.warn('Continuando carregamento com dados de Topologia vazios')
    }
    
    // Definir erro geral apenas se todos os carregamentos falharem
    error.value = !hasAnyData
    
  } catch (e) {
    console.error('Erro geral ao carregar dados avançados:', e)
    error.value = true
  } finally {
    loading.value = false
    console.log('Carregamento de dados concluído. Status de erro:', error.value)
  }
}

const topologyContainer = ref(null)

// Função para criar o gráfico D3 de topologia
const renderTopologyGraph = () => {
  if (!topologyContainer.value || !topologyData.value.nodes || !topologyData.value.links) return
  
  // Limpar o container antes de renderizar
  d3.select(topologyContainer.value).selectAll('*').remove()
  
  const width = topologyContainer.value.clientWidth
  const height = topologyContainer.value.clientHeight
  
  // Criar um SVG dentro do container
  const svg = d3.select(topologyContainer.value)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
  
  // Criar um grupo para o conteúdo do gráfico
  const g = svg.append('g')
    .attr('class', 'topology-graph')
  
  // Definir os dados do gráfico
  const nodes = topologyData.value.nodes
  const links = topologyData.value.links
  
  // Criar simulação de força para posicionamento dos nós
  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(150))
    .force('charge', d3.forceManyBody().strength(-500))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide().radius(60))
  
  // Adicionar linhas para representar as relações
  const link = g.append('g')
    .attr('class', 'links')
    .selectAll('line')
    .data(links)
    .enter()
    .append('line')
    .attr('stroke', d => d.errors > 0 ? '#f87171' : '#6b7280')  // Vermelho se tem erros, cinza se não
    .attr('stroke-width', d => Math.max(1, Math.min(5, Math.log(d.calls_per_minute) / 2)))
    .attr('stroke-opacity', 0.6)
    
  // Adicionar setas direcionais nas linhas
  svg.append('defs').selectAll('marker')
    .data(['end'])
    .enter().append('marker')
    .attr('id', d => d)
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 25)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('fill', '#6b7280')
    .attr('d', 'M0,-5L10,0L0,5')
  
  link.attr('marker-end', 'url(#end)')
  
  // Criar grupos para cada nó
  const nodeGroups = g.append('g')
    .attr('class', 'nodes')
    .selectAll('g')
    .data(nodes)
    .enter()
    .append('g')
  
  // Adicionar círculos para cada nó
  const getNodeColor = (status) => {
    status = status.toLowerCase()
    if (status === 'healthy') return '#10b981' // verde
    if (status === 'degraded') return '#f59e0b' // amarelo
    return '#ef4444' // vermelho para critical e outros
  }
  
  nodeGroups.append('circle')
    .attr('r', 25)
    .attr('fill', d => getNodeColor(d.status))
    .attr('stroke', '#1e293b')
    .attr('stroke-width', 2)
  
  // Adicionar texto para cada nó
  nodeGroups.append('text')
    .text(d => d.name)
    .attr('text-anchor', 'middle')
    .attr('dy', 35)
    .attr('fill', 'white')
    .attr('font-size', '12px')
  
  // Adicionar funcionalidade de arrasto
  nodeGroups.call(d3.drag()
    .on('start', dragstarted)
    .on('drag', dragged)
    .on('end', dragended))
  
  // Adicionar tooltip ao passar o mouse
  nodeGroups.append('title')
    .text(d => `${d.name}\nStatus: ${d.status}\nApdex: ${d.metrics.apdex.toFixed(2)}\nResp Time: ${d.metrics.response_time.toFixed(1)}ms\nErro: ${(d.metrics.error_rate * 100).toFixed(2)}%`)
  
  // Função de atualização da simulação
  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y)
    
    nodeGroups.attr('transform', d => `translate(${d.x},${d.y})`)
  })
  
  // Funções para o arrasto dos nós
  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart()
    d.fx = d.x
    d.fy = d.y
  }
  
  function dragged(event, d) {
    d.fx = event.x
    d.fy = event.y
  }
  
  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0)
    d.fx = null
    d.fy = null
  }
}

// Observar mudanças nos dados da topologia e na aba ativa para renderizar o gráfico
watch(
  [() => topologyData.value, () => activeTab.value],
  () => {
    if (activeTab.value === 'topology') {
      // Aguardar um pequeno delay para garantir que o DOM foi atualizado
      setTimeout(() => {
        renderTopologyGraph()
      }, 100)
    }
  },
  { deep: true }
)

// Inicializar a página
onMounted(() => {
  fetchData()
  
  // Adicionar listener para redimensionamento da janela
  window.addEventListener('resize', () => {
    if (activeTab.value === 'topology') {
      renderTopologyGraph()
    }
  })
})
</script>
