import axios from 'axios';

// Cria uma instância do axios com configurações base para a API
const apiClient = axios.create({
  baseURL: '/api',
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

// Interceptor para logs de respostas e tratamento de erros
apiClient.interceptors.response.use(
  response => {
    return response;
  },
  error => {
    if (error.response) {
      // O servidor respondeu com um status de erro
      console.error(`Erro ${error.response.status}: ${error.response.statusText}`);
      console.error('Dados do erro:', error.response.data);
    } else if (error.request) {
      // A requisição foi feita mas não houve resposta
      console.error('Sem resposta do servidor:', error.request);
    } else {
      // Erro na configuração da requisição
      console.error('Erro de configuração:', error.message);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
