import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api', // Aponta diretamente para o backend real
  timeout: 90000, // Aumentado para 90 segundos para permitir respostas da IA
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})
// Novo endpoint: dados avançados por entidade
export const getDadosAvancadosEntidade = (guid, period = '7d') =>
  handleApiResponse(api.get(`/entidade/${guid}/dados_avancados?period=${period}`))

// Função utilitária para tratar respostas e erros
const handleApiResponse = async (promise) => {
  try {
    const response = await promise
    if (response.data && response.data.erro) {
      // Backend retornou erro explícito
      console.warn('Backend retornou erro:', response.data.mensagem)
      return { erro: true, mensagem: response.data.mensagem || 'Dados indisponíveis no momento.' }
    }
    return response.data
  } catch (error) {
    // Erro de rede, timeout ou backend fora
    console.error('Erro na API:', error)
    
    // Se é erro de conexão (backend não está rodando)
    if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED') {
      return { erro: true, mensagem: 'Backend não está em execução. Inicie o backend na porta 8000.' }
    }
    
    if (error.code === 'ECONNABORTED') {
      return { erro: true, mensagem: 'Timeout na requisição. Tente novamente.' }
    }
    if (error.response?.status === 404) {
      return { erro: true, mensagem: 'Endpoint não encontrado no backend.' }
    }
    if (error.response?.status === 500) {
      return { erro: true, mensagem: 'Erro interno do servidor. Verifique os logs do backend.' }
    }
    return { erro: true, mensagem: error?.response?.data?.mensagem || 'Erro ao acessar dados do backend.' }
  }
}

export const getResumoGeral = () => handleApiResponse(api.get('/resumo-geral'))
export const getStatus = () => handleApiResponse(api.get('/status'))
export const getKPIs = () => handleApiResponse(api.get('/kpis'))
export const getCobertura = () => handleApiResponse(api.get('/cobertura'))
export const getTendencias = () => handleApiResponse(api.get('/tendencias'))
export const getInsights = () => handleApiResponse(api.get('/insights'))
// Novo: aceita objeto completo (mensagem, session_id, perfil, contexto)
export const getChatResposta = ({ mensagem, session_id, perfil, contexto }) =>
  handleApiResponse(api.post('/chat', { mensagem, session_id, perfil, contexto }))
export const getEntidades = () => handleApiResponse(api.get('/entidades'))
export const atualizarCacheAPI = () => handleApiResponse(api.post('/cache/atualizar'))
export const atualizarCacheAvancadoAPI = () => handleApiResponse(api.post('/cache/atualizar_avancado'))
export const getDiagnosticoCache = () => handleApiResponse(api.get('/cache/diagnostico'))
export const getHealth = () => handleApiResponse(api.get('/health'))
export const resetTokenLimits = () => handleApiResponse(api.post('/limits/reset'))
export const getLogs = () => handleApiResponse(api.get('/logs'))
export const getAlertas = () => handleApiResponse(api.get('/alertas'))
export const getDashboards = () => handleApiResponse(api.get('/dashboards'))
export const getIncidentes = () => handleApiResponse(api.get('/incidentes'))

export default api
