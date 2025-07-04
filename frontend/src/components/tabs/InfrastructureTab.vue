// Arquivo removido: componente não será mais utilizado
          <div class="text-xs text-blue-300">Memória Média</div>
          <div class="text-2xl font-bold text-white">{{ data?.summary?.avg_memory || 0 }}%</div>
        </div>
        <div>
          <div class="text-xs text-blue-300">Disponibilidade</div>
          <div class="text-2xl font-bold text-green-400">{{ data?.summary?.availability || 0 }}%</div>
        </div>
      </div>
    </div>
    
    <!-- Servidores -->
    <div class="bg-gray-900 rounded-xl p-6 shadow-lg">
      <h3 class="text-lg font-bold text-white mb-4">Servidores</h3>
      <div class="overflow-x-auto">
        <table v-if="data?.hosts && data.hosts.length > 0" class="w-full text-sm text-left text-gray-300">
          <thead class="text-xs text-gray-400 uppercase bg-gray-800">
            <tr>
              <th class="px-4 py-3">Hostname</th>
              <th class="px-4 py-3">Tipo</th>
              <th class="px-4 py-3">CPU</th>
              <th class="px-4 py-3">Memória</th>
              <th class="px-4 py-3">Disco</th>
              <th class="px-4 py-3">Uptime</th>
              <th class="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="host in data.hosts" :key="host.name" class="border-b border-gray-800">
              <td class="px-4 py-3">{{ host.name }}</td>
              <td class="px-4 py-3">{{ host.type }}</td>
              <td class="px-4 py-3">
                <div class="flex items-center">
                  <div class="w-24 bg-gray-700 rounded-full h-2.5 mr-2">
                    <div class="bg-blue-600 h-2.5 rounded-full" :style="{ width: `${host.cpu_usage}%` }"></div>
                  </div>
                  <span>{{ host.cpu_usage }}%</span>
                </div>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center">
                  <div class="w-24 bg-gray-700 rounded-full h-2.5 mr-2">
                    <div class="bg-green-600 h-2.5 rounded-full" :style="{ width: `${host.memory_usage}%` }"></div>
                  </div>
                  <span>{{ host.memory_usage }}%</span>
                </div>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center">
                  <div class="w-24 bg-gray-700 rounded-full h-2.5 mr-2">
                    <div class="bg-purple-600 h-2.5 rounded-full" :style="{ width: `${host.disk_usage}%` }"></div>
                  </div>
                  <span>{{ host.disk_usage }}%</span>
                </div>
              </td>
              <td class="px-4 py-3">{{ formatUptime(host.uptime) }}</td>
              <td class="px-4 py-3">
                <span class="px-2 py-1 rounded-full text-xs"
                  :class="host.status === 'online' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'">
                  {{ host.status === 'online' ? 'Online' : 'Offline' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="text-center py-4 text-gray-400">
          Nenhum servidor encontrado
        </div>
      </div>
    </div>
    
    <!-- Alertas de Performance -->
    <div class="bg-gray-900 rounded-xl p-6 shadow-lg">
      <h3 class="text-lg font-bold text-white mb-4">Alertas de Performance</h3>
      <div v-if="data?.alerts && data.alerts.length > 0" class="space-y-3">
        <div v-for="(alert, index) in data.alerts" :key="index" 
          class="bg-gray-800 p-4 rounded-lg border-l-4" 
          :class="{
            'border-red-500': alert.severity === 'critical',
            'border-yellow-500': alert.severity === 'warning',
            'border-blue-500': alert.severity === 'info'
          }">
          <div class="flex items-start justify-between">
            <div>
              <h4 class="font-bold text-white">{{ alert.title }}</h4>
              <p class="text-sm text-gray-400">{{ alert.description }}</p>
            </div>
            <span class="px-2 py-1 rounded-full text-xs"
              :class="{
                'bg-red-900 text-red-300': alert.severity === 'critical',
                'bg-yellow-900 text-yellow-300': alert.severity === 'warning',
                'bg-blue-900 text-blue-300': alert.severity === 'info'
              }">
              {{ alert.severity }}
            </span>
          </div>
          <div class="mt-2 flex justify-between text-xs text-gray-500">
            <span>{{ alert.host }}</span>
            <span>{{ formatDate(alert.timestamp) }}</span>
          </div>
        </div>
      </div>
      <div v-else class="text-center py-4 text-gray-400">
        Nenhum alerta de performance
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  data: {
    type: Object,
    default: () => ({})
  }
});

function formatUptime(seconds) {
  if (!seconds && seconds !== 0) return 'N/A';
  
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  let result = '';
  if (days > 0) result += `${days}d `;
  if (hours > 0) result += `${hours}h `;
  if (minutes > 0) result += `${minutes}m`;
  
  return result.trim() || '< 1m';
}

function formatDate(dateString) {
  if (!dateString) return 'N/A';
  return new Date(dateString).toLocaleString();
}
</script>
