// Arquivo removido: componente não será mais utilizado
          <div class="text-xs text-purple-300">Conexões</div>
          <div class="text-2xl font-bold text-white">{{ data?.summary?.total_connections || 0 }}</div>
        </div>
        <div>
          <div class="text-xs text-purple-300">Saúde Geral</div>
          <div class="text-2xl font-bold text-green-400">{{ data?.summary?.health_score || 0 }}%</div>
        </div>
        <div>
          <div class="text-xs text-purple-300">Latência Média</div>
          <div class="text-2xl font-bold text-white">{{ data?.summary?.avg_latency || 0 }} ms</div>
        </div>
      </div>
    </div>
    
    <!-- Visualização da Topologia -->
    <div class="bg-gray-900 rounded-xl p-6 shadow-lg">
      <h3 class="text-lg font-bold text-white mb-4">Visualização da Topologia</h3>
      <div id="topology-graph" ref="graphContainer" class="h-[600px] w-full bg-gray-800 rounded-lg"></div>
    </div>
    
    <!-- Detalhes dos Serviços -->
    <div class="bg-gray-900 rounded-xl p-6 shadow-lg">
      <h3 class="text-lg font-bold text-white mb-4">Serviços</h3>
      <div class="overflow-x-auto">
        <table v-if="data?.services && data.services.length > 0" class="w-full text-sm text-left text-gray-300">
          <thead class="text-xs text-gray-400 uppercase bg-gray-800">
            <tr>
              <th class="px-4 py-3">Nome</th>
              <th class="px-4 py-3">Tipo</th>
              <th class="px-4 py-3">Chamadas</th>
              <th class="px-4 py-3">Latência</th>
              <th class="px-4 py-3">Erro</th>
              <th class="px-4 py-3">Dependências</th>
              <th class="px-4 py-3">Saúde</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="service in data.services" :key="service.id" class="border-b border-gray-800">
              <td class="px-4 py-3 font-medium text-white">{{ service.name }}</td>
              <td class="px-4 py-3">{{ service.type }}</td>
              <td class="px-4 py-3">{{ service.calls_per_minute }} rpm</td>
              <td class="px-4 py-3">{{ service.avg_latency }} ms</td>
              <td class="px-4 py-3">{{ service.error_rate }}%</td>
              <td class="px-4 py-3">{{ service.dependencies?.length || 0 }}</td>
              <td class="px-4 py-3">
                <span class="px-2 py-1 rounded-full text-xs"
                  :class="{
                    'bg-green-900 text-green-300': service.health > 90,
                    'bg-yellow-900 text-yellow-300': service.health > 70 && service.health <= 90,
                    'bg-red-900 text-red-300': service.health <= 70
                  }">
                  {{ service.health }}%
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="text-center py-4 text-gray-400">
          Nenhum serviço encontrado
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';

const props = defineProps({
  data: {
    type: Object,
    default: () => ({})
  }
});

// Referência para o container do gráfico
const graphContainer = ref(null);

// Inicializar o gráfico quando os dados estiverem disponíveis
watch(() => props.data, (newData) => {
  if (newData && newData.services && graphContainer.value) {
    // Aqui você chamaria a função para renderizar o gráfico
    console.log('Dados de topologia disponíveis para renderização');
  }
}, { immediate: true });

// Lifecycle hooks
onMounted(() => {
  // Se os dados já estiverem disponíveis na montagem
  if (props.data && props.data.services && graphContainer.value) {
    // Aqui você chamaria a função para renderizar o gráfico
    console.log('Montando gráfico de topologia');
  }
});

onUnmounted(() => {
  // Limpar qualquer recurso do gráfico ao desmontar o componente
  console.log('Limpando recursos do gráfico de topologia');
});
</script>
