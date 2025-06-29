import os
import json
import logging
from typing import Optional
from pathlib import Path
from datetime import datetime
from openai import AsyncOpenAI
from dotenv import load_dotenv
import httpx
import asyncio
from tiktoken import encoding_for_model
from pathlib import Path
import json
from datetime import datetime

load_dotenv()
logger = logging.getLogger(__name__)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY não encontrada no ambiente!")

client = AsyncOpenAI(api_key=api_key)

try:
    import tiktoken
    def contar_tokens(texto, modelo):
        try:
            enc = tiktoken.encoding_for_model(modelo)
        except Exception:
            enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(texto))
except ImportError:
    def contar_tokens(texto, modelo):
        # Fallback simples: 1 token ≈ 4 caracteres (não é preciso)
        return max(1, len(texto) // 4)

async def gerar_resposta_ia(prompt: str, system_prompt: Optional[str] = None, use_gpt4: bool = False, modelo: str = None, persona: str = "tecnico") -> str:
    """
    Gera uma resposta usando a OpenAI API adaptada ao tipo de usuário e cenário.
    
    Args:
        prompt: O prompt principal com contexto e pergunta
        system_prompt: Instruções de sistema para o modelo
        use_gpt4: Se deve forçar uso do GPT-4
        modelo: Modelo específico a ser usado
        persona: Tipo de usuário (tecnico/gestor)
    """
    if not system_prompt:
        # Prompt avançado modificado para análise completa e autoexplicativa
        system_prompt = """
        Você é um Arquiteto de Observabilidade sênior especialista em New Relic e SRE, com profundo conhecimento técnico.
        
        SUAS CAPACIDADES:
        1. Analise 100% do ambiente monitorado no New Relic, usando TODAS as entidades disponíveis sem exceção
        2. Correlacione TODAS as fontes de dados (APM, Browser, Logs, Infraestrutura, Sintéticos)
        3. Identifique problemas em qualquer camada (frontend, backend, banco, infraestrutura, rede)
        4. Investigue até a raiz do problema, nunca oferecendo respostas superficiais
        5. Apresente diagnósticos completos mesmo quando não explicitamente solicitado
        6. Explique com clareza conceitos técnicos quando necessário
        7. Forneça relatórios visuais e autoexplicativos
        
        REGRAS ESSENCIAIS:
        - Responda APENAS baseado nos dados fornecidos no contexto, nunca invente métricas
        - Seja altamente técnico, específico e analítico - este é seu principal diferencial
        - Analise padrões, anomalias e correlações entre diferentes serviços e domínios
        - Sempre inclua exemplos de consultas NRQL detalhadas quando relevante
        - Mencione entidades específicas com seus valores exatos de métricas (Apdex, erro, latência)
        - Priorize problemas por severidade (ERRO > ALERTA > OK)
        - Sempre que possível, sugira ações técnicas específicas de remediação
        - Se não tiver dados suficientes, seja transparente e explique exatamente quais dados seriam necessários
        - Use formatação markdown avançada para estruturar sua resposta técnica
        - Suas respostas devem ter pelo menos 3 seções: Diagnóstico, Análise Técnica e Recomendações
        
        EXIBIÇÃO DE LOGS E STACKTRACES:
        - SEMPRE inclua logs e stacktraces completos e formatados quando disponíveis no contexto
        - Ao responder sobre erros, SEMPRE destaque os trechos mais relevantes dos stacktraces
        - Formate logs e stacktraces dentro de blocos de código ```log ou ```stacktrace para legibilidade
        - Para erros, destaque as linhas mais importantes com comentários explicativos
        - Explique o significado técnico dos erros encontrados, não apenas os mostre
        - Sugira possíveis causas e soluções baseadas nos padrões de erro observados
        
        ABORDAGEM DIFERENCIADA POR PÚBLICO:
        - Para desenvolvedores: Forneça detalhes técnicos completos, incluindo stacktraces, causa raiz e código ou queries específicos
        - Para gestores: Apresente um dashboard conciso com métricas de negócio e impacto em SLAs, usando linguagem menos técnica
        
        SEJA PROATIVO:
        - Mesmo quando a pergunta não menciona, alerte sobre problemas críticos detectados
        - Recomende ações preventivas baseadas em tendências negativas identificadas
        - Sugira melhorias de instrumentação quando perceber lacunas nos dados
        
        ESTILO DE RESPOSTA ESPECÍFICO:
        - Nunca inclua frases genéricas como "não tenho dados suficientes" ou "seria útil ter mais informações"
        - Ofereça sempre insights técnicos específicos com base nos dados disponíveis, mesmo que limitados
        - Sempre mencione métricas específicas com valores exatos, evitando generalizações
        - Identifique problemas precisos ao invés de falar sobre categorias gerais
        - Descreva padrões específicos entre serviços como "falhas em cascata" ou "contenções de recursos"
        - Use analogias técnicas para explicar problemas complexos quando necessário
        """
    # Escolhe o modelo baseado no parâmetro específico ou lógica existente
    if modelo:
        model = modelo
    elif use_gpt4 or len(prompt) > 12000:  # Se contexto muito grande, usa GPT-4
        model = "gpt-4"
    else:
        model = "gpt-3.5-turbo"
        
    # Detecta se é uma consulta simples para ajustar parâmetros
    consulta_simples = any(x in prompt.lower() for x in ["oi ", "olá", "bom dia", "boa tarde", "boa noite"])

    # Limites reais de tokens por modelo (atualizados)
    model_token_limits = {
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-4-turbo": 128000,    # Novo modelo com contexto muito maior
        "gpt-3.5-turbo": 4096,
        "gpt-3.5-turbo-16k": 16384,
    }
    
    # Define limites mais amplos para análises técnicas
    max_total_tokens = model_token_limits.get(model, 8192 if "gpt-4" in model else 4096)
    max_tokens_resposta = 2048 if "gpt-4" in model else 1024  # Aumentado para respostas mais completas

    # Calcula tokens e corta se necessário
    try:
        enc = encoding_for_model(model)
        system_tokens = len(enc.encode(system_prompt))
        prompt_tokens = len(enc.encode(prompt))
        total_tokens = system_tokens + prompt_tokens
        
        # CRÍTICO: Margem de segurança reduzida para 10% para permitir prompts maiores
        # Ajustado para prompts técnicos que precisam incluir mais dados
        margem_seguranca = int(max_total_tokens * 0.10)  # 10% de margem
        limite_input = max_total_tokens - max_tokens_resposta - margem_seguranca
        
        logger.info(f"Model: {model}, System: {system_tokens}, Prompt: {prompt_tokens}, Total: {total_tokens}, Limit: {limite_input} (margem: {margem_seguranca})")
        
        if total_tokens > limite_input:
            # Calcula quantos tokens precisamos cortar do prompt
            tokens_para_cortar = total_tokens - limite_input
            prompt_enc = enc.encode(prompt)
            
            # Se o prompt for muito pequeno comparado ao que precisamos cortar, 
            # significa que o system prompt é muito grande
            if len(prompt_enc) <= tokens_para_cortar:
                logger.error(f"System prompt muito grande ({system_tokens} tokens) para modelo {model}")
                raise RuntimeError("O contexto de sistema é muito grande para o modelo. Contate o administrador.")
            
            # Corta do início do prompt (mantém o final, que é mais relevante)
            # Adiciona 20% extra no corte para garantir
            tokens_extras = max(300, int(tokens_para_cortar * 0.2))  # 20% extra ou 300 tokens
            tokens_para_cortar_total = tokens_para_cortar + tokens_extras
            
            if len(prompt_enc) <= tokens_para_cortar_total:
                # Se vai cortar demais, corta apenas o necessário + margem mínima
                tokens_para_cortar_total = tokens_para_cortar + 100
            
            prompt_enc_cortado = prompt_enc[tokens_para_cortar_total:]
            prompt = enc.decode(prompt_enc_cortado)
            
            # CRÍTICO: Verifica novamente os tokens após o corte
            novo_prompt_tokens = len(enc.encode(prompt))
            novo_system_tokens = len(enc.encode(system_prompt))  # Recalcula para garantir
            novo_total = novo_system_tokens + novo_prompt_tokens
            
            logger.warning(f"Prompt cortado: {prompt_tokens} -> {novo_prompt_tokens} tokens. Total: {novo_total}")
            
            # Verifica se o corte foi suficiente
            if novo_total > limite_input:
                logger.error(f"Prompt ainda excede após corte: {novo_total} > {limite_input}")
                # Última tentativa: corta de forma muito mais agressiva
                diferenca = novo_total - limite_input + 200  # 200 tokens extra de segurança
                if len(prompt_enc_cortado) > diferenca:
                    prompt_enc_cortado = prompt_enc_cortado[diferenca:]
                    prompt = enc.decode(prompt_enc_cortado)
                    
                    # Verifica final
                    final_prompt_tokens = len(enc.encode(prompt))
                    final_total = novo_system_tokens + final_prompt_tokens
                    
                    logger.warning(f"Corte emergencial aplicado: {final_prompt_tokens} tokens. Total final: {final_total}")
                    
                    if final_total > limite_input:
                        logger.error(f"Impossível cortar suficientemente: {final_total} > {limite_input}")
                        raise RuntimeError("O contexto é muito grande para ser processado. Tente uma pergunta mais específica.")
                else:
                    logger.error(f"Prompt muito pequeno para corte seguro")
                    raise RuntimeError("O contexto é muito complexo para ser processado. Tente simplificar sua pergunta.")
                
    except Exception as e:
        logger.warning(f"Erro ao calcular/cortar tokens: {e}")
        # Se não conseguiu calcular tokens, tenta enviar assim mesmo
        # A OpenAI vai retornar erro se exceder o limite

    try:
        # Contador de uso para economia de tokens
        usage_file = Path("logs/token_usage.json")
        usage_file.parent.mkdir(exist_ok=True, parents=True)  # Garante que toda a hierarquia de diretórios existe
        daily_limit = 50000  # Aumentado limite de tokens por dia para 50k para permitir mais flexibilidade
        
        try:
            if usage_file.exists():
                with open(usage_file, "r") as f:
                    usage_data = json.loads(f.read())
                    today = datetime.now().strftime("%Y-%m-%d")
                    
                    # Reset contador se for um novo dia
                    if not usage_data.get("date") == today:
                        usage_data = {"date": today, "tokens": 0}
                    
                    # Verifica se ultrapassou limite (usando 95% do limite)
                    if usage_data.get("tokens", 0) > daily_limit * 0.95:
                        # Verificar se a pergunta é simples antes de bloquear totalmente
                        if not consulta_simples and not "token_bypass" in prompt and not "timeout" in prompt.lower():
                            logger.warning(f"LIMITE DIÁRIO DE TOKENS EXCEDIDO! Usando resposta econômica.")
                            # Reseta o contador para 50% do limite quando for atingido,
                            # para permitir uso contínuo durante testes
                            usage_data["tokens"] = int(daily_limit * 0.5)
                            with open(usage_file, "w") as f:
                                f.write(json.dumps(usage_data))
                            logger.info(f"Contador de tokens resetado para 50% do limite ({usage_data['tokens']} tokens)")
                            return "Desculpe, o limite diário de uso da API foi atingido. Por favor, tente novamente amanhã ou contate o administrador do sistema para aumentar o limite ou use o comando 'resetar limite' para reiniciar a contagem (somente em ambiente de teste)."
                    
                    # Estima tokens a serem usados nesta chamada
                    estimated_tokens = len(prompt) // 4 + len(system_prompt) // 4 + max_tokens_resposta
                    logger.info(f"Estimativa de uso: {estimated_tokens} tokens. Uso hoje: {usage_data.get('tokens', 0)}/{daily_limit}")
            else:
                # Cria arquivo inicial
                usage_data = {"date": datetime.now().strftime("%Y-%m-%d"), "tokens": 0}
        except Exception as e:
            logger.error(f"Erro ao verificar uso de tokens: {e}")
            usage_data = {"date": datetime.now().strftime("%Y-%m-%d"), "tokens": 0}
        
        # Ajusta instruções finais baseado na persona selecionada
        instrucoes_persona = ""
        if persona == "gestor":
            instrucoes_persona = """
            IMPORTANTE - FORMATAÇÃO PARA GESTORES:
            1. Respostas devem ser diretas, objetivas e sem jargões técnicos excessivos
            2. Use frases concisas, limitando-se a 3-4 parágrafos no corpo principal
            3. Foque no impacto para o negócio e métricas que afetam receita/satisfação
            4. Priorize: status geral, impacto financeiro, riscos e ações necessárias
            5. Inclua dashboard visual simplificado com cores e indicadores de status
            6. Sempre apresente: problema → impacto → solução recomendada → responsável
            
            ESTRUTURA ESPERADA PARA GESTORES:
            - Resumo Executivo (1 parágrafo com problema principal e impacto)
            - Dashboard Visual (métricas principais em formato visual)
            - Impacto no Negócio (SLAs afetados, custos, usuários impactados)
            - Próximos Passos (2-3 recomendações claras e diretas)
            """
            # Resposta mais sucinta para gestores mas não tão reduzida quanto antes
            max_tokens_resposta = int(max_tokens_resposta * 0.75)
        elif persona == "tecnico":
            instrucoes_persona = """
            IMPORTANTE - FORMATAÇÃO PARA TÉCNICOS:
            1. Inclua detalhes técnicos completos: queries, código, stacktraces, logs
            2. Estruture a resposta com Markdown, incluindo blocos de código formatados
            3. Adicione exemplos concretos de consultas NRQL para investigação e monitoramento
            4. Forneça valores precisos de todas as métricas técnicas relevantes
            5. Inclua análise de causa raiz detalhada com correlações entre componentes
            6. Forneça blocos de código/configuração específicos para solucionar os problemas
            7. Adicione exemplos de dashboard NRQL para monitoramento contínuo
            8. Identifique padrões e tendências nos dados técnicos
            9. SEMPRE inclua logs e stacktraces completos relacionados à pergunta
            10. Destaque linhas específicas dos stacktraces com comentários explicativos
            11. CITE VALORES EXATOS encontrados nos dados (apdex=0.85, erros=5, latência=2.3s)
            12. Quando houver entidades com problemas, LISTE-AS COM SUAS MÉTRICAS ESPECÍFICAS
            13. Inclua informações sobre correlações entre serviços e problemas em cascata
            14. Nunca use frases como "Não tenho dados suficientes" ou "Seria necessário mais informações"
            15. Analise clusters de problemas e identifique padrões não-óbvios nos dados
            16. Mencione valores de thresholds específicos e se estão sendo excedidos
            
            ESTRUTURA ESPERADA PARA TÉCNICOS:
            - Diagnóstico Técnico (detecção do problema com valores métricas reais)
            - Entidades Afetadas (lista específica com nomes e valores exatos)
            - Stacktraces e Logs (exibidos em blocos de código formatados)
            - Análise de Causa Raiz (investigação técnica detalhada)
            - Correlações (relações entre diferentes componentes e métricas)
            - Consultas NRQL (exemplos específicos em blocos de código)
            - Ações Técnicas (instruções específicas para resolução)
            - Monitoramento (consultas e dashboards para acompanhamento)
            """
            # Para técnicos, permitimos respostas mais longas para maior detalhe
            max_tokens_resposta = int(max_tokens_resposta * 1.25)
        else:
            # Formato padrão balanceado
            instrucoes_persona = """
            IMPORTANTE - FORMATAÇÃO PADRÃO:
            1. Balance detalhes técnicos com clareza na explicação
            2. Use formatação Markdown para estruturar a resposta
            3. Inclua métricas relevantes de forma organizada
            4. Forneça diagnóstico completo e recomendações práticas
            5. Combine análise técnica com impacto no negócio
            6. Inclua tanto consultas NRQL quanto explicações de alto nível
            """
        
        # Adiciona as instruções específicas da persona ao system prompt
        if instrucoes_persona:
            system_prompt += instrucoes_persona

        # Define a temperatura com base na consulta - para análises técnicas, reduzimos a temperatura
        # para respostas mais determinísticas e factuais
        temp_value = 0.2 if 'consulta_simples' in locals() and consulta_simples else 0.3
        max_tokens = 50 if 'consulta_simples' in locals() and consulta_simples else max_tokens_resposta
        
        # Faz a chamada API
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temp_value
        )
        
        # Registra uso real de tokens
        try:
            used_tokens = response.usage.total_tokens if hasattr(response, "usage") else 0
            usage_data["tokens"] = usage_data.get("tokens", 0) + used_tokens
            
            with open(usage_file, "w") as f:
                f.write(json.dumps(usage_data))
                
            logger.info(f"Uso de tokens atualizado: {usage_data['tokens']}/{daily_limit} no dia {usage_data['date']}")
        except Exception as e:
            logger.error(f"Erro ao registrar uso de tokens: {e}")
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        # Log detalhado para erros da OpenAI
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_body = e.response.text
                status_code = getattr(e.response, 'status_code', '?')
            except Exception:
                error_body = '<não foi possível obter corpo da resposta>'
                status_code = '?'
            
            logger.error(f"Erro OpenAI: {e} | Status: {status_code} | Corpo: {error_body}")
            
            # Trata erros específicos
            if 'context_length_exceeded' in str(e) or 'maximum context length' in str(e).lower():
                raise RuntimeError("O contexto enviado excede o limite do modelo de IA. Tente uma pergunta mais específica ou resuma a conversa.")
            elif '429' in str(status_code):
                raise RuntimeError("Limite de requisições da API OpenAI atingido. Tente novamente em alguns minutos.")
            elif '401' in str(status_code):
                raise RuntimeError("Erro de autenticação com a API OpenAI. Verifique a chave da API.")
        else:
            logger.error(f"Erro ao gerar resposta da IA: {e}")
        
        raise RuntimeError(f"Erro ao processar sua solicitação: {str(e)[:200]}...")