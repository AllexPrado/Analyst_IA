<template>
  <div class="apex-chart-safe-wrapper">
    <div v-if="!hasValidData" class="flex items-center justify-center h-full min-h-[200px] bg-gray-900/50 rounded-lg">
      <div class="text-center text-gray-400">
        <font-awesome-icon :icon="noDataIcon" class="text-3xl mb-2 opacity-50" />
        <p>{{ noDataMessage }}</p>
      </div>
    </div>
    <apexchart v-else
      :type="chartType"
      :height="height"
      :width="width"
      :options="safeOptions"
      :series="safeSeries"
    />
  </div>
</template>

<script>
import { computed, onMounted, watch } from 'vue';
import { 
  isValidSeries, 
  sanitizeSeries, 
  createSafeApexOptions, 
  createSafeApexSeries 
} from '../utils/nullDataHandler';

export default {
  name: 'SafeApexChart',
  props: {
    // Props do ApexChart
    type: {
      type: String,
      default: 'line'
    },
    height: {
      type: [String, Number],
      default: 300
    },
    width: {
      type: [String, Number],
      default: '100%'
    },
    options: {
      type: Object,
      default: () => ({})
    },
    series: {
      type: Array,
      default: () => []
    },
    // Props adicionais para segurança
    noDataMessage: {
      type: String,
      default: 'Sem dados disponíveis'
    },
    noDataIcon: {
      type: String,
      default: 'chart-bar'
    }
  },
  setup(props) {
    // Verifica se tem dados válidos
    const hasValidData = computed(() => {
      if (!props.series || !Array.isArray(props.series) || props.series.length === 0) {
        return false;
      }
      
      return props.series.some(serie => {
        if (!serie || !serie.data || !Array.isArray(serie.data)) {
          return false;
        }
        return serie.data.length > 0 && serie.data.some(val => val !== null && val !== undefined);
      });
    });
    
    // Cria séries seguras
    const safeSeries = computed(() => {
      return createSafeApexSeries(props.series);
    });
    
    // Cria opções seguras
    const safeOptions = computed(() => {
      return createSafeApexOptions(props.options);
    });
    
    // Tipo de gráfico
    const chartType = computed(() => {
      return props.type || 'line';
    });
    
    return {
      hasValidData,
      safeSeries,
      safeOptions,
      chartType
    };
  }
};
</script>

<style scoped>
.apex-chart-safe-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
}
</style>
