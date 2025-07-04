import axios from 'axios';

// Cria uma instância do axios com configurações base para a API
const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api',  // Apontando para o backend na porta 8000
  timeout: 15000, // Timeout aumentado para 15 segundos
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Interceptor para logs de requisições (útil para debugging)
apiClient.interceptors.request.use(config => {
  console.log(`Requisição para: ${config.url}`);
  return config;
});

// Interceptor para tratamento de erros
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response) {
      console.error(`Erro ${error.response.status}: ${error.response.data.detail || error.response.statusText}`);
    } else if (error.request) {
      console.error('Erro de conexão com o servidor. Verifique se o backend está rodando.');
    } else {
      console.error('Erro:', error.message);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
