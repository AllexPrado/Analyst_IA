<template>
  <div class="py-8">
    <h2 class="text-2xl font-bold text-blue-400 mb-6">Relacionamentos entre Entidades</h2>
    <div v-if="loading" class="text-gray-400">Carregando relacionamentos...</div>
    <div v-else-if="!relationships.length" class="text-gray-400">Nenhum relacionamento encontrado.</div>
    <div v-else>
      <div class="overflow-x-auto">
        <table class="min-w-full text-sm text-left text-gray-300 border border-gray-700 my-2">
          <thead class="bg-gray-800">
            <tr>
              <th class="bg-gray-800 px-2 py-1 border-b border-gray-700">Entidade Origem</th>
              <th class="bg-gray-800 px-2 py-1 border-b border-gray-700">Entidade Relacionada</th>
              <th class="bg-gray-800 px-2 py-1 border-b border-gray-700">Tipo</th>
              <th class="bg-gray-800 px-2 py-1 border-b border-gray-700">Direção</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(rel, idx) in relationships" :key="idx">
              <td class="px-2 py-1 border-b border-gray-700">{{ rel.sourceName }}</td>
              <td class="px-2 py-1 border-b border-gray-700">{{ rel.name }}</td>
              <td class="px-2 py-1 border-b border-gray-700">{{ rel.type }}</td>
              <td class="px-2 py-1 border-b border-gray-700">{{ rel.direction }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getEntidades } from '../../api/backend.js'

const relationships = ref([])
const loading = ref(true)

onMounted(async () => {
  loading.value = true
  try {
    const entidades = await getEntidades()
    const rels = []
    if (Array.isArray(entidades)) {
      entidades.forEach(ent => {
        if (ent.dados_avancados && Array.isArray(ent.dados_avancados.relationships)) {
          ent.dados_avancados.relationships.forEach(rel => {
            rels.push({
              ...rel,
              sourceName: ent.name || ent.guid
            })
          })
        }
      })
    }
    relationships.value = rels
  } catch (e) {
    relationships.value = []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
</style>
