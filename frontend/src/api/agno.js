// Resetar limite de tokens (equivalente ao /limits/reset)
export const resetTokenLimits = async () => {
  try {
    const response = await agnoApi.post('/limits/reset');
    return response.data;
  } catch (error) {
    if (error.response) {
      return { erro: true, mensagem: error.response.data?.mensagem || 'Erro ao resetar limite de tokens.' };
    }
    return { erro: true, mensagem: error.message || 'Erro desconhecido ao resetar limite.' };
  }
};
import axios from 'axios';

const agnoApi = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});


// Chat endpoint: envia mensagem e recebe resposta contextualizada
export const enviarMensagemChat = async ({ mensagem, session_id, perfil, contexto }) => {
  if (!mensagem) throw new Error('Campo "mensagem" é obrigatório!');
  if (!session_id) throw new Error('Campo "session_id" é obrigatório!');
  if (!perfil) throw new Error('Campo "perfil" é obrigatório!');
  try {
    const payload = { mensagem, session_id, perfil };
    if (contexto) payload.contexto = contexto;
    const response = await agnoApi.post('/agno/chat', payload);
    return response.data;
  } catch (error) {
    if (error.response) {
      return { erro: true, mensagem: error.response.data?.mensagem || 'Erro ao acessar dados do backend.' };
    }
    if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED') {
      return { erro: true, mensagem: 'Backend não está em execução. Inicie o backend na porta 8000.' };
    }
    if (error.code === 'ECONNABORTED') {
      return { erro: true, mensagem: 'Timeout na requisição. Tente novamente.' };
    }
    return { erro: true, mensagem: error.message || 'Erro desconhecido ao acessar o backend.' };
  }
};

// 1. Gerar Relatório
export const gerarRelatorio = ({ tipo, filtro }) => {
  if (!tipo) throw new Error('Campo "tipo" é obrigatório!');
  return agnoApi.post('/agno/relatorio', { tipo, filtro });
};

// 2. Corrigir Entidade
export const corrigirEntidade = ({ entidade, acao = 'corrigir' }) => {
  if (!entidade) throw new Error('Campo "entidade" é obrigatório!');
  return agnoApi.post('/agno/corrigir', { entidade, acao });
};

// 3. Disparar Alerta
export const dispararAlerta = ({ mensagem, destino }) => {
  if (!mensagem) throw new Error('Campo "mensagem" é obrigatório!');
  return agnoApi.post('/agno/alerta', { mensagem, destino });
};

// 4. Consultar Histórico
export const consultarHistorico = ({ session_id, limite }) => {
  if (!session_id) throw new Error('Campo "session_id" é obrigatório!');
  return agnoApi.get(`/agno/historico?session_id=${session_id}${limite ? `&limite=${limite}` : ''}`);
};

// 5. Analisar Intenção
export const analisarIntencao = ({ texto }) => {
  if (!texto) throw new Error('Campo "texto" é obrigatório!');
  return agnoApi.post('/agno/intencao', { texto });
};

// 6. Executar Playbook
export const executarPlaybook = ({ nome, contexto }) => {
  if (!nome) throw new Error('Campo "nome" é obrigatório!');
  return agnoApi.post('/agno/playbook', { nome, contexto });
};

// 7. Executar Ação Plugável
export const executarAcao = ({ acao }) => {
  if (!acao) throw new Error('Campo "acao" é obrigatório!');
  return agnoApi.post('/agno/acao', { acao });
};

// 8. Correlacionar Eventos
export const correlacionarEventos = ({ eventos }) => {
  if (!eventos || !Array.isArray(eventos)) throw new Error('Campo "eventos" deve ser uma lista!');
  return agnoApi.post('/agno/correlacionar', { eventos });
};

// 9. Consultar Contexto/Memória
export const consultarContexto = ({ session_id }) => {
  if (!session_id) throw new Error('Campo "session_id" é obrigatório!');
  return agnoApi.get(`/agno/contexto?session_id=${session_id}`);
};

// 10. Registrar Feedback
export const registrarFeedback = ({ feedback }) => {
  if (!feedback || !feedback.mensagem || !feedback.score) throw new Error('Feedback deve conter mensagem e score!');
  return agnoApi.post('/agno/feedback', { feedback });
};

// 11. Coletar Dados do New Relic
export const coletarNewRelic = ({ entidade, periodo, tipo }) => {
  if (!periodo || !tipo) throw new Error('Campos "periodo" e "tipo" são obrigatórios!');
  return agnoApi.post('/agno/coletar_newrelic', { entidade, periodo, tipo });
};

export default agnoApi;
