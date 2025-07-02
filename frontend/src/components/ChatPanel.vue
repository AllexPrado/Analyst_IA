<template>
  <div class="flex flex-col items-center justify-center min-h-screen bg-gray-900">
    <div class="w-full max-w-5xl mx-auto rounded-2xl shadow-2xl bg-gray-900 text-white p-0 md:p-6 flex flex-col h-screen">
      <div class="flex-shrink-0 px-6 pt-6 pb-3 border-b border-gray-800">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center">
            <font-awesome-icon icon="robot" class="text-blue-400 text-xl mr-3" />
            <h2 class="text-2xl font-bold">Chat IA</h2>
          </div>
          <div>
            <button class="bg-gray-800 hover:bg-gray-700 px-3 py-1 rounded-lg text-sm flex items-center" @click="limparConversa">
              <font-awesome-icon icon="trash" class="mr-2" />
              Limpar conversa
            </button>
          </div>
        </div>
        <p class="text-gray-400 text-sm mb-0">Seu analista digital para dúvidas técnicas e executivas</p>
      </div>
      <div class="flex-1 overflow-y-auto px-4 py-4" ref="chatHistory" style="scroll-behavior: smooth;">
        <div v-if="mensagens.length === 0" class="flex flex-col items-center justify-center h-full text-gray-400">
          <font-awesome-icon icon="comment-dots" class="text-5xl mb-5 text-blue-400" />
          <p class="text-2xl mb-3 font-light">Converse com o Chat IA</p>
          <div class="max-w-lg">
            <p class="text-sm mb-6 text-center">Pergunte sobre métricas, tendências, incidentes, recomendações e mais.</p>
            
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
            <div class="flex items-start">
              <div class="flex-shrink-0 mr-2 mt-1">
                <div class="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center text-white">
                  <font-awesome-icon icon="robot" />
                </div>
              </div>
              <div :class="`px-5 py-3 rounded-2xl max-w-[70%] shadow ${mensagem.erro ? 'bg-red-900 border border-red-800' : 'bg-gray-700'}`">
                <div v-if="!mensagem.erro" class="text-white">
                  <div v-html="formatarResposta(mensagem.texto)"></div>
                  
                  <!-- Mostra dados de entidade específica, se disponível -->
                  <div v-if="mensagem.entidadesDetalhadas && mensagem.entidadesDetalhadas.length" class="mt-3 border-t border-gray-600 pt-3">
                    <div v-for="(entidade, idx) in mensagem.entidadesDetalhadas" :key="idx" class="mb-2 p-2 rounded bg-gray-800/50">
                      <div class="font-medium text-blue-300">{{ entidade.name }}</div>
                      <div class="grid grid-cols-2 gap-2 text-sm mt-1">
                        <div class="flex justify-between">
                          <span class="text-gray-400">Apdex:</span>
                          <span :class="getColorClass(entidade.metricas?.['24h']?.apdex, 'apdex')">{{ formatarValor(entidade.metricas?.['24h']?.apdex) }}</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-400">Erros:</span>
                          <span :class="getColorClass(entidade.metricas?.['24h']?.error_rate, 'error')">{{ formatarValor(entidade.metricas?.['24h']?.error_rate, '%') }}</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-400">Resposta:</span>
                          <span>{{ formatarValor(entidade.metricas?.['24h']?.response_time, 'ms') }}</span>
                        </div>
                        <div class="flex justify-between">
                          <span class="text-gray-400">Throughput:</span>
                          <span>{{ formatarValor(entidade.metricas?.['24h']?.throughput, 'req/min') }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- Resumo de métricas globais, se disponível -->
                  <div v-if="mensagem.resumoMetricas" class="mt-3 border-t border-gray-600 pt-3 text-sm">
                    <div class="grid grid-cols-2 gap-2">
                      <div class="flex justify-between p-1 rounded bg-gray-800/50">
                        <span class="text-gray-400">Disponibilidade:</span>
                        <span :class="getColorClass(mensagem.resumoMetricas.disponibilidade, 'disponibilidade')">{{ formatarValor(mensagem.resumoMetricas.disponibilidade, '%') }}</span>
                      </div>
                      <div class="flex justify-between p-1 rounded bg-gray-800/50">
                        <span class="text-gray-400">Apdex médio:</span>
                        <span :class="getColorClass(mensagem.resumoMetricas.apdex_medio, 'apdex')">{{ formatarValor(mensagem.resumoMetricas.apdex_medio) }}</span>
                      </div>
                      <div class="flex justify-between p-1 rounded bg-gray-800/50">
                        <span class="text-gray-400">Taxa de erro média:</span>
                        <span :class="getColorClass(mensagem.resumoMetricas.taxa_erro_media, 'error')">{{ formatarValor(mensagem.resumoMetricas.taxa_erro_media, '%') }}</span>
                      </div>
                      <div class="flex justify-between p-1 rounded bg-gray-800/50">
                        <span class="text-gray-400">Total de entidades:</span>
                        <span>{{ formatarValor(mensagem.resumoMetricas.total_entidades) }}</span>
                      </div>
                    </div>
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
import { getChatResposta, getStatus } from '../api/backend.js'
import axios from 'axios'
import { marked } from 'marked'

const pergunta = ref('')
const mensagens = ref([])
const carregando = ref(false)
const chatHistory = ref(null)

// Sugestões predefinidas para ajudar usuários não técnicos
const sugestoesPredefinidas = [
  "Qual o status atual do sistema?",
  "Mostre os principais alertas de hoje",
  "Como está o desempenho da aplicação?",
  "Quais métricas estão críticas?"
]

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

const enviarPergunta = async (texto) => {
  if (!texto.trim()) return
  
  // Obtém a data e hora atual
  const agora = new Date()
  const formatoHora = new Intl.DateTimeFormat('pt-BR', {
    hour: '2-digit',
    minute: '2-digit'
  }).format(agora)
  
  // Adiciona a pergunta do usuário com timestamp
  mensagens.value.push({
    tipo: 'pergunta',
    texto: texto.trim(),
    timestamp: formatoHora
  })
  
  // Adiciona um placeholder para a resposta com indicador de carregamento
  mensagens.value.push({
    tipo: 'resposta',
    texto: '',
    carregando: true
  })
  
  // Limpa o campo de pergunta e esconde sugestões após o primeiro uso
  pergunta.value = ''
  carregando.value = true
  
  // Rola para o final do chat
  await nextTick()
  if (chatHistory.value) {
    chatHistory.value.scrollTop = chatHistory.value.scrollHeight
  }

  try {
    await carregarDados()
    // Chamada real à API
    const data = await getChatResposta(texto.trim())
    const ultimaMensagem = mensagens.value[mensagens.value.length - 1]
    
    if (data && !data.erro) {
      ultimaMensagem.texto = data.resposta || 'Desculpe, não consegui processar sua pergunta.'
      ultimaMensagem.carregando = false
      
      // Processar o contexto recebido e extrair informações relevantes
      if (data.contexto) {
        contexto.value = {
          ...contexto.value,
          ...data.contexto,
          atualizadoEm: new Date(data.contexto.atualizadoEm || new Date())
        }
        
        // Extrair entidades detalhadas, se disponíveis no contexto
        if (data.contexto.entidades && Array.isArray(data.contexto.entidades)) {
          // Limitar a 3 entidades para não sobrecarregar a interface
          ultimaMensagem.entidadesDetalhadas = data.contexto.entidades.slice(0, 3)
        }
        
        // Extrair resumo de métricas, se disponível
        if (data.contexto.metricas || data.contexto.resumo) {
          ultimaMensagem.resumoMetricas = {
            disponibilidade: data.contexto.disponibilidade || data.contexto.metricas?.disponibilidade,
            apdex_medio: data.contexto.apdex_medio || data.contexto.metricas?.apdex_medio,
            taxa_erro_media: data.contexto.taxa_erro_media || data.contexto.metricas?.taxa_erro_media,
            total_entidades: data.contexto.totalEntidades || data.contexto.entidades?.length || 0
          }
        }
      }
    } else {
      ultimaMensagem.texto = data?.mensagem || 'Erro ao obter resposta da IA.'
      ultimaMensagem.carregando = false
      ultimaMensagem.erro = true
    }
  } catch (error) {
    const ultimaMensagem = mensagens.value[mensagens.value.length - 1]
    ultimaMensagem.texto = error?.message || 'Erro inesperado ao processar sua pergunta.'
    ultimaMensagem.carregando = false
    ultimaMensagem.erro = true
  } finally {
    carregando.value = false
    await nextTick()
    if (chatHistory.value) {
      chatHistory.value.scrollTop = chatHistory.value.scrollHeight
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

const resetarLimiteTokens = async () => {
  try {
    // Adiciona mensagem informativa
    mensagens.value.push({
      tipo: 'resposta',
      texto: 'Resetando limite de tokens...',
      carregando: true
    })
    
    // Chama o endpoint para resetar tokens
    const response = await axios.post('/api/limits/reset')
    
    // Atualiza mensagem com resultado
    const ultimaMensagem = mensagens.value[mensagens.value.length - 1]
    if (response.data && response.data.sucesso) {
      ultimaMensagem.texto = 'Limite de tokens resetado com sucesso! Você já pode continuar usando o chat.'
      ultimaMensagem.carregando = false
      ultimaMensagem.erro = false
    } else {
      ultimaMensagem.texto = `Erro ao resetar limite: ${response.data?.mensagem || 'Ocorreu um erro desconhecido'}`
      ultimaMensagem.carregando = false
      ultimaMensagem.erro = true
    }
    
    // Rola para o final do chat
    await nextTick()
    if (chatHistory.value) {
      chatHistory.value.scrollTop = chatHistory.value.scrollHeight
    }
  } catch (error) {
    console.error("Erro ao resetar limite de tokens:", error)
    
    // Adiciona mensagem de erro
    mensagens.value.push({
      tipo: 'resposta',
      texto: `Erro ao resetar limite de tokens: ${error.message || 'Erro desconhecido'}`,
      erro: true
    })
    
    // Rola para o final do chat
    await nextTick()
    if (chatHistory.value) {
      chatHistory.value.scrollTop = chatHistory.value.scrollHeight
    }
  }
}

const carregarDados = async () => {
  try {
    const response = await getStatus()
    
    if (response.data) {
      // Atualiza o contexto com dados reais do backend
      contexto.value = {
        ...contexto.value,
        statusGeral: response.data.statusGeral || 'Bom',
        incidentesAtivos: response.data.incidentesAtivos || 0,
        disponibilidade: response.data.disponibilidade || 99.9,
        totalEntidades: response.data.totalEntidades || 0,
        entidadesComMetricas: response.data.entidadesComMetricas || 0,
        atualizadoEm: new Date()
      }
    }
  } catch (error) {
    console.error("Erro ao carregar dados do backend:", error)
  }
}

// Inicializa com mensagem de boas-vindas
onMounted(async () => {
  try {
    // Carregar histórico salvo, se existir
    const historico = localStorage.getItem('chatHistory')
    if (historico) {
      try {
        mensagens.value = JSON.parse(historico)
      } catch (e) {
        console.error('Erro ao carregar histórico:', e)
      }
    } else {
      // Sem histórico, carrega mensagem inicial
      const data = await getChatResposta('mensagem_inicial')
      if (data && data.resposta) {
        mensagens.value.push({
          tipo: 'resposta',
          texto: data.resposta
        })
        
        if (data.contexto) {
          contexto.value = {
            ...contexto.value,
            ...data.contexto,
            atualizadoEm: new Date()
          }
        }
      }
    }
  } catch (error) {
    console.error('Erro ao carregar mensagem inicial:', error)
  }

  // Carrega dados iniciais quando o componente for montado
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
