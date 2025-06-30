from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import JSONResponse
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import random
from pathlib import Path
from pydantic import BaseModel

# Configuração do logger
logger = logging.getLogger(__name__)

# Criar o router
router = APIRouter()

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

# Função para gerar respostas baseadas no conteúdo da pergunta
async def generate_chat_response(pergunta: str) -> str:
    """Gera resposta contextualizada para o chat IA"""
    pergunta = pergunta.lower()
    
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
            return "Não encontrei dados de monitoramento no cache. Por favor, atualize o cache com dados reais do New Relic."
        
        # Extrair informações úteis do cache
        entidades = cache_data.get("entidades", [])
        num_entidades = len(entidades)
        
        # Calcular métricas reais
        apdex_scores = []
        disponibilidades = []
        taxas_erro = []
        
        for entidade in entidades:
            metricas = entidade.get("metricas", {}).get("24h", {})
            if isinstance(metricas, dict):
                if "apdex" in metricas and metricas["apdex"] is not None:
                    apdex_scores.append(float(metricas["apdex"]))
                if "error_rate" in metricas and metricas["error_rate"] is not None:
                    taxas_erro.append(float(metricas["error_rate"]))
        
        # Calcular médias
        apdex_medio = sum(apdex_scores) / len(apdex_scores) if apdex_scores else None
        taxa_erro_media = sum(taxas_erro) / len(taxas_erro) if taxas_erro else None
        
        # Contagem por domínio
        dominios = cache_data.get("contagem_por_dominio", {})
        
        # Formatar uma resposta baseada em dados reais
        if "métrica" in pergunta or "metricas" in pergunta or "métricas" in pergunta:
            if apdex_medio is not None:
                return f"Com base nos dados reais, o Apdex score médio é {apdex_medio:.2f}. A taxa de erro média é {taxa_erro_media:.2f}%. Temos {num_entidades} entidades monitoradas."
            else:
                return "Não encontrei métricas suficientes nas entidades monitoradas. Por favor, verifique a coleta de dados do New Relic."
        
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
                resposta = f"As 3 entidades com pior performance são: "
                for i, (nome, tempo) in enumerate(top_3):
                    resposta += f"{nome} ({tempo:.2f}ms)"
                    if i < len(top_3) - 1:
                        resposta += ", "
                return resposta
            else:
                return "Não encontrei dados de performance suficientes. Por favor, verifique a coleta de dados do New Relic."
        
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
                resposta = f"As 3 entidades com mais erros são: "
                for i, (nome, taxa) in enumerate(top_3):
                    resposta += f"{nome} ({taxa:.2f}%)"
                    if i < len(top_3) - 1:
                        resposta += ", "
                return resposta
            else:
                return "Não encontrei dados de erros suficientes. Por favor, verifique a coleta de dados do New Relic."
        
        else:
            # Resposta genérica com dados reais
            return (
                f"Com base nos dados reais do New Relic, posso informar que temos {num_entidades} entidades monitoradas "
                f"{', '.join([f'{k}: {v}' for k, v in dominios.items()])}. "
                f"{f'O Apdex score médio é {apdex_medio:.2f}. ' if apdex_medio is not None else ''}"
                f"{f'A taxa de erro média é {taxa_erro_media:.2f}%. ' if taxa_erro_media is not None else ''}"
                f"Para uma análise mais específica, por favor, detalhe sua pergunta sobre métricas, performance, "
                f"erros, infraestrutura, impacto no negócio ou recomendações."
            )
    except Exception as e:
        logger.error(f"Erro ao processar dados reais para chat: {e}")
        return "Ocorreu um erro ao analisar os dados de monitoramento. Por favor, verifique o cache e a coleta de dados."

class ChatInput(BaseModel):
    pergunta: str

@router.post("/chat")
async def chat_ai(data: dict = Body(...)):
    try:
        # Validar input
        pergunta = data.get("pergunta", "")
        if not pergunta:
            raise HTTPException(status_code=400, detail="Pergunta não fornecida")
        
        logger.info(f"Pergunta recebida: {pergunta}")
        
        # Gerar resposta contextualizada (função assíncrona)
        resposta = await generate_chat_response(pergunta)
        
        logger.info(f"Resposta gerada: {resposta}")
        
        # Salvar conversa em histórico
        try:
            salvar_no_historico(pergunta, resposta)
        except Exception as e:
            logger.warning(f"Não foi possível salvar no histórico: {e}")
            
        # Retornar resposta
        return {
            "resposta": resposta,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Erro ao processar chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
