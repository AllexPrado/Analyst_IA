import axios from 'axios'

const api = axios.create({
  baseURL: '/api', // Usa o proxy configurado no vite.config.js para direcionar para http://localhost:8000
  timeout: 90000, // Aumentado para 90 segundos para permitir respostas da IA
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

export const getResumoGeral = () => api.get('/resumo-geral')
export const getStatus = () => api.get('/status')
export const getKPIs = () => api.get('/kpis')
export const getCobertura = () => api.get('/cobertura')
export const getTendencias = () => api.get('/tendencias')
export const getInsights = () => api.get('/insights')
export const getChatResposta = (pergunta) => api.post('/chat', { pergunta: pergunta })
export const getEntidades = () => api.get('/entidades')
export const atualizarCacheAPI = () => api.post('/cache/atualizar')
export const atualizarCacheAvancadoAPI = () => api.post('/cache/atualizar_avancado')
export const getDiagnosticoCache = () => api.get('/cache/diagnostico')
export const getHealth = () => api.get('/health')
export const resetTokenLimits = () => api.post('/limits/reset')

export default api
