import axios from 'axios'

const api = axios.create({
  baseURL: '/api', // Usa o proxy configurado no vite.config.js para direcionar para http://localhost:8000
  timeout: 90000, // Aumentado para 90 segundos para permitir respostas da IA
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// Função utilitária para tratar respostas e erros
const handleApiResponse = async (promise) => {
  try {
    const response = await promise
    if (response.data && response.data.erro) {
      // Backend retornou erro explícito
      return { erro: true, mensagem: response.data.mensagem || 'Dados indisponíveis no momento.' }
    }
    return response.data
  } catch (error) {
    // Erro de rede, timeout ou backend fora
    return { erro: true, mensagem: error?.response?.data?.mensagem || 'Erro ao acessar dados do backend.' }
  }
}

export const getResumoGeral = () => handleApiResponse(api.get('/resumo-geral'))
export const getStatus = () => handleApiResponse(api.get('/status'))
export const getKPIs = () => handleApiResponse(api.get('/kpis'))
export const getCobertura = () => handleApiResponse(api.get('/cobertura'))
export const getTendencias = () => handleApiResponse(api.get('/tendencias'))
export const getInsights = () => handleApiResponse(api.get('/insights'))
export const getChatResposta = (pergunta) => handleApiResponse(api.post('/chat', { pergunta: pergunta }))
export const getEntidades = () => handleApiResponse(api.get('/entidades'))
export const atualizarCacheAPI = () => handleApiResponse(api.post('/cache/atualizar'))
export const atualizarCacheAvancadoAPI = () => handleApiResponse(api.post('/cache/atualizar_avancado'))
export const getDiagnosticoCache = () => handleApiResponse(api.get('/cache/diagnostico'))
export const getHealth = () => handleApiResponse(api.get('/health'))
export const resetTokenLimits = () => handleApiResponse(api.post('/limits/reset'))

export default api
