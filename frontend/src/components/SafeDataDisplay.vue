<template>
  <div class="safe-data-container">
    <div v-if="hasData" class="data-content">
      <slot></slot>
    </div>
    <div v-else class="no-data-fallback">
      <div class="flex flex-col items-center justify-center p-6 h-full min-h-[120px]">
        <font-awesome-icon :icon="noDataIcon" class="text-3xl text-gray-400/60 mb-3" />
        <p class="text-gray-500 text-center">{{ noDataMessage }}</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SafeDataDisplay',
  props: {
    data: {
      type: [Object, Array, Number, String],
      default: null
    },
    noDataMessage: {
      type: String,
      default: 'Dados não disponíveis'
    },
    noDataIcon: {
      type: String,
      default: 'exclamation-circle'
    }
  },
  computed: {
    hasData() {
      if (this.data === null || this.data === undefined) return false;
      
      if (Array.isArray(this.data)) {
        return this.data.length > 0;
      } else if (typeof this.data === 'object') {
        return Object.keys(this.data).length > 0;
      }
      
      return true;
    }
  }
}
</script>

<style scoped>
.safe-data-container {
  width: 100%;
  height: 100%;
}

.no-data-fallback {
  width: 100%;
  height: 100%;
  background-color: rgba(243, 244, 246, 0.05);
  border-radius: 0.5rem;
}
</style>
