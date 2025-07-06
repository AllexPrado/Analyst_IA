<template>
  <div class="py-8">
    <h2 class="text-2xl font-bold text-blue-400 mb-6">Diagnóstico Completo do Sistema</h2>
    <div v-if="loading" class="text-gray-400">Carregando diagnóstico...</div>
    <div v-else-if="!diagnosticoCompleto" class="text-gray-400">Nenhum diagnóstico completo encontrado.</div>
    <div v-else>
      <div class="bg-gray-900 rounded-xl shadow-lg p-6 text-white">
        <h3 class="text-xl font-semibold text-blue-300 mb-2">Resumo</h3>
        <p class="mb-4">{{ diagnosticoCompleto }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getEntidades } from '../../api/backend.js'

const diagnosticoCompleto = ref('')
const loading = ref(true)

onMounted(async () => {
  loading.value = true
  try {
    const entidades = await getEntidades()
    // Busca o campo diagnosticoCompleto na primeira entidade que possuir
    let found = ''
    if (Array.isArray(entidades)) {
      for (const ent of entidades) {
        if (ent.diagnosticoCompleto) {
          found = ent.diagnosticoCompleto
          break
        }
      }
    }
    diagnosticoCompleto.value = found
  } catch (e) {
    diagnosticoCompleto.value = ''
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
</style>
