/**
 * Servico centralizado para requisicoes relacionadas a dados avancados
 */
import apiClient from './axios';

const BASE_URL = '/avancado';
const STATUS_URL = '/status';

const advancedDataService = {
  /**
   * Verifica se o sistema esta usando dados reais
   */
  async checkIfUsingRealData() {
    try {
      const response = await apiClient.get(`${STATUS_URL}/data_source`);
      console.log('Status dos dados:', response.data);
      return response.data?.using_real_data === true;
    } catch (error) {
      console.error('Erro ao verificar status dos dados:', error);
      return true; // Assumir dados reais por padrão
    }
  },

  /**
   * Força a atualização de todos os dados
   */
  async refreshAllData() {
    console.log('Forçando atualização de todos os dados...');
    try {
      const [kubernetes, infraestrutura, topologia] = await Promise.all([
        this.getKubernetesData(),
        this.getInfrastructureData(),
        this.getTopologyData()
      ]);

      return {
        kubernetes,
        infraestrutura,
        topologia,
        refreshedAt: new Date().toISOString()
      };
    } catch (error) {
      console.error('Erro ao atualizar dados:', error);
      throw error;
    }
  },

  /**
   * Obtem dados de métricas do Kubernetes
   */
  async getKubernetesData() {
    const response = await apiClient.get(`${BASE_URL}/kubernetes`);
    return response.data;
  },

  /**
   * Obtem dados de infraestrutura
   */
  async getInfrastructureData() {
    const response = await apiClient.get(`${BASE_URL}/infraestrutura`);
    return response.data;
  },

  /**
   * Obtem dados de topologia
   */
  async getTopologyData() {
    const response = await apiClient.get(`${BASE_URL}/topologia`);
    return response.data;
  },

  /**
   * Obtem status geral do sistema
   */
  async getSystemStatus() {
    try {
      const [health, dataSource] = await Promise.all([
        apiClient.get(`${STATUS_URL}/health`),
        apiClient.get(`${STATUS_URL}/data_source`)
      ]);

      return {
        health: health.data?.status === 'OK',
        usingRealData: dataSource.data?.using_real_data === true,
        lastUpdate: dataSource.data?.timestamp,
        source: dataSource.data?.source
      };
    } catch (error) {
      console.error('Erro ao obter status do sistema:', error);
      return {
        health: false,
        usingRealData: true,
        error: error.message
      };
    }
  }
}

export default advancedDataService;
