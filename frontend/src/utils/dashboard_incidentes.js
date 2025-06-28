// dashboard_incidentes.js
// Funções auxiliares para lidar com incidentes no Dashboard

import axios from 'axios'

/**
 * Busca incidentes e alertas da API
 * @returns {Promise} Resultado da consulta API
 */
export async function buscarIncidentes() {
  try {
    const response = await axios.get('/api/incidentes')
    return response.data
  } catch (error) {
    console.error('Erro ao buscar incidentes:', error)
    return {
      incidentes: [],
      alertas: [],
      resumo: {
        total_incidentes: 0,
        total_alertas: 0,
        incidentes_ativos: 0,
        incidentes_resolvidos: 0,
        severidade_critica: 0,
        severidade_warning: 0,
        severidade_info: 0
      }
    }
  }
}

/**
 * Formata a gravidade para exibição
 * @param {string} severidade - A severidade original (critical, warning, info)
 * @returns {Object} Objeto com texto, classe CSS e ícone
 */
export function formatarSeveridade(severidade) {
  const mapa = {
    critical: {
      texto: 'Crítico',
      classe: 'text-red-600 bg-red-100',
      icone: 'triangle-exclamation'
    },
    warning: {
      texto: 'Alerta',
      classe: 'text-yellow-600 bg-yellow-100',
      icone: 'exclamation-circle'
    },
    info: {
      texto: 'Informativo',
      classe: 'text-blue-600 bg-blue-100',
      icone: 'info-circle'
    }
  }
  
  return mapa[severidade] || {
    texto: 'Desconhecido',
    classe: 'text-gray-600 bg-gray-100',
    icone: 'question-circle'
  }
}

/**
 * Determina o status geral do sistema baseado nos incidentes
 * @param {Object} resumo - O resumo dos incidentes e alertas
 * @returns {Object} Objeto com texto, classe CSS, status e descrição
 */
export function determinarStatusGeral(resumo) {
  if (resumo.severidade_critica > 0) {
    return {
      texto: 'Crítico',
      classe: 'text-red-500',
      status: 'CRÍTICO',
      descricao: `${resumo.severidade_critica} incidente(s) crítico(s) em andamento`
    }
  } else if (resumo.incidentes_ativos > 0 || resumo.severidade_warning > 0) {
    return {
      texto: 'Alerta',
      classe: 'text-yellow-500',
      status: 'ALERTA',
      descricao: `${resumo.incidentes_ativos} incidente(s) em andamento`
    }
  } else {
    return {
      texto: 'OK',
      classe: 'text-green-500',
      status: 'OK',
      descricao: 'Todos os serviços operando normalmente'
    }
  }
}

/**
 * Formata uma data ISO para exibição amigável
 * @param {string} isoDate - A data em formato ISO
 * @returns {string} Data formatada para exibição
 */
export function formatarData(isoDate) {
  if (!isoDate) return 'Data não disponível'
  
  try {
    const data = new Date(isoDate)
    return data.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return 'Data inválida'
  }
}
