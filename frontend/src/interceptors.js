// Interceptores para melhorar o tratamento de erros do Axios
import axios from 'axios';

// Criar uma instância interceptora que pode ser usada em toda aplicação
export const setupAxiosInterceptors = () => {
  // Request interceptor - adiciona headers e tratamento comum
  axios.interceptors.request.use(
    (config) => {
      // Evitar requisições para domínios externos com cookies
      if (!config.url.startsWith('/api') && !config.url.startsWith('http://localhost')) {
        config.withCredentials = false;
      }
      return config;
    },
    (error) => {
      console.warn('Erro na requisição:', error);
      return Promise.reject(error);
    }
  );

  // Response interceptor - para tratamento global de erros
  axios.interceptors.response.use(
    (response) => {
      return response;
    },
    (error) => {
      // Tratamento específico para diferentes tipos de erros
      if (error.response) {
        // O servidor respondeu com status de erro
        console.warn(`Erro ${error.response.status} na resposta: ${error.response.statusText}`);
        
        // Tratamento específico para diferentes códigos de status
        switch (error.response.status) {
          case 401:
            console.warn('Erro de autenticação. O usuário precisa fazer login novamente.');
            break;
          case 403:
            console.warn('Acesso negado a este recurso.');
            break;
          case 404:
            console.warn('Recurso não encontrado.');
            break;
          case 500:
            console.warn('Erro interno do servidor.');
            break;
          default:
            console.warn('Erro na resposta do servidor.');
        }
      } else if (error.request) {
        // A requisição foi feita mas não houve resposta
        console.warn('Sem resposta do servidor:', error.request);
      } else {
        // Erro na configuração da requisição
        console.warn('Erro na configuração da requisição:', error.message);
      }
      
      // Propaga o erro para tratamento específico nos componentes
      return Promise.reject(error);
    }
  );
};

export default setupAxiosInterceptors;
