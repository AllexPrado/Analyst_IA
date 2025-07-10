<template>
  <div class="flex flex-col items-center justify-center min-h-screen bg-gray-900">
    <div class="w-full max-w-6xl mx-auto rounded-2xl shadow-2xl bg-gray-900 text-white p-0 md:p-6 flex flex-col h-screen">
      <!-- Filtro de período e ações globais -->
      <div class="flex flex-wrap gap-4 px-6 pt-6 pb-3 border-b border-gray-800 items-end">
        <div class="flex items-center">
          <font-awesome-icon icon="robot" class="text-blue-400 text-xl mr-3" />
          <h2 class="text-2xl font-bold">Chat IA - Painel Unificado</h2>
        </div>
        <div class="flex-1"></div>
        <div>
          <label class="block text-gray-300 text-xs mb-1">Período</label>
          <select v-model="periodoSelecionado" class="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white">
            <option value="24h">Últimas 24h</option>
            <option value="7d">Últimos 7 dias</option>
            <option value="30d">Últimos 30 dias</option>
          </select>
        </div>
        <div>
          <button class="bg-gray-800 hover:bg-gray-700 px-3 py-1 rounded-lg text-sm flex items-center" @click="carregarEntidades">
            <font-awesome-icon icon="sync" class="mr-2" />
            Atualizar entidades
          </button>
        </div>
        <div>
          <button class="bg-gray-800 hover:bg-gray-700 px-3 py-1 rounded-lg text-sm flex items-center" @click="limparConversa">
            <font-awesome-icon icon="trash" class="mr-2" />
            Limpar conversa
          </button>
        </div>
      </div>
      <p class="text-gray-400 text-sm mb-0 px-6">Análise completa: entidades, métricas, logs, incidentes, dashboards e alertas em tempo real</p>
      <div class="flex-1 overflow-y-auto px-4 py-4" ref="chatHistory" style="scroll-behavior: smooth;">
        <div v-if="mensagens.length === 0" class="flex flex-col items-center justify-center h-full text-gray-400">
          <font-awesome-icon icon="comment-dots" class="text-5xl mb-5 text-blue-400" />
          <p class="text-2xl mb-3 font-light">Converse com o Chat IA</p>
          <div class="max-w-lg">
            <p class="text-sm mb-6 text-center">Pergunte sobre métricas, logs, incidentes, dashboards, alertas e mais.</p>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
              <button 
                v-for="(sugestao, i) in sugestoesPredefinidas" 
                :key="i" 
                @click="selecionarSugestao(sugestao)"
                class="bg-gray-800 hover:bg-gray-700 px-4 py-3 rounded-xl text-left text-sm transition-all border border-gray-700">
                {{ sugestao }}
              </button>
            </div>
          </div>
        </div>
        <div v-for="(mensagem, index) in mensagens" :key="index" class="mb-4">
          <div v-if="mensagem.tipo === 'pergunta'" class="flex justify-end mb-4">
            <div class="flex items-start">
              <div class="bg-blue-700 text-white px-5 py-3 rounded-2xl max-w-[70%] shadow">
                <p class="text-white">{{ mensagem.texto }}</p>
                <div class="text-right mt-1">
                  <span class="text-xs text-blue-300">{{ mensagem.timestamp || 'Agora' }}</span>
                </div>
              </div>
              <div class="flex-shrink-0 ml-2 mt-1">
                <div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white">
                  <font-awesome-icon icon="user" />
                </div>
              </div>
            </div>
          </div>
          <div v-else class="flex mb-4">
            <div class="flex items-start w-full">
              <div class="flex-shrink-0 mr-2 mt-1">
                <div class="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center text-white">
                  <font-awesome-icon icon="robot" />
                </div>
              </div>
              <div :class="`px-5 py-3 rounded-2xl max-w-full w-full shadow ${mensagem.erro ? 'bg-red-900 border border-red-800' : 'bg-gray-700'}`">
                <div v-if="!mensagem.erro" class="text-white">
                  <div v-html="formatarResposta(mensagem.texto)"></div>
                  <!-- Botões de ação para casos especiais como limite de tokens -->
                  <div v-if="mensagem.mostrarBotoesAcao" class="mt-3 space-y-2">
                    <button @click="resetarLimiteTokens" 
                      class="block w-full bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded transition-colors text-sm">
                      🔄 Resetar limite de tokens
                    </button>
                    <button @click="limparConversa" 
                      class="block w-full bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded transition-colors text-sm">
                      🗑️ Limpar conversa e começar de novo
                    </button>
                  </div>
                </div>
                <p class="text-red-300 font-semibold" v-else>{{ mensagem.texto || 'Ocorreu um erro ao obter resposta do backend. Nenhum dado real disponível.' }}</p>
                <div class="text-right mt-1">
                  <span class="text-xs" :class="mensagem.erro ? 'text-red-200' : 'text-blue-300'">{{ mensagem.timestamp || 'Agora' }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <form @submit.prevent="enviarPergunta(pergunta)" class="flex gap-2 items-center px-6 py-4 border-t border-gray-800 bg-gray-900">
        <div class="relative flex-1">
          <input 
            v-model="pergunta" 
            placeholder="Digite sua pergunta..." 
            class="w-full px-4 py-4 pr-10 bg-gray-800 text-white border border-gray-700 rounded-2xl focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-base shadow-inner" 
            :disabled="carregando" 
          />
          <div v-if="pergunta.length > 0" class="absolute right-3 top-1/2 transform -translate-y-1/2">
            <button 
              type="button" 
              @click="pergunta = ''" 
              class="text-gray-400 hover:text-gray-300 p-1"
            >
              <font-awesome-icon icon="times-circle" />
            </button>
          </div>
        </div>
        <button 
          type="submit" 
          class="bg-blue-600 text-white px-6 py-4 rounded-2xl hover:bg-blue-700 flex items-center justify-center min-w-[90px] transition-colors shadow-lg disabled:opacity-50 disabled:cursor-not-allowed" 
          :disabled="carregando || !pergunta.trim()">
          <font-awesome-icon v-if="carregando" icon="spinner" spin />
          <font-awesome-icon v-else icon="paper-plane" class="mr-2" />
          <span v-if="!carregando">Enviar</span>
        </button>
      </form>
    </div>
  </div>
</template>


<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'
import { enviarMensagemChat } from '../api/agno.js'
import { getStatus, getEntidades, getDadosAvancadosEntidade } from '../api/backend.js' // TODO: migrar para agno.js se aplicável
// Use apenas axios via agno.js para garantir centralização de erros
import { marked } from 'marked'

const pergunta = ref('')
const mensagens = ref([])
const carregando = ref(false)
const chatHistory = ref(null)


// Sugestões predefinidas para ajudar usuários não técnicos
const sugestoesPredefinidas = [
  "Qual o status atual do sistema e principais riscos?",
  "Quais são os KPIs mais críticos que preciso acompanhar?",
  "Há algum incidente afetando nossos clientes?",
  "Como está a performance comparada ao mês passado?",
  "Quais ações devo tomar para melhorar a disponibilidade?",
  "Mostre um resumo executivo da situação atual"
]

// Estado para entidades e período
const entidades = ref([])
const entidadeSelecionada = ref('')
const periodoSelecionado = ref('7d')

// Carregar entidades do backend
const carregarEntidades = async () => {
  try {
    const lista = await getEntidades()
    if (Array.isArray(lista)) {
      entidades.value = lista
      if (lista.length > 0 && !entidadeSelecionada.value) {
        entidadeSelecionada.value = lista[0].guid
      }
    }
  } catch (e) {
    // Silencioso, pode exibir erro se necessário
  }
}

// Dados iniciais do contexto para garantir que interface não está vazia
const contexto = ref({
  statusGeral: 'Carregando...',
  incidentesAtivos: 0,
  disponibilidade: 0,
  atualizadoEm: new Date(),
  conhecimentos: [
    'Métricas', 'Incidentes', 'Tendências', 'KPIs',
    'Alertas', 'Infraestrutura', 'Logs', 'Performance'
  ],
  totalEntidades: 0,
  entidadesComMetricas: 0
})

// Selecionar uma sugestão predefinida
const selecionarSugestao = (texto) => {
  pergunta.value = texto
  enviarPergunta(texto)
}

// Limpar toda a conversa
const limparConversa = () => {
  if (mensagens.value.length > 0) {
    if (confirm('Tem certeza que deseja limpar toda a conversa?')) {
      mensagens.value = []
      localStorage.removeItem('chatHistory')
    }
  }
}

// Copiar texto da resposta para a área de transferência
const copiarResposta = (texto) => {
  // Remove HTML tags para obter texto puro
  const textoPuro = texto.replace(/<[^>]*>/g, '')
  navigator.clipboard.writeText(textoPuro).then(() => {
    alert('Resposta copiada para a área de transferência')
  }).catch(err => {
    console.error('Erro ao copiar texto: ', err)
  })
}

// Formatar valores numéricos com unidade
const formatarValor = (valor, unidade = '') => {
  if (valor === null || valor === undefined) return 'N/A'
  
  if (typeof valor === 'number') {
    // Formata número com 2 casas decimais
    const formatado = valor.toFixed(2)
    return unidade ? `${formatado}${unidade}` : formatado
  }
  
  return unidade ? `${valor}${unidade}` : valor
}

// Determinar classe de cor baseado no valor e tipo de métrica
const getColorClass = (valor, tipo) => {
  if (valor === null || valor === undefined) return 'text-gray-400'
  
  switch(tipo) {
    case 'apdex':
      return valor >= 0.9 ? 'text-green-400' : 
             valor >= 0.7 ? 'text-yellow-400' : 'text-red-400'
    case 'error':
      return valor <= 1 ? 'text-green-400' : 
             valor <= 5 ? 'text-yellow-400' : 'text-red-400'
    case 'disponibilidade':
      return valor >= 99 ? 'text-green-400' : 
             valor >= 95 ? 'text-yellow-400' : 'text-red-400'
    default:
      return 'text-white'
  }
}



// Função utilitária para gerar um session_id único
function gerarNovoSessionId() {
  return 'sess_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
}

// Função para obter o perfil do usuário (pode ser aprimorada conforme o sistema)
function obterPerfilUsuario() {
  // Exemplo: buscar do localStorage ou definir padrão
  return localStorage.getItem('perfil_usuario') || 'tecnico';
}

const enviarPergunta = async (texto) => {
  if (!texto.trim()) return;

  // Obtém a data e hora atual
  const agora = new Date();
  const formatoHora = new Intl.DateTimeFormat('pt-BR', {
    hour: '2-digit',
    minute: '2-digit'
  }).format(agora);

  mensagens.value.push({
    tipo: 'pergunta',
    texto: texto.trim(),
    timestamp: formatoHora
  });

  mensagens.value.push({
    tipo: 'resposta',
    texto: '',
    carregando: true
  });

  pergunta.value = '';
  carregando.value = true;

  await nextTick();
  if (chatHistory.value) {
    chatHistory.value.scrollTop = chatHistory.value.scrollHeight;
  }

  try {
    // Busca dados avançados de todas as entidades para contexto global
    let contextoGlobal = { entidades: [] };
    for (const ent of entidades.value) {
      const dados = await getDadosAvancadosEntidade(ent.guid, periodoSelecionado.value);
      contextoGlobal.entidades.push({ guid: ent.guid, name: ent.name, ...dados });
    }
    // session_id persistente por usuário
    let session_id = localStorage.getItem('session_id');
    if (!session_id) {
      session_id = gerarNovoSessionId();
      localStorage.setItem('session_id', session_id);
    }
    const perfil = obterPerfilUsuario();
    // Envia contexto como objeto para o backend (ajustado para o padrão do backend)
    // Monta payload apenas com campos definidos
    const payload = {
      mensagem: texto.trim(),
      session_id,
      perfil
    };
    if (contextoGlobal && contextoGlobal.entidades && contextoGlobal.entidades.length > 0) {
      payload.contexto = contextoGlobal;
    }
    const data = await enviarMensagemChat(payload);
    const ultimaMensagem = mensagens.value[mensagens.value.length - 1];
    // Tratamento robusto de resposta
    if (data && !data.erro) {
      ultimaMensagem.texto = data.resposta || 'Desculpe, não consegui processar sua pergunta.';
      ultimaMensagem.carregando = false;
      if (data.contexto) {
        contexto.value = {
          ...contexto.value,
          ...data.contexto,
          atualizadoEm: new Date(data.contexto.atualizadoEm || new Date())
        };
        ultimaMensagem.entidadesDetalhadas = Array.isArray(data.contexto.entidades) ? data.contexto.entidades : [];
        ultimaMensagem.logsDetalhados = Array.isArray(data.contexto.logs) ? data.contexto.logs : [];
        ultimaMensagem.incidentesDetalhados = Array.isArray(data.contexto.incidentes) ? data.contexto.incidentes : [];
        ultimaMensagem.dashboardsDetalhados = Array.isArray(data.contexto.dashboards) ? data.contexto.dashboards : [];
        ultimaMensagem.alertasDetalhados = Array.isArray(data.contexto.alertas) ? data.contexto.alertas : [];
        if (data.contexto.metricas || data.contexto.resumo) {
          ultimaMensagem.resumoMetricas = {
            disponibilidade: data.contexto.disponibilidade || data.contexto.metricas?.disponibilidade,
            apdex_medio: data.contexto.apdex_medio || data.contexto.metricas?.apdex_medio,
            taxa_erro_media: data.contexto.taxa_erro_media || data.contexto.metricas?.taxa_erro_media,
            total_entidades: data.contexto.totalEntidades || (Array.isArray(data.contexto.entidades) ? data.contexto.entidades.length : 0)
          };
        }
      }
    } else {
      ultimaMensagem.texto =
        `<div class="bg-red-900/30 border border-red-600 rounded-lg p-4 mt-2">
          <h4 class="font-semibold text-red-300 mb-2">🚫 Serviço indisponível</h4>
          <p class="text-red-200 mb-3">${data?.mensagem || 'O Chat IA não conseguiu processar sua pergunta. Verifique se o backend está funcionando.'}</p>
          <div class="text-sm text-red-300">
            <p><strong>Possíveis causas:</strong></p>
            <ul class="list-disc ml-4 mt-1">
              <li>Backend não está em execução na porta 8000</li>
              <li>Erro de conectividade com a API</li>
              <li>Serviço de IA temporariamente indisponível</li>
            </ul>
            <button onclick=\"location.reload()\" 
              class=\"mt-3 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded transition-colors\">
              🔄 Recarregar página
            </button>
          </div>
        </div>`;
      ultimaMensagem.carregando = false;
      ultimaMensagem.erro = true;
      if (data?.mensagem && data.mensagem.includes('context_length_exceeded')) {
        ultimaMensagem.texto =
          `<div class="bg-yellow-900/30 border border-yellow-600 rounded-lg p-4 mt-2">
            <h4 class="font-semibold text-yellow-300 mb-2">⚠️ Limite de tokens excedido</h4>
            <p class="text-yellow-200 mb-3">A conversa ficou muito longa para o modelo processar. Você pode:</p>
            <div class="space-y-2 text-sm">
              <button onclick=\"window.limparConversa()\" 
                class=\"block w-full bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded transition-colors\">
                🗑️ Limpar conversa e começar de novo
              </button>
            </div>
          </div>`;
      }
    }
  } catch (error) {
    const ultimaMensagem = mensagens.value[mensagens.value.length - 1];
    ultimaMensagem.texto = error?.message || 'Erro inesperado ao processar sua pergunta.';
    ultimaMensagem.carregando = false;
    ultimaMensagem.erro = true;
  } finally {
    carregando.value = false;
    await nextTick();
    if (chatHistory.value) {
      chatHistory.value.scrollTop = chatHistory.value.scrollHeight;
    }
  }
}

function formatarResposta(texto) {
  if (!texto) return '<span class="text-gray-400">Sem resposta da IA</span>'

  // Renderiza markdown usando 'marked' e aplica classes utilitárias para tabelas, listas e blocos de código
  let html = marked.parse(texto, { breaks: true })

  // Adiciona classes utilitárias do Tailwind para tabelas, listas e blocos de código
  html = html
    .replace(/<table>/g, '<table class="min-w-full text-sm text-left text-gray-300 border border-gray-700 my-2">')
    .replace(/<thead>/g, '<thead class="bg-gray-800">')
    .replace(/<th>/g, '<th class="bg-gray-800 px-2 py-1 border-b border-gray-700">')
    .replace(/<td>/g, '<td class="px-2 py-1 border-b border-gray-700">')
    .replace(/<ul>/g, '<ul class="list-disc ml-6 my-2">')
    .replace(/<ol>/g, '<ol class="list-decimal ml-6 my-2">')
    .replace(/<pre>/g, '<pre class="bg-gray-800 rounded p-2 overflow-x-auto my-2">')
    .replace(/<code>/g, '<code class="text-green-400">')
    .replace(/<a /g, '<a class="text-blue-400 hover:underline" ')

  return html
}

const formatarDataHora = (data) => {
  if (!data) return ''
  
  if (typeof data === 'string') {
    data = new Date(data)
  }
  
  return data.toLocaleString('pt-BR', { 
    day: '2-digit',
    month: '2-digit', 
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

import { resetTokenLimits } from '../api/agno.js'
const resetarLimiteTokens = async () => {
  try {
    mensagens.value.push({
      tipo: 'resposta',
      texto: 'Resetando limite de tokens...',
      carregando: true
    })
    const response = await resetTokenLimits()
    const ultimaMensagem = mensagens.value[mensagens.value.length - 1]
    if (response && !response.erro) {
      ultimaMensagem.texto = 'Limite de tokens resetado com sucesso! Você já pode continuar usando o chat.'
      ultimaMensagem.carregando = false
      ultimaMensagem.erro = false
    } else {
      ultimaMensagem.texto = `Erro ao resetar limite: ${response?.mensagem || 'Ocorreu um erro desconhecido'}`
      ultimaMensagem.carregando = false
      ultimaMensagem.erro = true
    }
    await nextTick()
    if (chatHistory.value) {
      chatHistory.value.scrollTop = chatHistory.value.scrollHeight
    }
  } catch (error) {
    console.error('Erro ao resetar limite de tokens:', error)
    mensagens.value.push({
      tipo: 'resposta',
      texto: `Erro ao resetar limite de tokens: ${error.message || 'Erro desconhecido'}`,
      erro: true
    })
    await nextTick()
    if (chatHistory.value) {
      chatHistory.value.scrollTop = chatHistory.value.scrollHeight
    }
  }
}

const carregarDados = async () => {
  try {
    const response = await getStatus();
    console.log('Resposta do getStatus:', response);
    if (response && !response.erro) {
      contexto.value = {
        ...contexto.value,
        statusGeral: response.statusGeral || 'Bom',
        incidentesAtivos: response.incidentesAtivos || 0,
        disponibilidade: response.disponibilidade || 99.9,
        totalEntidades: response.totalEntidades || 0,
        entidadesComMetricas: response.entidadesComMetricas || 0,
        atualizadoEm: new Date()
      }
    } else {
      console.warn('Status do backend retornou erro ou dados vazios:', response);
    }
  } catch (error) {
    console.error("Erro ao carregar dados do backend:", error)
  }
}

// Inicializa com mensagem de boas-vindas

onMounted(async () => {
  // Expor função globalmente para botões inline
  window.limparConversa = limparConversa
  await carregarEntidades()
  // Busca mensagem inicial e contexto do backend para garantir atualização
  try {
    let contextoAvancado = null
    if (entidadeSelecionada.value) {
      contextoAvancado = await getDadosAvancadosEntidade(entidadeSelecionada.value, periodoSelecionado.value)
    }
    // Monta payload inicial para mensagem_inicial
    let session_id = localStorage.getItem('session_id');
    if (!session_id) {
      session_id = gerarNovoSessionId();
      localStorage.setItem('session_id', session_id);
    }
    const perfil = obterPerfilUsuario();
    const payload = {
      mensagem: 'mensagem_inicial',
      session_id,
      perfil
    };
    if (contextoAvancado) payload.contexto = contextoAvancado;
    const data = await enviarMensagemChat(payload);
    if (data && data.resposta) {
      mensagens.value = [{ tipo: 'resposta', texto: data.resposta }]
      if (data.contexto) {
        contexto.value = {
          ...contexto.value,
          ...data.contexto,
          atualizadoEm: new Date()
        }
      }
      localStorage.setItem('chatHistory', JSON.stringify(mensagens.value))
    } else {
      mensagens.value = [{
        tipo: 'resposta',
        texto: `
          <div class="bg-yellow-900/30 border border-yellow-600 rounded-lg p-4">
            <h4 class="font-semibold text-yellow-300 mb-2">⚠️ Backend indisponível</h4>
            <p class="text-yellow-200 mb-3">Não foi possível conectar ao backend. Verifique se o serviço está rodando na porta 8000.</p>
            <p class="text-yellow-200 text-sm">O Chat IA ficará disponível assim que o backend for iniciado.</p>
          </div>
        `,
        erro: true
      }]
      localStorage.setItem('chatHistory', JSON.stringify(mensagens.value))
    }
  } catch (error) {
    mensagens.value = [{
      tipo: 'resposta',
      texto: `
        <div class="bg-red-900/30 border border-red-600 rounded-lg p-4">
          <h4 class="font-semibold text-red-300 mb-2">🚫 Erro de conexão</h4>
          <p class="text-red-200 mb-3">Não foi possível carregar a mensagem inicial do backend.</p>
          <p class="text-red-200 text-sm"><strong>Erro:</strong> ${error.message}</p>
          <button onclick="location.reload()" 
            class="mt-3 bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded text-sm transition-colors">
            🔄 Tentar novamente
          </button>
        </div>
      `,
      erro: true
    }]
    localStorage.setItem('chatHistory', JSON.stringify(mensagens.value))
    console.error('Erro ao carregar mensagem inicial:', error)
  }
  carregarDados()
})

// Salvar histórico sempre que as mensagens mudarem
watch(mensagens, (novasMensagens) => {
  if (novasMensagens.length > 0) {
    localStorage.setItem('chatHistory', JSON.stringify(novasMensagens))
  }
}, { deep: true })
</script>

<style scoped>
body, html {
  background: #181c24 !important;
  color: #fff;
}
.dot-flashing {
  position: relative;
  width: 1.5em;
  height: 1.5em;
  border-radius: 50%;
  background: #3b82f6;
  animation: dotFlashing 1s infinite linear alternate;
}
@keyframes dotFlashing {
  0% { opacity: 1; }
  50% { opacity: 0.3; }
  100% { opacity: 1; }
}
</style>
