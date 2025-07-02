/**
 * Servico centralizado para requisicoes relacionadas a dados avancados
 * Este servico encapsula todas as chamadas de API para os endpoints avancados,
 * fornecendo uma interface limpa e consistente para os componentes Vue.
 */

import apiClient from './axios';

const BASE_URL = '/avancado';

// Objeto para armazenar respostas em cache da memoria (opcional)
const responseCache = {
  kubernetes: null,
  infraestrutura: null,
  topologia: null,
  cacheTimestamp: null,
  // Tempo de expiracao do cache em milissegundos (5 minutos)
  CACHE_DURATION: 5 * 60 * 1000
};

/**
 * Verifica se o cache esta valido
 * @returns {boolean} - true se o cache estiver valido, false caso contrario
 */
const isCacheValid = () => {
  if (!responseCache.cacheTimestamp) return false;
  const now = Date.now();
  return (now - responseCache.cacheTimestamp) < responseCache.CACHE_DURATION;
};

const advancedDataService = {
  /**
   * Verifica se o sistema esta usando dados reais
   * @returns {Promise<boolean>} - Promise que resolve para true se estiver usando dados reais
   */
  checkIfUsingRealData() {
    // Verificar o indicador no backend
    return apiClient.get('/status/data_source')
      .then(response => {
        console.log('Status dos dados:', response.data);
        return response.data?.using_real_data === true;
      })
      .catch(error => {
        console.warn('Erro ao verificar status dos dados:', error);
        // Tentar verificar pelo indicador local
        return fetch('/status/using_real_data.json')
          .then(res => res.json())
          .then(data => data?.using_real_data === true)
          .catch(() => false);
      });
  },

  /**
   * Obtem dados de kubernetes
   * @param {boolean} useCache - Se deve usar o cache quando disponivel
   * @returns {Promise} - Promise com os dados de kubernetes
   */
  getKubernetesData(useCache = true) {
    if (useCache && responseCache.kubernetes && isCacheValid()) {
      console.log('Usando cache para dados de Kubernetes');
      return Promise.resolve(responseCache.kubernetes);
    }
    
    return apiClient.get(`${BASE_URL}/kubernetes`)
      .then(response => {
        responseCache.kubernetes = response.data;
        responseCache.cacheTimestamp = Date.now();
        return response.data;
      });
  },
  
  /**
   * Obtem dados detalhados de infraestrutura
   * @param {boolean} useCache - Se deve usar o cache quando disponivel
   * @returns {Promise} - Promise com os dados de infraestrutura
   */
  getInfrastructureData(useCache = true) {
    if (useCache && responseCache.infraestrutura && isCacheValid()) {
      console.log('Usando cache para dados de Infraestrutura');
      return Promise.resolve(responseCache.infraestrutura);
    }
    
    return apiClient.get(`${BASE_URL}/infraestrutura`)
      .then(response => {
        responseCache.infraestrutura = response.data;
        responseCache.cacheTimestamp = Date.now();
        return response.data;
      });
  },
  
  /**
   * Obtem dados de topologia de servicos
   * @param {boolean} useCache - Se deve usar o cache quando disponivel
   * @returns {Promise} - Promise com os dados de topologia
   */
  getTopologyData(useCache = true) {
    if (useCache && responseCache.topologia && isCacheValid()) {
      console.log('Usando cache para dados de Topologia');
      return Promise.resolve(responseCache.topologia);
    }
    
    return apiClient.get(`${BASE_URL}/topologia`)
      .then(response => {
        responseCache.topologia = response.data;
        responseCache.cacheTimestamp = Date.now();
        return response.data;
      });
  },
  
  /**
   * Obtem todos os dados avancados de uma vez
   * @returns {Promise} - Promise com todos os dados avancados
   */
  getAllAdvancedData(forceRefresh = false) {
    // Limpar cache se forceRefresh for true
    if (forceRefresh) {
      this.clearCache();
    }
    
    // Verificar se estamos usando dados reais
    return this.checkIfUsingRealData().then(usingRealData => {
      if (usingRealData) {
        console.log('📊 Usando DADOS REAIS do New Relic');
        // Forçar refresh se estiver usando dados reais
        forceRefresh = true;
      } else {
        console.log('📊 Usando dados simulados');
      }
      
      // Continuar com a chamada normal
      return Promise.all([
        this.getKubernetesData(!usingRealData),
        this.getInfrastructureData(!usingRealData),
        this.getTopologyData(!usingRealData)
      ]).then(([kubernetes, infraestrutura, topologia]) => {
        return { kubernetes, infraestrutura, topologia };
      });
    });
  },
  
  /**
   * Limpa o cache de dados
   */
  clearCache() {
    responseCache.kubernetes = null;
    responseCache.infraestrutura = null;
    responseCache.topologia = null;
    responseCache.cacheTimestamp = null;
    console.log('Cache de dados avançados limpo');
  }
};

export default advancedDataService;
