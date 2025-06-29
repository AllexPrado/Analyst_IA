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
        """
        Detecta tópicos relevantes na pergunta do usuário.
        Versão expandida para capturar uma gama mais ampla de tópicos e subtópicos,
        garantindo análise completa de todos os aspectos do ambiente monitorado.
        """
        pergunta_lower = pergunta.lower()
        topicos = []
        
        # Mapeia palavras-chave para tópicos - versão expandida
        mapeamento_topicos = {
            # Performance e latência
            'performance': ['performance', 'lent', 'lenta', 'devagar', 'latência', 'apdex', 'resposta', 'throughput', 'tempo', 'carregamento', 
                           'otimiz', 'velocidade', 'rápid', 'demorad', 'lerdo', 'millisegundo', 'segundo', 'performance', 'desempenho',
                           'responsividade', 'responsivo', 'carga', 'benchmark', 'transaction', 'transação'],
            
            # Erros, exceções e problemas
            'erro': ['erro', 'crash', 'exception', 'falha', 'bug', 'problema', 'crítico', 'alerta', 'incidente', 'exceção',
                    'traceback', 'stack trace', 'stacktrace', 'error rate', 'taxa de erro', 'failure', 'failed', 'timeout',
                    'code', 'status', 'http 5', 'http 4', 'quebrado', 'interrompido', 'panic', 'fatal', 'quebra'],
            
            # Banco de dados e queries
            'database': ['sql', 'database', 'banco de dados', 'query', 'db', 'consulta', 'índice', 'index', 'tabela', 'join',
                        'relacionamento', 'foreign key', 'primary key', 'procedure', 'stored procedure', 'trigger', 'transaction',
                        'commit', 'rollback', 'lock', 'deadlock', 'row', 'column', 'select', 'insert', 'update', 'delete',
                        'slow query', 'consulta lenta', 'postgre', 'mysql', 'oracle', 'sqlserver', 'mongodb', 'nosql'],
            
            # Frontend e experiência do usuário
            'frontend': ['frontend', 'browser', 'javascript', 'css', 'html', 'web', 'página', 'interface', 'ui', 'usuario', 'cliente',
                        'ajax', 'xhr', 'fetch', 'dom', 'render', 'spa', 'single page', 'react', 'angular', 'vue', 'webpack',
                        'web vital', 'lcp', 'fid', 'cls', 'ttfb', 'first paint', 'first contentful', 'core web vital',
                        'experiência', 'ux', 'usabilidade', 'mobile', 'responsivo', 'navegador', 'chrome', 'firefox', 'safari'],
            
            # Backend e APIs
            'backend': ['backend', 'api', 'serviço', 'microserviço', 'serviços', 'apm', 'função', 'método', 'controller',
                       'endpoint', 'rest', 'soap', 'graphql', 'grpc', 'websocket', 'http', 'https', 'post', 'get', 'put',
                       'delete', 'patch', 'middleware', 'gateway', 'load balancer', 'proxy', 'reverse proxy', 'serverless',
                       'lambda', 'function', 'rotas', 'request', 'response'],
            
            # Infraestrutura e recursos
            'infra': ['servidor', 'infra', 'infraestrutura', 'cpu', 'memória', 'disco', 'rede', 'network', 'host', 'vm', 'container',
                     'kubernetes', 'k8s', 'docker', 'escalabilidade', 'nuvem', 'cloud', 'aws', 'azure', 'gcp', 'datacenter',
                     'hardware', 'virtualização', 'storage', 'armazenamento', 'load', 'carga', 'consumo', 'throughput',
                     'bandwidth', 'largura de banda', 'latency', 'jitter', 'packet loss', 'perda de pacote', 'firewall',
                     'dns', 'http', 'tcp', 'udp', 'ip', 'ipv4', 'ipv6', 'tls', 'ssl', 'cdn', 'tráfego', 'traffic'],
            
            # Logs e monitoramento
            'log': ['log', 'trace', 'stack', 'depuração', 'debug', 'monitoramento', 'alerta', 'logging', 'rastreamento',
                   'audit', 'auditoria', 'event', 'evento', 'registro', 'record', 'monitorar', 'observabilidade',
                   'telemetria', 'trace', 'span', 'distributed tracing', 'rastreamento distribuído', 'correlation id'],
            
            # Tendências e análise histórica
            'tendencia': ['tendência', 'histórico', 'comparação', 'baseline', 'anomalia', 'padrão', 'sazonalidade', 'previsto',
                         'forecast', 'previsão', 'projeção', 'regressão', 'crescimento', 'queda', 'pico', 'valley', 'vale',
                         'outlier', 'desvio', 'normalidade', 'anormal', 'média', 'mediana', 'percentil', 'correlação',
                         'causa raiz', 'causa-efeito', 'root cause', 'machine learning', 'ai', 'previsão'],
            
            # Segurança e compliance
            'security': ['segurança', 'vulnerabilidade', 'ataque', 'acesso', 'autenticação', 'autorização', 'token',
                        'jwt', 'oauth', 'permissão', 'privilégio', 'brute force', 'força bruta', 'sql injection',
                        'xss', 'csrf', 'cross-site', 'ddos', 'firewall', 'waf', 'criptografia', 'encryption',
                        'password', 'senha', 'hash', 'certificado', 'compliance', 'gdpr', 'lgpd', 'pci', 'hipaa',
                        'vazamento', 'data breach', 'incident', 'incidente', 'malware', 'vírus', 'trojan', 'ransomware'],
                        
            # Métricas e visualizações
            'metricas': ['gráfico', 'dashboard', 'métrica', 'kpi', 'indicador', 'sli', 'slo', 'sla', 'objective', 'objetivo',
                        'meta', 'target', 'threshold', 'limite', 'orçamento', 'budget', 'disponibilidade', 'availability',
                        'reliabilidade', 'reliability', 'visualização', 'visualization', 'monitor', 'alert', 'alerta',
                        'notification', 'notificação', 'relatorio', 'report'],
                        
            # Mobile e aplicativos
            'mobile': ['mobile', 'app', 'aplicativo', 'android', 'ios', 'smartphone', 'tablet', 'cellular', 'celular',
                      'push notification', 'notificação', 'crash', 'anr', 'not responding', 'freeze', 'travamento',
                      'battery', 'bateria', 'offline', 'online', 'sincronização', 'sync'],
                      
            # Custo e eficiência
            'custo': ['custo', 'gasto', 'despesa', 'economia', 'otimização', 'redução', 'cloud cost', 'billing', 'fatura',
                     'cobrança', 'orçamento', 'budget', 'uso', 'utilização', 'eficiência', 'rightsizing', 'saving', 'economia'],
                     
            # Resiliência e confiabilidade
            'resiliencia': ['resiliência', 'confiabilidade', 'failover', 'disaster recovery', 'recuperação', 'circuit breaker',
                           'retry', 'retentativa', 'backoff', 'timeout', 'fallback', 'degradação', 'graceful', 'gracioso', 
                           'self-healing', 'auto-recuperação', 'alta disponibilidade', 'high availability', 'redundância']
        }
        
        # Verifica cada tópico com detecção avançada de contexto
        for topico, palavras_chave in mapeamento_topicos.items():
            # Verifica correspondência exata de palavras ou partes de palavras
            if any(palavra in pergunta_lower for palavra in palavras_chave):
                topicos.append(topico)
            # Verifica correspondências parciais em palavras longas
            elif any(any(palavra in word for word in pergunta_lower.split()) for palavra in palavras_chave if len(palavra) > 4):
                topicos.append(topico)
        
        # Detecção de casos específicos com alta prioridade
        if 'critico' in pergunta_lower or 'crítico' in pergunta_lower or 'urgente' in pergunta_lower:
            if 'erro' not in topicos:
                topicos.append('erro')
            
        if 'lent' in pergunta_lower and 'api' in pergunta_lower:
            if 'performance' not in topicos:
                topicos.append('performance')
            if 'backend' not in topicos:
                topicos.append('backend')
        
        if ('sql' in pergunta_lower and ('lent' in pergunta_lower or 'performance' in pergunta_lower)):
            if 'database' not in topicos:
                topicos.append('database')
            if 'performance' not in topicos:
                topicos.append('performance')
        
        # Se não detectou nenhum tópico específico, adiciona tópico geral
        if not topicos:
            topicos.append('geral')
            
        return topicos
    
    def _analisar_performance(self, entidades: List[Dict]) -> Dict:
        """
        Análise avançada de métricas de performance entre entidades.
        Examina múltiplas dimensões de performance: latência, throughput, apdex, erros e tendências.
        """
        resultado = {
            'entidades_lentas': {},
            'metricas_destacadas': {},
            'analise': "",
            'gargalos_identificados': [],
            'correlacoes_performance': [],
            'tendencias_performance': []
        }
        
        # Arrays para diferentes métricas de performance
        entidades_com_apdex = []
        entidades_com_latencia = []
        entidades_com_throughput_anormal = []
        entidades_com_degradacao = []
        endpoints_mais_usados = []
        
        # Valores agregados para análise holística
        total_requests = 0
        total_erros = 0
        latencia_media_global = []
        apdex_medio_global = []
        
        for entidade in entidades:
            nome = entidade.get('name', 'Desconhecido')
            tipo = entidade.get('domain', 'Desconhecido')
            guid = entidade.get('guid', 'sem-guid')
            
            metricas = entidade.get('metricas', {})
            if not metricas:
                continue
                
            # Análise dos últimos 30 minutos
            periodo_30min = metricas.get('30min', {})
            if not periodo_30min:
                continue
            
            # Extração avançada de métricas de performance
            performance_metrics = {
                'apdex': None,
                'latencia_max': None,
                'latencia_avg': None,
                'throughput': None,
                'erros': 0,
                'taxa_erro': None,
                'cpu': None,
                'memory': None,
                'saturation': None,
                'top_endpoints': []
            }
            
            # Extrai Apdex (satisfação do usuário)
            if 'apdex' in periodo_30min and periodo_30min['apdex'] and isinstance(periodo_30min['apdex'], list) and periodo_30min['apdex'][0]:
                apdex = periodo_30min['apdex'][0].get('score')
                performance_metrics['apdex'] = apdex
                
                if apdex is not None:
                    apdex_medio_global.append(apdex)
                    
                    # Categoriza por severidade do problema de Apdex
                    if apdex < 0.7:  # Ruim
                        severidade = "crítico"
                    elif apdex < 0.85:  # Abaixo do ideal
                        severidade = "alerta"
                    else:
                        severidade = "ok"
                        
                    if apdex < 0.85:  # Somente adiciona se estiver abaixo do ideal
                        entidades_com_apdex.append({
                            'nome': nome,
                            'tipo': tipo,
                            'apdex': apdex,
                            'guid': guid,
                            'severidade': severidade
                        })
            
            # Extrai latência (max e avg)
            if 'response_time_max' in periodo_30min and periodo_30min['response_time_max'] and isinstance(periodo_30min['response_time_max'], list):
                latencia_max = periodo_30min['response_time_max'][0].get('max.duration') if periodo_30min['response_time_max'][0] else None
                performance_metrics['latencia_max'] = latencia_max
                
                if latencia_max is not None:
                    latencia_media_global.append(latencia_max)
                    
                    # Categoriza por severidade do problema de latência
                    if latencia_max > 3.0:  # Extremamente lento
                        severidade = "crítico"
                    elif latencia_max > 1.0:  # Lento
                        severidade = "alerta"
                    else:
                        severidade = "ok"
                        
                    if latencia_max > 1.0:  # Somente adiciona se for lento
                        entidades_com_latencia.append({
                            'nome': nome,
                            'tipo': tipo,
                            'latencia': latencia_max,
                            'guid': guid,
                            'severidade': severidade
                        })
            
            # Extrai throughput (qps - queries por segundo)
            if 'throughput' in periodo_30min and periodo_30min['throughput'] and isinstance(periodo_30min['throughput'], list):
                throughput = periodo_30min['throughput'][0].get('avg.qps') if periodo_30min['throughput'][0] else None
                performance_metrics['throughput'] = throughput
                
                if throughput is not None:
                    total_requests += throughput
                    
                    # Detecta anomalias em throughput (muito alto ou muito baixo)
                    if throughput > 100:  # Alto volume
                        entidades_com_throughput_anormal.append({
                            'nome': nome,
                            'tipo': tipo,
                            'throughput': throughput,
                            'guid': guid,
                            'anomalia': 'alto_volume'
                        })
                    elif throughput < 0.1 and tipo != 'INFRA':  # Volume muito baixo (exceto para infra)
                        entidades_com_throughput_anormal.append({
                            'nome': nome,
                            'tipo': tipo,
                            'throughput': throughput,
                            'guid': guid,
                            'anomalia': 'volume_baixo'
                        })
            
            # Extrai erros
            if 'recent_error' in periodo_30min:
                erros = periodo_30min['recent_error']
                num_erros = len(erros) if isinstance(erros, list) else 0
                performance_metrics['erros'] = num_erros
                total_erros += num_erros
                
                # Calcula taxa de erro se tiver throughput
                if performance_metrics['throughput'] and performance_metrics['throughput'] > 0:
                    taxa_erro = min(100, (num_erros / performance_metrics['throughput']) * 100) if performance_metrics['throughput'] > 0 else 0
                    performance_metrics['taxa_erro'] = taxa_erro
        
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
        
        # Detecção de degradação comparando com 24h atrás
        periodo_24h = metricas.get('24h', {})
        if periodo_24h:
            # Comparação de latência com 24h atrás
            latencia_24h = None
            if 'response_time_max' in periodo_24h and periodo_24h['response_time_max'] and isinstance(periodo_24h['response_time_max'], list):
                latencia_24h = periodo_24h['response_time_max'][0].get('max.duration') if periodo_24h['response_time_max'][0] else None
            
            if latencia_24h and performance_metrics['latencia_max']:
                # Detecta degradação de latência maior que 25%
                if performance_metrics['latencia_max'] > (latencia_24h * 1.25) and performance_metrics['latencia_max'] > 0.5:
                    entidades_com_degradacao.append({
                        'nome': nome,
                        'tipo': tipo,
                        'latencia_atual': performance_metrics['latencia_max'],
                        'latencia_anterior': latencia_24h,
                        'aumento_percentual': round(((performance_metrics['latencia_max'] - latencia_24h) / latencia_24h) * 100, 1),
                        'guid': guid
                    })
        
        # Extrai consumo de CPU e memória para serviços APM 
        if 'cpu' in periodo_30min and periodo_30min['cpu'] and isinstance(periodo_30min['cpu'], list):
            cpu_usage = periodo_30min['cpu'][0].get('avg.usage') if periodo_30min['cpu'][0] else None
            performance_metrics['cpu'] = cpu_usage
            
        if 'memory' in periodo_30min and periodo_30min['memory'] and isinstance(periodo_30min['memory'], list):
            memory_usage = periodo_30min['memory'][0].get('avg.usage') if periodo_30min['memory'][0] else None
            performance_metrics['memory'] = memory_usage
            
        # Detecção avançada: extração de endpoints mais usados
        if 'top_endpoints' in periodo_30min and periodo_30min['top_endpoints'] and isinstance(periodo_30min['top_endpoints'], list):
            for endpoint in periodo_30min['top_endpoints'][:5]:  # Top 5 endpoints
                if endpoint:
                    endpoints_mais_usados.append({
                        'entidade': nome,
                        'endpoint': endpoint.get('name', 'Desconhecido'),
                        'latencia': endpoint.get('avg.duration', 0),
                        'throughput': endpoint.get('avg.qps', 0)
                    })
        
        # Ordena entidades por problemas de performance
        entidades_com_apdex.sort(key=lambda x: x.get('apdex', 1.0))
        entidades_com_latencia.sort(key=lambda x: x.get('latencia', 0), reverse=True)
        entidades_com_degradacao.sort(key=lambda x: x.get('aumento_percentual', 0), reverse=True)
        endpoints_mais_usados.sort(key=lambda x: x.get('latencia', 0), reverse=True)
        
        # Identifica possíveis gargalos com base nas métricas
        gargalos = []
        
        # Gargalos baseados em latência extrema
        for entidade in entidades_com_latencia[:3]:  # Top 3 mais lentas
            if entidade.get('severidade') == "crítico":
                gargalos.append({
                    'tipo': 'latencia_critica',
                    'entidade': entidade.get('nome'),
                    'valor': f"{entidade.get('latencia', 0):.2f}s",
                    'recomendacao': "Investigar urgentemente bottlenecks, queries SQL lentas ou bloqueios"
                })
        
        # Gargalos baseados em degradação recente
        for entidade in entidades_com_degradacao[:3]:  # Top 3 com maior degradação
            if entidade.get('aumento_percentual', 0) > 50:  # Aumento de mais de 50%
                gargalos.append({
                    'tipo': 'degradacao_recente',
                    'entidade': entidade.get('nome'),
                    'valor': f"+{entidade.get('aumento_percentual', 0):.1f}%",
                    'recomendacao': "Verificar mudanças recentes, deploy ou alterações de configuração"
                })
        
        # Busca correlações entre problemas de performance
        correlacoes = []
        
        # Correlação entre latência e Apdex baixo
        entidades_criticas = set([e.get('nome') for e in entidades_com_latencia if e.get('severidade') == "crítico"])
        entidades_apdex_baixo = set([e.get('nome') for e in entidades_com_apdex if e.get('apdex', 1.0) < 0.7])
        
        # Entidades que aparecem em ambas as listas têm problema grave
        entidades_problema_duplo = entidades_criticas.intersection(entidades_apdex_baixo)
        if entidades_problema_duplo:
            correlacoes.append({
                'tipo': 'latencia_apdex',
                'entidades': list(entidades_problema_duplo),
                'analise': f"Entidades com problemas críticos tanto de latência quanto de satisfação do usuário (Apdex)",
                'severidade': 'crítico'
            })
        
        # Compila resultados
        resultado['entidades_lentas'] = {
            'por_apdex': entidades_com_apdex[:10],  # Limita para os 10 piores
            'por_latencia': entidades_com_latencia[:10],  # Limita para os 10 piores
            'com_degradacao': entidades_com_degradacao[:5]  # Top 5 com degradação
        }
        resultado['gargalos_identificados'] = gargalos
        resultado['correlacoes_performance'] = correlacoes
        resultado['endpoints_lentos'] = endpoints_mais_usados[:10]
        
        # Métricas agregadas
        if apdex_medio_global:
            resultado['metricas_destacadas']['apdex_medio_global'] = round(sum(apdex_medio_global) / len(apdex_medio_global), 2)
        
        if latencia_media_global:
            resultado['metricas_destacadas']['latencia_media_global'] = round(sum(latencia_media_global) / len(latencia_media_global), 2)
        
        resultado['metricas_destacadas']['total_requests'] = round(total_requests, 1)
        resultado['metricas_destacadas']['total_erros'] = total_erros
        
        # Gera análise textual avançada
        analises = []
        
        # Análise de problemas de Apdex
        if entidades_com_apdex:
            criticas = len([e for e in entidades_com_apdex if e.get('severidade') == 'crítico'])
            alerta = len([e for e in entidades_com_apdex if e.get('severidade') == 'alerta'])
            
            if criticas > 0:
                analises.append(f"Crítico: {criticas} entidades com Apdex extremamente baixo (<0.7), indicando sérios problemas de satisfação do usuário.")
            if alerta > 0:
                analises.append(f"Alerta: {alerta} entidades com Apdex abaixo do ideal (<0.85), requerendo atenção.")
                
        # Análise de problemas de latência
        if entidades_com_latencia:
            criticas = len([e for e in entidades_com_latencia if e.get('severidade') == 'crítico'])
            alerta = len([e for e in entidades_com_latencia if e.get('severidade') == 'alerta'])
            
            if criticas > 0:
                analises.append(f"Crítico: {criticas} entidades com latência extremamente alta (>3s), causando experiência ruim ao usuário.")
            if alerta > 0:
                analises.append(f"Alerta: {alerta} entidades com latência alta (>1s), requerendo otimização.")
                
        # Análise de degradação
        if entidades_com_degradacao:
            total_degradacao = len(entidades_com_degradacao)
            degradacao_grave = len([e for e in entidades_com_degradacao if e.get('aumento_percentual', 0) > 50])
            
            if degradacao_grave > 0:
                analises.append(f"Alerta: {degradacao_grave} entidades com degradação severa de performance (>50%) nas últimas 24h.")
            elif total_degradacao > 0:
                analises.append(f"Observação: {total_degradacao} entidades apresentam degradação de performance nas últimas 24h.")
                
        # Análise de gargalos identificados
        if gargalos:
            analises.append(f"Identificados {len(gargalos)} potenciais gargalos no sistema que precisam de atenção imediata.")
            
        # Conclusão
        if analises:
            resultado['analise'] = " ".join(analises)
        else:
            resultado['analise'] = "Nenhum problema significativo de performance detectado no ambiente."
        
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
    
    def _analisar_correlacoes(self, entidades: List[Dict], alertas: List[Dict]) -> Dict:
        """
        Analisa correlações entre entidades e alertas para detectar padrões.
        Versão avançada com detecção de relações causais.
        """
        resultado = {
            'correlacoes_detectadas': [],
            'relacionamentos': {},
            'causas_potenciais': [],
            'analise': ""
        }
        
        try:
            # Se não tem dados suficientes para correlação
            if not entidades or len(entidades) <= 1:
                resultado['analise'] = "Não há entidades suficientes para análise de correlação."
                return resultado
            
            # Categoriza entidades por status
            entidades_por_status = {"ERRO": [], "ALERTA": [], "OK": []}
            entidades_com_erros = []
            entidades_com_latencia = []
            
            # Mapeia entidades para poder referenciar por nome/guid
            entidades_map = {}
            for e in entidades:
                nome = e.get('name')
                guid = e.get('guid')
                if nome:
                    entidades_map[nome] = e
                if guid:
                    entidades_map[guid] = e
                    
                # Determina status da entidade
                status = "OK"
                metricas = e.get('metricas', {}).get('30min', {})
                
                # Verifica erros
                erros = metricas.get('recent_error', [])
                if erros and len(erros) > 0:
                    status = "ERRO"
                    entidades_com_erros.append((nome, len(erros), erros[0].get('message', '') if erros[0] else ''))
                
                # Verifica latência alta
                latencia = None
                if 'response_time_max' in metricas and metricas['response_time_max']:
                    if isinstance(metricas['response_time_max'], list) and metricas['response_time_max'][0]:
                        latencia = metricas['response_time_max'][0].get('max.duration')
                        
                if latencia and latencia > 1.0:  # Mais de 1 segundo
                    if status == "OK":  # Não sobrescreve ERRO
                        status = "ALERTA"
                    entidades_com_latencia.append((nome, latencia))
                
                # Verifica Apdex baixo
                apdex = None
                if 'apdex' in metricas and metricas['apdex']:
                    if isinstance(metricas['apdex'], list) and metricas['apdex'][0]:
                        apdex = metricas['apdex'][0].get('score')
                        
                if apdex and apdex < 0.7:  # Apdex muito baixo
                    if status == "OK":  # Não sobrescreve ERRO ou ALERTA
                        status = "ALERTA"
                
                # Adiciona à categoria
                entidades_por_status[status].append(e)
            
            # Detecta correlações entre entidades em ERRO
            if entidades_por_status["ERRO"]:
                # Agrupa erros por tipo/mensagem
                erros_por_tipo = {}
                for nome, qtd, mensagem in entidades_com_erros:
                    erro_tipo = mensagem[:50]  # Usa os primeiros 50 chars como chave
                    if erro_tipo not in erros_por_tipo:
                        erros_por_tipo[erro_tipo] = []
                    erros_por_tipo[erro_tipo].append((nome, qtd))
                
                # Verifica erros do mesmo tipo em múltiplas entidades
                for erro_tipo, entidades_erro in erros_por_tipo.items():
                    if len(entidades_erro) > 1:
                        nomes_entidades = ", ".join([e[0] for e in entidades_erro])
                        resultado['correlacoes_detectadas'].append(
                            f"Erro comum detectado em múltiplas entidades ({nomes_entidades}): {erro_tipo}..."
                        )
                        
                        # Procura por causa comum
                        if len(entidades_erro) > 2:
                            resultado['causas_potenciais'].append(
                                f"Potencial problema sistêmico causando erros em {len(entidades_erro)} entidades"
                            )
            
            # Detecta correlações de latência
            if entidades_com_latencia:
                # Ordena por latência
                entidades_com_latencia.sort(key=lambda x: x[1], reverse=True)
                
                # Agrupa entidades com latência alta
                if len(entidades_com_latencia) > 1:
                    top_5 = entidades_com_latencia[:5]
                    nomes = ", ".join([e[0] for e in top_5])
                    valores = ", ".join([f"{e[1]:.2f}s" for e in top_5])
                    resultado['correlacoes_detectadas'].append(
                        f"Problema de latência afetando múltiplas entidades: {nomes} (valores: {valores})"
                    )
            
            # Constrói grafo de relacionamentos para análise de dependência
            # Uma análise básica conectando entidades que chamam umas às outras
            grafo_dependencias = {}
            
            # Para cada entidade, verifica suas transações para identificar relações
            for e in entidades:
                nome = e.get('name')
                metricas = e.get('metricas', {}).get('30min', {})
                
                # Procura por transações chamando outras entidades
                for metrica_nome, metrica_valor in metricas.items():
                    if 'extservice' in metrica_nome or 'external' in metrica_nome:
                        if not isinstance(metrica_valor, list):
                            continue
                        
                        for item in metrica_valor:
                            if isinstance(item, dict):
                                # Tenta encontrar nome da entidade chamada
                                service_name = item.get('name') or item.get('host') or item.get('target')
                                if service_name:
                                    # Adiciona relação no grafo
                                    if nome not in grafo_dependencias:
                                        grafo_dependencias[nome] = []
                                    if service_name not in grafo_dependencias[nome]:
                                        grafo_dependencias[nome].append(service_name)
                                        
                                        # Registra o relacionamento
                                        resultado['relacionamentos'][nome] = resultado['relacionamentos'].get(nome, [])
                                        resultado['relacionamentos'][nome].append(service_name)
            
            # Constrói lista de correlações a partir do grafo
            if grafo_dependencias:
                for origem, destinos in grafo_dependencias.items():
                    if destinos:
                        # Verifica se a origem está em ERRO e tem dependências
                        origem_entity = next((e for e in entidades if e.get('name') == origem), None)
                        if origem_entity and origem in [e[0] for e in entidades_com_erros]:
                            for destino in destinos:
                                destino_entity = next((e for e in entidades if e.get('name') == destino), None)
                                # Se o destino também está com erro, possível correlação
                                if destino_entity and destino in [e[0] for e in entidades_com_erros]:
                                    resultado['correlacoes_detectadas'].append(
                                        f"Possível propagação de erro: {origem} → {destino}"
                                    )
            
            # Análise de causa raiz - entidade que afeta mais outras
            if resultado['relacionamentos']:
                impacto_por_entidade = {}
                for origem, destinos in resultado['relacionamentos'].items():
                    impacto_por_entidade[origem] = len(destinos)
                
                # Ordena por impacto
                mais_impacto = sorted(impacto_por_entidade.items(), key=lambda x: x[1], reverse=True)
                if mais_impacto:
                    top_impacto = mais_impacto[0]
                    if top_impacto[1] > 1:  # Se afeta mais de uma entidade
                        # Verifica se está com erro
                        if top_impacto[0] in [e[0] for e in entidades_com_erros]:
                            resultado['causas_potenciais'].append(
                                f"Entidade {top_impacto[0]} pode ser causa raiz - afeta {top_impacto[1]} outras entidades"
                            )
            
            # Gera resumo da análise
            num_correlacoes = len(resultado['correlacoes_detectadas'])
            num_relacoes = sum(len(deps) for deps in resultado['relacionamentos'].values())
            num_causas = len(resultado['causas_potenciais'])
            
            resultado['analise'] = f"Análise de correlação concluída: {num_correlacoes} padrões, {num_relacoes} relacionamentos, {num_causas} causas potenciais"
            
            return resultado
        except Exception as e:
            logger.error(f"Erro na análise de correlação: {str(e)}")
            resultado['analise'] = f"Erro na análise de correlação: {str(e)}"
            return resultado
    
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
