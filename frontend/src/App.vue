<template>
  <div class="dark bg-gray-900 text-white min-h-screen">
    <!-- Navegação Superior -->
    <nav class="flex items-center justify-between px-8 py-4 shadow bg-gradient-to-r from-gray-900 to-gray-800">
      <div class="flex items-center gap-8">
        <span class="text-2xl font-extrabold tracking-tight text-white">Analyst IA</span>
        <router-link v-for="item in menu" :key="item.path" :to="item.path" class="px-4 py-2 rounded-lg font-semibold transition-all"
          :class="[$route.path === item.path ? 'bg-white/20 text-yellow-300 shadow' : 'text-white hover:bg-white/10']">
          <font-awesome-icon :icon="item.icon" class="mr-2"/>
          {{ item.label }}
        </router-link>
      </div>
    </nav>
    <!-- Conteúdo -->
    <main class="max-w-7xl mx-auto px-4 py-8">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
const $route = useRoute()
const menu = [
  { path: '/', label: 'Visão Geral', icon: ['fas', 'chart-bar'] },
  { path: '/cobertura', label: 'Cobertura', icon: ['fas', 'shield-alt'] },
  { path: '/kpis', label: 'KPIs', icon: ['fas', 'chart-line'] },
  { path: '/tendencias', label: 'Tendências', icon: ['fas', 'wave-square'] },
  { path: '/insights', label: 'Insights', icon: ['fas', 'lightbulb'] },
  { path: '/chat', label: 'Chat IA', icon: ['fas', 'comments'] },
]
</script>

<style>
body.dark {
  background: #181c24;
  color: #fff;
}
</style>