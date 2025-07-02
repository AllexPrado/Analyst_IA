import { createRouter, createWebHistory } from 'vue-router'
import VisaoGeral from './components/pages/VisaoGeral.vue'
import Cobertura from './components/pages/Cobertura.vue'
import Kpis from './components/pages/Kpis.vue'
import Tendencias from './components/pages/Tendencias.vue'
import Insights from './components/pages/Insights.vue'
import InfraAvancada from './components/pages/InfraAvancada.vue'
import CoreInteligentePanel from './components/CoreInteligentePanel.vue'
import ChatPanel from './components/ChatPanel.vue'

const routes = [
  { path: '/', name: 'VisaoGeral', component: VisaoGeral },
  { path: '/cobertura', name: 'Cobertura', component: Cobertura },
  { path: '/kpis', name: 'KPIs', component: Kpis },
  { path: '/tendencias', name: 'Tendencias', component: Tendencias },
  { path: '/insights', name: 'Insights', component: Insights },
  { path: '/infraestrutura-avancada', name: 'InfraAvancada', component: InfraAvancada },
  { path: '/core-inteligente', name: 'CoreInteligente', component: CoreInteligentePanel },
  { path: '/chat', name: 'ChatIA', component: ChatPanel },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
