
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
            <tr v-for="cluster in data.clusters" :key="cluster.name" class="border-b border-gray-800">
              <td class="px-4 py-3">{{ cluster.name }}</td>
              <td class="px-4 py-3">{{ cluster.version }}</td>
              <td class="px-4 py-3">{{ cluster.nodes }}</td>
              <td class="px-4 py-3">{{ cluster.pods }}</td>
              <td class="px-4 py-3">{{ cluster.resource_usage?.cpu || 0 }}%</td>
              <td class="px-4 py-3">{{ cluster.resource_usage?.memory || 0 }}%</td>
              <td class="px-4 py-3">
                <span class="px-2 py-1 rounded-full text-xs"
                  :class="cluster.health === 'healthy' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'">
                  {{ cluster.health === 'healthy' ? 'Healthy' : 'Issues' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="text-center py-4 text-gray-400">
          Nenhum cluster encontrado
        </div>
      </div>
    </div>
    
    <!-- Nodes -->
    <div class="bg-gray-900 rounded-xl p-6 shadow-lg">
      <h3 class="text-lg font-bold text-white mb-4">Nodes</h3>
      <div v-if="data?.nodes && data.nodes.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="node in data.nodes" :key="node.name" 
          class="bg-gray-800 rounded-lg p-4 border-l-4"
          :class="node.health === 'healthy' ? 'border-green-500' : 'border-red-500'">
          <div class="flex justify-between items-start mb-2">
            <span class="font-medium text-white">{{ node.name }}</span>
            <span class="px-2 py-1 rounded-full text-xs"
              :class="node.health === 'healthy' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'">
              {{ node.health === 'healthy' ? 'Healthy' : 'Issues' }}
            </span>
          </div>
          <div class="grid grid-cols-2 gap-2 text-xs text-gray-400">
            <div>
              <div>CPU</div>
              <div class="text-white">{{ node.resource_usage?.cpu || 0 }}%</div>
            </div>
            <div>
              <div>Memory</div>
              <div class="text-white">{{ node.resource_usage?.memory || 0 }}%</div>
            </div>
            <div>
              <div>Pods</div>
              <div class="text-white">{{ node.pods }}</div>
            </div>
            <div>
              <div>Cluster</div>
              <div class="text-white">{{ node.cluster }}</div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="text-center py-4 text-gray-400">
        Nenhum node encontrado
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
</script>
