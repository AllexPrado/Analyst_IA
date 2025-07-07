import { createRouter, createWebHistory } from 'vue-router'
import ExecutiveDashboard from './components/pages/ExecutiveDashboard.vue'
import OperationalDashboard from './components/pages/OperationalDashboard.vue'
import ChatIA from './components/ChatPanel.vue'

const routes = [
  { path: '/', name: 'Executive', component: ExecutiveDashboard },
  { path: '/operational', name: 'Operational', component: OperationalDashboard },
  { path: '/chat', name: 'ChatIA', component: ChatIA },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
