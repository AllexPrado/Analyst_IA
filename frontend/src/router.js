import { createRouter, createWebHistory } from 'vue-router'
import VisaoGeral from './components/pages/VisaoGeral.vue'
import Cobertura from './components/pages/Cobertura.vue'
import Kpis from './components/pages/Kpis.vue'
import Tendencias from './components/pages/Tendencias.vue'
import Insights from './components/pages/Insights.vue'
import CoreInteligentePanel from './components/CoreInteligentePanel.vue'
import ChatPanel from './components/ChatPanel.vue'

import DiagnosticoCompleto from './components/pages/DiagnosticoCompleto.vue'
import Relacionamentos from './components/pages/Relacionamentos.vue'

const routes = [
  { path: '/', name: 'VisaoGeral', component: VisaoGeral },
  { path: '/cobertura', name: 'Cobertura', component: Cobertura },
  { path: '/kpis', name: 'KPIs', component: Kpis },
  { path: '/tendencias', name: 'Tendencias', component: Tendencias },
  { path: '/insights', name: 'Insights', component: Insights },
  { path: '/diagnostico', name: 'DiagnosticoCompleto', component: DiagnosticoCompleto },
  { path: '/relacionamentos', name: 'Relacionamentos', component: Relacionamentos },
  { path: '/core-inteligente', name: 'CoreInteligente', component: CoreInteligentePanel },
  { path: '/chat', name: 'ChatIA', component: ChatPanel },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
