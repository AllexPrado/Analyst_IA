// Utilitários para validação e tratamento de dados da API
// Valida se os dados recebidos da API são válidos
export const validateApiData = (data, expectedType = 'object') => {
  if (!data) return false
  
  // Se há um erro explícito na resposta
  if (data.erro) return false
  
  // Valida tipo esperado
  switch (expectedType) {
    case 'array':
      return Array.isArray(data)
    case 'object':
      return typeof data === 'object' && !Array.isArray(data)
    case 'number':
      return typeof data === 'number' && !isNaN(data)
    case 'string':
      return typeof data === 'string' && data.length > 0
    default:
      return data !== null && data !== undefined
  }
}

// Sanitiza dados para exibição segura
export const sanitizeApiData = (data, fallback = 'N/A') => {
  if (data === null || data === undefined || data === '') {
    return fallback
  }
  
  if (typeof data === 'number' && isNaN(data)) {
    return fallback
  }
  
  return data
}

// Formata timestamps para exibição
export const formatTimestamp = (timestamp, fallback = 'Não disponível') => {
  if (!timestamp) return fallback
  
  try {
    const date = new Date(timestamp)
    if (isNaN(date.getTime())) return fallback
    
    return date.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return fallback
  }
}

// Extrai métricas de forma segura
export const extractMetrics = (data, metricPath, fallback = 0) => {
  if (!data || typeof data !== 'object') return fallback
  
  const keys = metricPath.split('.')
  let current = data
  
  for (const key of keys) {
    if (current === null || current === undefined || typeof current !== 'object') {
      return fallback
    }
    current = current[key]
  }
  
  return sanitizeApiData(current, fallback)
}

// Calcula porcentagem de forma segura
export const calculatePercentage = (value, total, fallback = 0) => {
  if (!value || !total || total === 0) return fallback
  
  const percentage = (value / total) * 100
  return isNaN(percentage) ? fallback : Math.round(percentage * 100) / 100
}

// Determina status de saúde baseado em métricas
export const determineHealthStatus = (metrics) => {
  if (!metrics || typeof metrics !== 'object') {
    return { status: 'unknown', color: 'gray', description: 'Status desconhecido' }
  }
  
  const { erros = 0, alertas = 0, disponibilidade = 100 } = metrics
  
  if (erros > 0) {
    return { 
      status: 'critical', 
      color: 'red', 
      description: `${erros} erro(s) crítico(s) detectado(s)` 
    }
  }
  
  if (alertas > 0) {
    return { 
      status: 'warning', 
      color: 'yellow', 
      description: `${alertas} alerta(s) ativo(s)` 
    }
  }
  
  if (disponibilidade >= 99) {
    return { 
      status: 'healthy', 
      color: 'green', 
      description: 'Sistema operacional' 
    }
  }
  
  if (disponibilidade >= 95) {
    return { 
      status: 'degraded', 
      color: 'yellow', 
      description: 'Performance degradada' 
    }
  }
  
  return { 
    status: 'critical', 
    color: 'red', 
    description: 'Sistema com problemas graves' 
  }
}

// Wrapper para chamadas de API com tratamento de erro consistente
export const safeApiCall = async (apiFunction, fallbackData = null) => {
  try {
    const result = await apiFunction()
    
    if (result && result.erro) {
      console.warn('API retornou erro:', result.mensagem)
      return { error: true, message: result.mensagem, data: fallbackData }
    }
    
    return { error: false, data: result }
  } catch (error) {
    console.error('Erro na chamada da API:', error)
    return { 
      error: true, 
      message: error.message || 'Erro de comunicação com o backend', 
      data: fallbackData 
    }
  }
}
