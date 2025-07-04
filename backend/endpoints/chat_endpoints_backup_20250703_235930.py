from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import random
from pathlib import Path
from pydantic import BaseModel, Field

# Configuração do logger
logger = logging.getLogger(__name__)

# Criar o router
router = APIRouter()

# Modelo para entrada do chat
class ChatInput(BaseModel):
    pergunta: str = Field(..., description="Pergunta do usuário")
    contexto: Optional[Dict[str, Any]] = Field(None, description="Contexto adicional para a pergunta (opcional)")

# Banco de conhecimento simulado para respostas mais relevantes
KNOWLEDGE_BASE = {
    "metricas": [
        "As métricas mais críticas atualmente são a latência da API de pagamentos (2.1s) e a taxa de erro do serviço de autenticação (3.5%).",
        "Recomendo focar na otimização da API de Pagamentos que está apresentando latência 245% acima do normal.",
        "Os microsserviços de autenticação e processamento de pedidos estão com desempenho abaixo do esperado.",
        "A disponibilidade atual está em 99.9%, com uma melhora de 0.2% em relação ao período anterior.",
        "O Apdex score está em 0.89, indicando excelente satisfação dos usuários."
    ],
    "performance": [
        "A performance do sistema está 15% melhor que no mês passado, com destaque para a redução de 45% no tempo de resposta da API principal.",
        "Identificamos que o banco de dados está com consultas lentas devido a índices ausentes nas tabelas principais.",
        "O bottleneck atual está no processamento de imagens. Recomendo implementar um sistema de cache ou CDN.",
        "O tempo de resposta da API principal melhorou significativamente após a otimização do código.",
        "A principal causa de lentidão está relacionada às consultas SQL não otimizadas."
    ],
    "erros": [
        "Os principais erros registrados nas últimas 24 horas são: timeout na API de pagamentos (68 ocorrências) e falhas de autenticação (45 ocorrências).",
        "O serviço de processamento de imagens apresentou 3 falhas críticas nas últimas 12 horas.",
        "Detectamos um aumento de 27% nos erros 500 após o último deploy. Recomendo verificar as mudanças recentes.",
        "A taxa de erro global está em 1.2%, abaixo do limite crítico de 2%.",
        "O padrão de erros indica um problema no serviço de cache que está afetando múltiplos componentes."
    ],
    "infraestrutura": [
        "O cluster Kubernetes está com 82% de utilização de CPU, próximo ao limite recomendado de 85%.",
        "Dois nós no cluster de produção estão com mais de 90% de utilização de memória e precisam ser escalados.",
        "O serviço de banco de dados está com 78% de utilização de disco, recomendo planejar expansão.",
        "A infraestrutura atual suporta até 5000 usuários simultâneos, mas o pico recente foi de 4200.",
        "Recomendo aumentar os recursos de CPU e memória para o serviço de processamento de pedidos."
    ],
    "negocio": [
        "O ROI do monitoramento está em 8.3x, representando um aumento de 9.0% em relação ao período anterior.",
        "A economia total gerada pelas otimizações foi de R$ 68.727,59 no último trimestre.",
        "O tempo médio de resolução de incidentes diminuiu 35%, aumentando a produtividade em 24.6%.",
        "17 incidentes críticos foram evitados no último mês graças ao monitoramento proativo.",
        "A satisfação dos usuários aumentou para 7.5/10, uma melhoria de 0.4 pontos."
    ],
    "recomendacoes": [
        "Recomendo otimizar as queries SQL no serviço de inventário que estão consumindo muitos recursos.",
        "Implementar cache de dados de sessão com Redis pode reduzir a carga no banco de dados em até 40%.",
        "Consolidar os servidores de aplicação no ambiente de homologação pode reduzir custos operacionais.",
        "Atualizar as bibliotecas de segurança é urgente devido a vulnerabilidades conhecidas.",
        "Implementar rate limiting em APIs públicas para prevenir abusos e ataques DoS."
    ]
}

# Função para encontrar entidades relevantes com base na pergunta
def encontrar_entidades_relevantes(pergunta: str, entidades: List[Dict], max_entidades: int = 3) -> List[Dict]:
    """
    Identifica entidades mais relevantes com base na pergunta do usuário
    
    Args:
        pergunta: Pergunta do usuário
        entidades: Lista de entidades disponíveis
        max_entidades: Máximo de entidades a retornar
    
    Returns:
        Lista de entidades mais relevantes
    """
    pergunta_lower = pergunta.lower()
    palavras_chave = pergunta_lower.split()
    
    # Pontuação para cada entidade com base em palavras-chave na pergunta
    pontuacao_entidades = []
    
    for entidade in entidades:
        pontos = 0
        nome = entidade.get("name", "").lower()
        tipo = entidade.get("tipo", "").lower()
        dominio = entidade.get("dominio", "").lower()
        
        # Verifica se o nome, tipo ou domínio da entidade aparece na pergunta
        for palavra in palavras_chave:
            if palavra in nome or palavra in tipo or palavra in dominio:
                pontos += 10
        
        # Se a pergunta menciona métricas críticas e esta entidade tem métricas ruins
        if "crític" in pergunta_lower or "pior" in pergunta_lower:
            metricas = entidade.get("metricas", {}).get("24h", {})
            if metricas:
                error_rate = metricas.get("error_rate")
                apdex = metricas.get("apdex")
                response_time = metricas.get("response_time")
                
                if error_rate is not None and float(error_rate) > 5:
                    pontos += 15
                if apdex is not None and float(apdex) < 0.7:
                    pontos += 15
                if response_time is not None and float(response_time) > 2000:
                    pontos += 15
        
        # Se pergunta é sobre performance e esta entidade tem dados de resposta
        if "performance" in pergunta_lower or "desempenho" in pergunta_lower or "lentid" in pergunta_lower:
            metricas = entidade.get("metricas", {}).get("24h", {})
            if metricas and "response_time" in metricas:
                pontos += 10
        
        # Se pergunta é sobre erros
        if "erro" in pergunta_lower or "falha" in pergunta_lower:
            metricas = entidade.get("metricas", {}).get("24h", {})
            if metricas and "error_rate" in metricas:
                pontos += 10
        
        pontuacao_entidades.append((entidade, pontos))
    
    # Ordenar por pontuação (maior para menor)
    pontuacao_entidades.sort(key=lambda x: x[1], reverse=True)
    
    # Retornar as N entidades mais relevantes
    return [e[0] for e in pontuacao_entidades[:max_entidades]]

# Função para gerar respostas baseadas no conteúdo da pergunta
async def generate_chat_response(pergunta: str) -> Dict:
    """Gera resposta contextualizada para o chat IA"""
    pergunta = pergunta.lower()
    
    # Estrutura de resposta completa
    resposta_estruturada = {
        "resposta": "",
        "entidades": [],
        "metricas": {},
        "apdex_medio": None,
        "taxa_erro_media": None,
        "disponibilidade": None,
        "totalEntidades": 0,
        "entidadesComMetricas": 0
    }
    
    # Se for mensagem inicial, dê as boas-vindas
    if pergunta == "mensagem_inicial":
        resposta_estruturada["resposta"] = (
            "👋 Olá! Sou o assistente virtual do Analyst_IA, especializado em monitoramento e análise de aplicações.\n\n"
            "Posso ajudar com informações sobre métricas, status do sistema, desempenho, erros, "
            "recomendações e análises técnicas ou executivas.\n\n"
            "Como posso ajudar você hoje?"
        )
        return resposta_estruturada
        
    # Vamos precisar do cache para ter dados reais
    try:
        # Importar cache aqui para evitar dependência circular
        from utils.cache import get_cache, get_cache_sync, _initialize_cache
        
        # Primeiro tentar inicializar o cache de forma assíncrona
        try:
            await _initialize_cache()
            # Obter dados reais do cache de forma assíncrona
            cache_data = await get_cache()
        except Exception as e:
            # Se falhar, tentar de forma síncrona
            logger.warning(f"Erro ao acessar cache de forma assíncrona: {e}, tentando método síncrono")
            cache_data = get_cache_sync()
        
        if not cache_data or not isinstance(cache_data, dict):
            resposta_estruturada["resposta"] = "Não encontrei dados de monitoramento no cache. Por favor, atualize o cache com dados reais do New Relic."
            return resposta_estruturada
        
        # Extrair informações úteis do cache
        entidades = cache_data.get("entidades", [])
        num_entidades = len(entidades)
        resposta_estruturada["totalEntidades"] = num_entidades
        
        # Calcular métricas reais
        apdex_scores = []
        disponibilidades = []
        taxas_erro = []
        entidades_com_metricas = 0
        
        for entidade in entidades:
            metricas = entidade.get("metricas", {}).get("24h", {})
            if isinstance(metricas, dict):
                tem_metricas = False
                if "apdex" in metricas and metricas["apdex"] is not None:
                    apdex_scores.append(float(metricas["apdex"]))
                    tem_metricas = True
                if "error_rate" in metricas and metricas["error_rate"] is not None:
                    taxas_erro.append(float(metricas["error_rate"]))
                    tem_metricas = True
                if tem_metricas:
                    entidades_com_metricas += 1
        
        resposta_estruturada["entidadesComMetricas"] = entidades_com_metricas
        
        # Calcular médias
        apdex_medio = sum(apdex_scores) / len(apdex_scores) if apdex_scores else None
        taxa_erro_media = sum(taxas_erro) / len(taxas_erro) if taxas_erro else None
        disponibilidade = 100 - (sum(taxas_erro) / len(taxas_erro) if taxas_erro else 0)
        
        # Adicionar médias ao contexto
        if apdex_medio is not None:
            resposta_estruturada["apdex_medio"] = apdex_medio
        if taxa_erro_media is not None:
            resposta_estruturada["taxa_erro_media"] = taxa_erro_media
        if disponibilidade is not None:
            resposta_estruturada["disponibilidade"] = disponibilidade
        
        # Encontrar entidades relevantes para a pergunta
        entidades_relevantes = encontrar_entidades_relevantes(pergunta, entidades)
        if entidades_relevantes:
            resposta_estruturada["entidades"] = entidades_relevantes
        
        # Contagem por domínio
        dominios = cache_data.get("contagem_por_dominio", {})
        
        # Formatar uma resposta baseada em dados reais
        if "métrica" in pergunta or "metricas" in pergunta or "métricas" in pergunta:
            if apdex_medio is not None:
                resposta_estruturada["resposta"] = f"Com base nos dados reais, o Apdex score médio é {apdex_medio:.2f}. A taxa de erro média é {taxa_erro_media:.2f}%. Temos {num_entidades} entidades monitoradas."
                
                # Adicionar detalhes das entidades com métricas mais críticas
                if entidades_relevantes:
                    resposta_estruturada["resposta"] += "\n\nEntidades com métricas mais relevantes:"
                    for entidade in entidades_relevantes:
                        nome = entidade.get("name", "Desconhecido")
                        metricas = entidade.get("metricas", {}).get("24h", {})
                        apdex = metricas.get("apdex", "N/A")
                        error_rate = metricas.get("error_rate", "N/A")
                        resposta_estruturada["resposta"] += f"\n- {nome}: Apdex {apdex}, Taxa de erro {error_rate}%"
            else:
                resposta_estruturada["resposta"] = "Não encontrei métricas suficientes nas entidades monitoradas. Por favor, verifique a coleta de dados do New Relic."
        
        elif "performance" in pergunta or "desempenho" in pergunta or "lentidão" in pergunta:
            # Encontrar entidades com pior desempenho
            entidades_lentas = []
            for entidade in entidades:
                metricas = entidade.get("metricas", {}).get("24h", {})
                if isinstance(metricas, dict) and "response_time" in metricas and metricas["response_time"] is not None:
                    entidades_lentas.append((entidade.get("name", "Unknown"), float(metricas["response_time"])))
            
            # Ordenar por tempo de resposta (decrescente)
            entidades_lentas.sort(key=lambda x: x[1], reverse=True)
            
            if entidades_lentas:
                top_3 = entidades_lentas[:3]
                resposta_estruturada["resposta"] = "As entidades com pior performance são:\n\n"
                for i, (nome, tempo) in enumerate(top_3):
                    resposta_estruturada["resposta"] += f"{i+1}. **{nome}**: {tempo:.2f}ms\n"
                
                # Adicionar análise e recomendação
                resposta_estruturada["resposta"] += f"\nA média de tempo de resposta do sistema é de {sum(e[1] for e in entidades_lentas)/len(entidades_lentas):.2f}ms. "
                resposta_estruturada["resposta"] += "Recomendo analisar as consultas e dependências externas das entidades mais lentas."
            else:
                resposta_estruturada["resposta"] = "Não encontrei dados de performance suficientes. Por favor, verifique a coleta de dados do New Relic."
        
        elif "erro" in pergunta or "falha" in pergunta:
            # Encontrar entidades com mais erros
            entidades_com_erros = []
            for entidade in entidades:
                metricas = entidade.get("metricas", {}).get("24h", {})
                if isinstance(metricas, dict) and "error_rate" in metricas and metricas["error_rate"] is not None:
                    entidades_com_erros.append((entidade.get("name", "Unknown"), float(metricas["error_rate"])))
            
            # Ordenar por taxa de erro (decrescente)
            entidades_com_erros.sort(key=lambda x: x[1], reverse=True)
            
            if entidades_com_erros:
                top_3 = entidades_com_erros[:3]
                resposta_estruturada["resposta"] = "As entidades com maior taxa de erro são:\n\n"
                for i, (nome, taxa) in enumerate(top_3):
                    resposta_estruturada["resposta"] += f"{i+1}. **{nome}**: {taxa:.2f}%\n"
                
                # Adicionar análise e recomendação
                if taxa_erro_media is not None:
                    resposta_estruturada["resposta"] += f"\nA taxa de erro média do sistema é {taxa_erro_media:.2f}%. "
                    
                    if any(taxa > 5 for _, taxa in top_3):
                        resposta_estruturada["resposta"] += "É recomendável investigar os logs dessas entidades com urgência."
                    else:
                        resposta_estruturada["resposta"] += "As taxas de erro estão dentro de níveis aceitáveis."
            else:
                resposta_estruturada["resposta"] = "Não encontrei dados de erros suficientes. Por favor, verifique a coleta de dados do New Relic."
        
        elif "status" in pergunta:
            # Gerar resumo do status geral do sistema
            resposta_estruturada["resposta"] = f"Status atual do sistema com base em {num_entidades} entidades monitoradas:\n\n"
            
            # Status baseado na média de Apdex e taxa de erro
            status_sistema = "Bom"
            if apdex_medio is not None and taxa_erro_media is not None:
                if apdex_medio < 0.7 or taxa_erro_media > 5:
                    status_sistema = "Crítico"
                elif apdex_medio < 0.85 or taxa_erro_media > 2:
                    status_sistema = "Alerta"
            
            resposta_estruturada["resposta"] += f"**Status geral:** {status_sistema}\n"
            
            if apdex_medio is not None:
                resposta_estruturada["resposta"] += f"**Apdex médio:** {apdex_medio:.2f}\n"
            
            if taxa_erro_media is not None:
                resposta_estruturada["resposta"] += f"**Taxa de erro média:** {taxa_erro_media:.2f}%\n"
            
            if disponibilidade is not None:
                resposta_estruturada["resposta"] += f"**Disponibilidade estimada:** {disponibilidade:.2f}%\n"
            
            # Resumo por domínio
            if dominios:
                resposta_estruturada["resposta"] += "\n**Entidades por domínio:**\n"
                for dominio, contagem in dominios.items():
                    resposta_estruturada["resposta"] += f"- {dominio}: {contagem}\n"
        
        else:
            # Resposta genérica com dados reais
            resposta_estruturada["resposta"] = (
                f"Com base nos dados reais de {num_entidades} entidades monitoradas, "
                f"posso informar que:"
            )
            
            # Métricas gerais
            if apdex_medio is not None or taxa_erro_media is not None:
                resposta_estruturada["resposta"] += "\n\n**Métricas gerais:**"
                if apdex_medio is not None:
                    resposta_estruturada["resposta"] += f"\n- Apdex score médio: {apdex_medio:.2f}"
                if taxa_erro_media is not None:
                    resposta_estruturada["resposta"] += f"\n- Taxa de erro média: {taxa_erro_media:.2f}%"
                if disponibilidade is not None:
                    resposta_estruturada["resposta"] += f"\n- Disponibilidade estimada: {disponibilidade:.2f}%"
            
            # Informações de domínio
            if dominios:
                resposta_estruturada["resposta"] += "\n\n**Entidades por domínio:**"
                for dominio, contagem in dominios.items():
                    resposta_estruturada["resposta"] += f"\n- {dominio}: {contagem}"
            
            # Entidades em destaque
            if entidades_relevantes:
                resposta_estruturada["resposta"] += "\n\n**Entidades em destaque:**"
                for entidade in entidades_relevantes:
                    nome = entidade.get("name", "Desconhecido")
                    tipo = entidade.get("tipo", "Desconhecido")
                    metricas = entidade.get("metricas", {}).get("24h", {})
                    
                    resposta_estruturada["resposta"] += f"\n- **{nome}** ({tipo})"
                    if isinstance(metricas, dict):
                        if "apdex" in metricas and metricas["apdex"] is not None:
                            resposta_estruturada["resposta"] += f", Apdex: {metricas['apdex']}"
                        if "error_rate" in metricas and metricas["error_rate"] is not None:
                            resposta_estruturada["resposta"] += f", Erros: {metricas['error_rate']}%"
            
            # Instrução final
            resposta_estruturada["resposta"] += "\n\nPara uma análise mais específica, pergunte sobre métricas, performance, erros, status do sistema ou recomendações."
        
        # Retornar resposta estruturada com contexto detalhado
        return resposta_estruturada
    
    except Exception as e:
        logger.error(f"Erro ao processar dados reais para chat: {e}")
        resposta_estruturada["resposta"] = "Ocorreu um erro ao analisar os dados de monitoramento. Por favor, verifique o cache e a coleta de dados."
        return resposta_estruturada

@router.post("/chat")
async def chat_message(input: ChatInput):
    """
    Endpoint para processar mensagens do chat
    Recebe a pergunta do usuário e retorna uma resposta contextualizada
    """
    try:
        # Validar input
        pergunta = input.pergunta
        if not pergunta or not pergunta.strip():
            return JSONResponse(
                status_code=400,
                content={
                    "resposta": "Por favor, forneça uma pergunta válida.",
                    "status": "error",
                    "erro": "Pergunta não fornecida ou vazia"
                }
            )
        
        logger.info(f"Pergunta recebida: {pergunta}")
        
        # Gerar resposta contextualizada (função assíncrona)
        resposta_dados = await generate_chat_response(pergunta)
        
        # Extrair apenas a resposta textual
        resposta_texto = resposta_dados.get("resposta", "")
        logger.info(f"Resposta gerada: {resposta_texto[:100]}...")
        
        # Salvar conversa em histórico
        try:
            salvar_no_historico(pergunta, resposta_texto)
        except Exception as e:
            logger.warning(f"Não foi possível salvar no histórico: {e}")
            
        # Retornar resposta padronizada com contexto completo
        return {
            "resposta": resposta_texto,
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "contexto": {
                "processado": True,
                "fonte": "dados_reais",
                "atualizadoEm": datetime.now().isoformat(),
                # Incluir dados detalhados para o frontend
                "entidades": resposta_dados.get("entidades", []),
                "metricas": {
                    "apdex_medio": resposta_dados.get("apdex_medio"),
                    "taxa_erro_media": resposta_dados.get("taxa_erro_media"),
                    "disponibilidade": resposta_dados.get("disponibilidade")
                },
                "totalEntidades": resposta_dados.get("totalEntidades", 0),
                "entidadesComMetricas": resposta_dados.get("entidadesComMetricas", 0)
            }
        }
    except Exception as e:
        logger.error(f"Erro ao processar chat: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "resposta": "Ocorreu um erro ao processar sua pergunta. Por favor, tente novamente mais tarde.",
                "status": "error",
                "erro": str(e),
                "contexto": {
                    "erro": True,
                    "mensagem": str(e)
                }
            }
        )

# Função para salvar histórico de chat
def salvar_no_historico(pergunta: str, resposta: str):
    """
    Salva a conversa no histórico
    
    Args:
        pergunta: A pergunta do usuário
        resposta: A resposta gerada pela IA
    """
    try:
        # Possíveis caminhos para o arquivo de histórico
        history_paths = [
            "dados/chat_history.json",
            "backend/dados/chat_history.json",
            "../dados/chat_history.json"
        ]
        
        # Buscar ou criar o diretório correto
        history_dir = None
        for path in history_paths:
            dir_path = os.path.dirname(path)
            if os.path.exists(dir_path):
                history_dir = dir_path
                history_path = path
                break
        
        # Se não encontrou, criar em dados/
        if not history_dir:
            history_dir = "dados"
            history_path = "dados/chat_history.json"
            os.makedirs(history_dir, exist_ok=True)
            
        # Ler histórico existente ou criar novo
        history = []
        if os.path.exists(history_path):
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
                    if not isinstance(history, list):
                        history = []
            except Exception as e:
                logger.error(f"Erro ao ler histórico: {e}")
                history = []
        
        # Adicionar nova conversa
        history.append({
            "pergunta": pergunta,
            "resposta": resposta,
            "timestamp": datetime.now().isoformat()
        })
        
        # Limitar tamanho do histórico (opcional)
        if len(history) > 1000:
            history = history[-1000:]  # Mantém apenas as 1000 conversas mais recentes
        
        # Salvar histórico atualizado
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Conversa salva no histórico: {history_path}")
    except Exception as e:
        logger.error(f"Erro ao salvar no histórico: {e}")
        raise
