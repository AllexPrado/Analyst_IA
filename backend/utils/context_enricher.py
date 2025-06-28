"""
Módulo para enriquecimento de contexto antes de enviar para a IA.
Realiza análise profunda de todas as métricas disponíveis e
enriquece o contexto com dados relevantes para a pergunta.
"""

import logging
from typing import Dict, List, Any, Optional
import re
import json
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

class ContextEnricher:
    """
    Classe responsável por enriquecer o contexto antes de enviar para o Chat IA.
    Garante que todas as métricas relevantes sejam incluídas e analisadas.
    """
    
    def __init__(self):
        self.metricas_essenciais = [
            'apdex', 'response_time', 'error_rate', 'throughput',
            'cpu', 'memory', 'disk', 'network', 'database', 'error'
        ]
        
        self.metricas_avancadas = [
            'sql_query', 'transaction_trace', 'stacktrace', 'error_detail', 
            'ajax_request', 'page_view', 'web_vitals', 'synthetic_check',
            'browser_interaction', 'span', 'distributed_trace', 'logs'
        ]
        
        # Pesos para diferentes tipos de dados
        self.pesos_metrica = {
            'apdex': 5,
            'error': 8,
            'response_time': 7,
            'sql_query': 8,
            'stacktrace': 9,
            'logs': 6,
            'distributed_trace': 7
        }
    
    def enriquecer_contexto(self, pergunta: str, contexto: Dict) -> Dict:
        """
        Enriquece o contexto baseado na pergunta e métricas disponíveis.
        
        Args:
            pergunta: A pergunta do usuário
            contexto: O contexto atual com entidades e métricas
            
        Returns:
            Contexto enriquecido com análises relevantes
        """
        logger.info(f"Iniciando enriquecimento de contexto para pergunta: {pergunta[:50]}...")
        
        if not contexto or not contexto.get('entidades'):
            logger.warning("Contexto vazio ou sem entidades para enriquecimento")
            return contexto
            
        # Detecta tópicos específicos na pergunta
        topicos = self._detectar_topicos(pergunta)
        logger.info(f"Tópicos detectados: {topicos}")
        
        # Cria análises específicas relevantes para os tópicos
        analises = {}
        
        # Analisa entidades em busca de padrões relevantes
        entidades = contexto.get('entidades', [])
        alertas = contexto.get('alertas', [])
        
        # Análise específica para cada tópico detectado
        if 'performance' in topicos:
            analises['performance'] = self._analisar_performance(entidades)
            
        if 'erro' in topicos:
            analises['erros'] = self._analisar_erros(entidades, alertas)
            
        if 'sql' in topicos or 'database' in topicos:
            analises['database'] = self._analisar_banco_dados(entidades)
            
        if 'frontend' in topicos or 'browser' in topicos:
            analises['frontend'] = self._analisar_frontend(entidades)
            
        if 'infra' in topicos or 'servidor' in topicos:
            analises['infra'] = self._analisar_infraestrutura(entidades)
        
        # Sempre executa análise de correlação para detectar padrões
        analises['correlacao'] = self._analisar_correlacoes(entidades, alertas)
        
        # Enriquece o contexto com as análises realizadas
        contexto_enriquecido = contexto.copy()
        contexto_enriquecido['analises'] = analises
        contexto_enriquecido['topicos_detectados'] = topicos
        
        # Adiciona timestamp da análise
        contexto_enriquecido['analise_timestamp'] = datetime.now().isoformat()
        
        return contexto_enriquecido
    
    def _detectar_topicos(self, pergunta: str) -> List[str]:
        """Detecta tópicos na pergunta do usuário"""
        pergunta_lower = pergunta.lower()
        
        topicos = []
        
        # Mapeamento de palavras-chave para tópicos
        mapeamento_topicos = {
            'performance': ['lent', 'performance', 'desempenho', 'lento', 'rapido', 'apdex', 'resposta'],
            'erro': ['erro', 'falha', 'exception', 'crash', 'bug', 'exceção', 'problema'],
            'sql': ['sql', 'query', 'consulta', 'banco', 'database', 'tabela'],
            'frontend': ['frontend', 'browser', 'javascript', 'página', 'site', 'web', 'carregamento'],
            'infra': ['servidor', 'infra', 'cpu', 'memória', 'rede', 'disk', 'cloud', 'azure'],
            'alertas': ['alerta', 'incidente', 'notificação'],
            'causa_raiz': ['causa', 'raiz', 'root', 'cause', 'motivo', 'origem'],
            'tendencia': ['tendência', 'padrão', 'histórico', 'evolução'],
            'recomendacao': ['recomendação', 'sugestão', 'como melhorar', 'como resolver']
        }
        
        # Detecta tópicos na pergunta
        for topico, keywords in mapeamento_topicos.items():
            for keyword in keywords:
                if keyword in pergunta_lower:
                    topicos.append(topico)
                    break
        
        return topicos
    
    def _analisar_performance(self, entidades: List[Dict]) -> Dict:
        """Analisa métricas de performance entre entidades"""
        resultado = {
            'entidades_lentas': [],
            'metricas_destacadas': {},
            'analise': ""
        }
        
        # Análise de performance
        entidades_com_apdex = []
        entidades_com_latencia = []
        
        for entidade in entidades:
            metricas = entidade.get('metricas', {})
            if not metricas:
                continue
                
            # Analisa métricas dos últimos 30 minutos
            periodo_30min = metricas.get('30min', {})
            
            # Verifica Apdex
            if periodo_30min and 'apdex' in periodo_30min:
                apdex_data = periodo_30min['apdex']
                if apdex_data and isinstance(apdex_data, list) and apdex_data[0]:
                    apdex = apdex_data[0].get('score')
                    if apdex is not None and apdex < 0.85:  # Apdex abaixo do ideal
                        entidades_com_apdex.append({
                            'nome': entidade.get('name', 'Desconhecido'),
                            'tipo': entidade.get('domain', 'Desconhecido'),
                            'apdex': apdex,
                            'guid': entidade.get('guid')
                        })
            
            # Verifica latência
            if periodo_30min and 'response_time_max' in periodo_30min:
                latencia_data = periodo_30min['response_time_max']
                if latencia_data and isinstance(latencia_data, list) and latencia_data[0]:
                    latencia = latencia_data[0].get('max.duration')
                    if latencia is not None and latencia > 1.0:  # Latência alta (>1s)
                        entidades_com_latencia.append({
                            'nome': entidade.get('name', 'Desconhecido'),
                            'tipo': entidade.get('domain', 'Desconhecido'),
                            'latencia': latencia,
                            'guid': entidade.get('guid')
                        })
        
        # Ordena entidades por problemas de performance
        entidades_com_apdex.sort(key=lambda x: x.get('apdex', 1.0))
        entidades_com_latencia.sort(key=lambda x: x.get('latencia', 0), reverse=True)
        
        # Compila resultados
        resultado['entidades_lentas'] = {
            'por_apdex': entidades_com_apdex[:5],  # Top 5 piores Apdex
            'por_latencia': entidades_com_latencia[:5]  # Top 5 maiores latências
        }
        
        # Estatísticas gerais
        if entidades_com_apdex:
            apdex_medio = sum(e.get('apdex', 0) for e in entidades_com_apdex) / len(entidades_com_apdex)
            resultado['metricas_destacadas']['apdex_medio'] = round(apdex_medio, 2)
            
        if entidades_com_latencia:
            latencia_media = sum(e.get('latencia', 0) for e in entidades_com_latencia) / len(entidades_com_latencia)
            resultado['metricas_destacadas']['latencia_media'] = round(latencia_media, 2)
        
        # Gera análise textual
        if entidades_com_apdex or entidades_com_latencia:
            analise = []
            if entidades_com_apdex:
                analise.append(f"Identificadas {len(entidades_com_apdex)} entidades com Apdex abaixo do ideal (<0.85)")
            if entidades_com_latencia:
                analise.append(f"Detectadas {len(entidades_com_latencia)} entidades com alta latência (>1s)")
                
            resultado['analise'] = " ".join(analise)
        else:
            resultado['analise'] = "Nenhum problema significativo de performance detectado."
        
        return resultado
    
    def _analisar_erros(self, entidades: List[Dict], alertas: List[Dict]) -> Dict:
        """Analisa erros e exceções nas entidades de forma detalhada"""
        resultado = {
            'entidades_com_erros': [],
            'padroes_erro': {},
            'alertas_relacionados': [],
            'logs_relevantes': [],
            'stacktraces': [],
            'erro_por_endpoint': {},
            'exemplos_completos': []  # Novos exemplos completos formatados
        }
        
        # Conta tipos de erros para detectar padrões
        contagem_tipos_erro = {}
        entidades_com_erro = []
        stacktraces_encontrados = []
        logs_encontrados = []
        endpoints_com_erro = {}
        
        for entidade in entidades:
            nome_entidade = entidade.get('name', 'Desconhecido')
            tipo_entidade = entidade.get('domain', 'Desconhecido')
            guid = entidade.get('guid', '')
            
            # Verificando métricas relacionadas a erros
            metricas = entidade.get('metricas', {})
            if not metricas:
                continue
            
            # Verifica métricas dos últimos 30 minutos e 24 horas
            for periodo_key, periodo_data in metricas.items():
                if not periodo_data:
                    continue
                
                # 1. Verificando taxa de erros (error_rate)
                taxa_erro = None
                if 'error_rate' in periodo_data:
                    error_data = periodo_data['error_rate']
                    if error_data and isinstance(error_data, list) and len(error_data) > 0:
                        taxa_erro = error_data[0].get('error.rate')
                
                # 2. Verificando erros recentes (recent_error) - formato completo com detalhes
                if 'recent_error' in periodo_data:
                    recent_errors = periodo_data['recent_error']
                    if recent_errors and isinstance(recent_errors, list):
                        for error in recent_errors:
                            # Extrai informações detalhadas do erro
                            tipo_erro = error.get('error.class') or error.get('type') or 'Erro Desconhecido'
                            mensagem = error.get('message') or error.get('error.message') or ''
                            transaction = error.get('transaction.name') or error.get('path') or ''
                            
                            # Registro para análise por endpoint
                            if transaction:
                                if transaction not in endpoints_com_erro:
                                    endpoints_com_erro[transaction] = {
                                        'contagem': 0,
                                        'tipos_erro': {},
                                        'entidades': set()
                                    }
                                endpoints_com_erro[transaction]['contagem'] += 1
                                endpoints_com_erro[transaction]['entidades'].add(nome_entidade)
                                
                                if tipo_erro in endpoints_com_erro[transaction]['tipos_erro']:
                                    endpoints_com_erro[transaction]['tipos_erro'][tipo_erro] += 1
                                else:
                                    endpoints_com_erro[transaction]['tipos_erro'][tipo_erro] = 1
                            
                            # Incrementa contagem para este tipo de erro
                            if tipo_erro in contagem_tipos_erro:
                                contagem_tipos_erro[tipo_erro] += 1
                            else:
                                contagem_tipos_erro[tipo_erro] = 1
                            
                            # Extrai o stacktrace completo
                            stacktrace = error.get('stack') or error.get('error.stack') or error.get('stacktrace') or ''
                            
                            # Armazene os 2-3 exemplos completos mais detalhados para análise profunda
                            if len(resultado['exemplos_completos']) < 3 and stacktrace and len(stacktrace) > 50:
                                # Formata o stacktrace para melhor legibilidade
                                stacktrace_formatado = self._formatar_stacktrace(stacktrace)
                                
                                resultado['exemplos_completos'].append({
                                    'entidade': nome_entidade,
                                    'tipo_erro': tipo_erro,
                                    'mensagem': mensagem,
                                    'transaction': transaction,
                                    'stacktrace': stacktrace_formatado,
                                    'timestamp': error.get('timestamp'),
                                    'formatted': f"""
# Erro em {nome_entidade} ({transaction})

**Tipo**: `{tipo_erro}`
**Mensagem**: {mensagem}
**Timestamp**: {error.get('timestamp')}

```stacktrace
{stacktrace_formatado}
```
"""
                                })
                            
                            if stacktrace and len(stacktrace) > 10:  # Garante que não seja vazio ou muito curto
                                stacktraces_encontrados.append({
                                    'entidade': nome_entidade,
                                    'tipo_entidade': tipo_entidade,
                                    'tipo_erro': tipo_erro,
                                    'mensagem': mensagem,
                                    'transaction': transaction,
                                    'stacktrace': stacktrace,
                                    'timestamp': error.get('timestamp'),
                                    'guid': guid
                                })
                
                # 3. Verificando logs relacionados a erros
                if 'logs' in periodo_data:
                    logs_data = periodo_data['logs']
                    if logs_data and isinstance(logs_data, list):
                        for log in logs_data:
                            # Procura por logs de erro (normalmente nível ERROR ou SEVERE)
                            nivel = log.get('level', '').upper()
                            mensagem_log = log.get('message', '')
                            
                            # Se for um log de erro ou contém palavras-chave de erro
                            if (nivel in ['ERROR', 'SEVERE', 'CRITICAL', 'FATAL']) or \
                               any(termo in mensagem_log.lower() for termo in ['error', 'exception', 'fail', 'crashed']):
                                # Formata o log para melhor legibilidade
                                log_formatado = self._formatar_log(log)
                                
                                logs_encontrados.append({
                                    'entidade': nome_entidade,
                                    'tipo_entidade': tipo_entidade,
                                    'nivel': nivel,
                                    'mensagem': mensagem_log,
                                    'timestamp': log.get('timestamp'),
                                    'contexto_adicional': log.get('context', {}),
                                    'guid': guid,
                                    'formatted': log_formatado
                                })
            
            # Adiciona à lista de entidades com erro se taxa de erro > 0 ou stacktrace encontrado
            if (taxa_erro and taxa_erro > 0) or any(st['entidade'] == nome_entidade for st in stacktraces_encontrados):
                entidades_com_erro.append({
                    'nome': nome_entidade,
                    'tipo': tipo_entidade,
                    'taxa_erro': taxa_erro,
                    'guid': guid,
                    'tem_stacktrace': any(st['entidade'] == nome_entidade for st in stacktraces_encontrados),
                    'num_erros_recentes': len([st for st in stacktraces_encontrados if st['entidade'] == nome_entidade])
                })
        
        # Adiciona alertas relacionados a erros
        alertas_erro = []
        for alerta in alertas:
            if any(termo in alerta.get('nome', '').lower() for termo in ['erro', 'error', 'exception', 'falha', 'failure']):
                alertas_erro.append(alerta)
        
        # Ordena stacktraces e logs por timestamp (mais recentes primeiro)
        stacktraces_encontrados.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        logs_encontrados.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Cria estrutura organizada de erros por endpoint
        endpoints_organizados = []
        for endpoint, dados in endpoints_com_erro.items():
            tipos_erro_ordenados = sorted(dados['tipos_erro'].items(), key=lambda x: x[1], reverse=True)
            endpoints_organizados.append({
                'endpoint': endpoint,
                'contagem': dados['contagem'],
                'entidades': list(dados['entidades']),
                'principais_erros': tipos_erro_ordenados
            })
        
        # Ordena endpoints por contagem de erros
        endpoints_organizados.sort(key=lambda x: x['contagem'], reverse=True)
        
        # Compila os resultados finais
        resultado['entidades_com_erros'] = entidades_com_erro
        resultado['padroes_erro'] = {
            'contagem_por_tipo': contagem_tipos_erro,
            'total_erros': sum(contagem_tipos_erro.values())
        }
        resultado['alertas_relacionados'] = alertas_erro
        resultado['logs_relevantes'] = logs_encontrados[:20]  # Limita a 20 logs mais relevantes
        resultado['stacktraces'] = stacktraces_encontrados[:15]  # Aumentado para 15 stacktraces
        resultado['erro_por_endpoint'] = endpoints_organizados[:10]  # Top 10 endpoints com erro
        
        # Análise textual
        analise = []
        
        if entidades_com_erro:
            analise.append(f"Identificadas {len(entidades_com_erro)} entidades com erros.")
            
        if contagem_tipos_erro:
            top_erros = sorted(contagem_tipos_erro.items(), key=lambda x: x[1], reverse=True)[:3]
            analise.append(f"Principais tipos de erro: " + ", ".join([f"{tipo} ({contagem})" for tipo, contagem in top_erros]))
            
        if endpoints_organizados:
            top_endpoints = endpoints_organizados[:3]
            analise.append(f"Top endpoints com erro: " + ", ".join([f"{e['endpoint']} ({e['contagem']})" for e in top_endpoints]))
            
        if stacktraces_encontrados:
            analise.append(f"Encontrados {len(stacktraces_encontrados)} stacktraces completos para análise.")
            
        if logs_encontrados:
            analise.append(f"Coletados {len(logs_encontrados)} logs de erro relevantes.")
            
        resultado['analise'] = " ".join(analise) if analise else "Nenhum erro significativo detectado no período analisado."
        
        return resultado
    
    def _analisar_correlacoes(self, entidades, alertas):
        """
        Analisa correlações entre entidades e alertas para identificar padrões
        e possíveis relações causais.
        
        Args:
            entidades (list): Lista de entidades para análise
            alertas (list): Lista de alertas ativos
            
        Returns:
            dict: Dicionário com correlações identificadas
        """
        logger.info("Analisando correlações entre entidades e alertas...")
        correlacoes = {
            "padroes": [],
            "relacionamentos": [],
            "causas_potenciais": []
        }
        
        # Implementação básica inicial
        if not entidades or len(entidades) < 2:
            logger.info("Poucas entidades para análise de correlação")
            return correlacoes
            
        try:
            # Identificar entidades com problemas semelhantes
            entidades_com_erros = [e for e in entidades if e.get('errorRate', 0) > 2]
            entidades_com_latencia = [e for e in entidades if e.get('responseTime', 0) > 1000]
            
            # Detectar correlações por domínio
            dominios = {}
            for entidade in entidades:
                dominio = entidade.get('domain', 'desconhecido')
                if dominio not in dominios:
                    dominios[dominio] = []
                dominios[dominio].append(entidade)
            
            # Identificar relações por domínio
            for dominio, ents in dominios.items():
                if len(ents) > 1:
                    correlacoes["relacionamentos"].append({
                        "tipo": "dominio",
                        "valor": dominio,
                        "entidades": len(ents),
                        "saude_media": sum(e.get('health', 0) for e in ents) / len(ents)
                    })
            
            # Analisar entidades com problemas
            if entidades_com_erros and entidades_com_latencia:
                # Verificar sobreposição
                erros_guids = [e.get('guid') for e in entidades_com_erros]
                latencia_guids = [e.get('guid') for e in entidades_com_latencia]
                
                overlap = set(erros_guids).intersection(set(latencia_guids))
                if overlap:
                    correlacoes["padroes"].append({
                        "tipo": "erro_latencia",
                        "descricao": f"{len(overlap)} entidades apresentam tanto erros quanto alta latência",
                        "severidade": "alta"
                    })
                    
                    # Identificar possíveis causas
                    correlacoes["causas_potenciais"].append({
                        "tipo": "sobrecarga",
                        "descricao": "Possível sobrecarga de sistema afetando múltiplas entidades",
                        "confianca": 0.7,
                        "entidades_afetadas": list(overlap)
                    })
            
            # Analisar correlação com alertas
            if alertas:
                for alerta in alertas:
                    entidades_relacionadas = [
                        e for e in entidades 
                        if e.get('guid') == alerta.get('entityGuid') or 
                           e.get('name') == alerta.get('entityName')
                    ]
                    
                    if entidades_relacionadas:
                        correlacoes["padroes"].append({
                            "tipo": "alerta_entidade",
                            "descricao": f"Alerta '{alerta.get('name')}' relacionado a {len(entidades_relacionadas)} entidades",
                            "severidade": alerta.get('severity', 'média')
                        })
                        
            logger.info(f"Análise de correlação concluída: {len(correlacoes['padroes'])} padrões, "
                           f"{len(correlacoes['relacionamentos'])} relacionamentos, "
                           f"{len(correlacoes['causas_potenciais'])} causas potenciais")
                           
        except Exception as e:
            logger.error(f"Erro na análise de correlações: {str(e)}")
            logger.debug(traceback.format_exc())
            
        return correlacoes
    
    def _formatar_stacktrace(self, stacktrace: str) -> str:
        """
        Formata um stacktrace para melhor legibilidade
        
        Args:
            stacktrace: O stacktrace a ser formatado
            
        Returns:
            Stacktrace formatado
        """
        if not stacktrace:
            return ""
            
        # Se já for formatado com quebras de linha, retorna como está
        if "\n" in stacktrace:
            return stacktrace
            
        # Tenta formatar stacktraces em formato compacto
        try:
            linhas = []
            frames = re.findall(r"at\s+([^\s]+)\s+\(([^)]+)\)", stacktrace)
            
            if frames:
                linhas.append("Stacktrace:")
                for i, (metodo, local) in enumerate(frames):
                    linhas.append(f"{i+1}. {metodo} em {local}")
                return "\n".join(linhas)
                
            # Formato Python
            frames = re.findall(r"File\s+\"([^\"]+)\",\s+line\s+(\d+),\s+in\s+(.+)", stacktrace)
            if frames:
                linhas.append("Stacktrace:")
                for i, (arquivo, linha, metodo) in enumerate(frames):
                    nome_arquivo = arquivo.split("/")[-1] if "/" in arquivo else arquivo.split("\\")[-1] if "\\" in arquivo else arquivo
                    linhas.append(f"{i+1}. {nome_arquivo}:{linha} - {metodo}")
                return "\n".join(linhas)
                
            # Se não conseguir formatar, retorna como está
            return stacktrace
            
        except Exception:
            # Em caso de erro na formatação, retorna o stacktrace original
            return stacktrace
        try:
            # Substitui "at" por quebras de linha + at para melhor legibilidade
            formatted = stacktrace.replace(" at ", "\n    at ")
            
            # Adiciona quebras de linha após exceções comuns
            for exception in ["Exception", "Error", "Throwable"]:
                formatted = formatted.replace(exception + ":", exception + ":\n")
                
            return formatted
        except Exception:
            # Em caso de erro, retorna o stacktrace original
            return stacktrace
    
    def _formatar_log(self, log: dict) -> str:
        """
        Formata um registro de log para melhor legibilidade
        
        Args:
            log: Dicionário contendo as informações do log
            
        Returns:
            Log formatado como string
        """
        timestamp = log.get('timestamp', '')
        level = log.get('level', 'INFO')
        message = log.get('message', '')
        context = log.get('context', {})
        
        # Formata o contexto como JSON se existir
        context_str = ""
        if context:
            try:
                context_str = "\nContexto: " + json.dumps(context, indent=2)
            except:
                context_str = "\nContexto: " + str(context)
        
        return f"[{timestamp}] {level}: {message}{context_str}"

# Instância global para uso em outros módulos
context_enricher = ContextEnricher()
