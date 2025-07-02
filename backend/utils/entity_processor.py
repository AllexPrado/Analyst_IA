"""
Módulo para processamento e validação de entidades antes de enviar para o frontend.
Responsável por garantir que apenas entidades com dados reais sejam enviadas.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

logger = logging.getLogger(__name__)

def is_entity_valid(entity: Dict) -> bool:
    """
    Verifica se uma entidade possui dados válidos e não-nulos
    que justifiquem enviá-la para o frontend.
    Critérios: aceitar entidades com pelo menos UMA métrica essencial real em qualquer período,
    ou entidades marcadas explicitamente como dados de teste.
    """
    # Aceitamos imediatamente entidades de teste
    if entity and isinstance(entity, dict) and (entity.get('testing', False) or entity.get('tipo_coleta') == 'dados_teste_desenvolvimento'):
        logger.info(f"Entidade de teste aceita: {entity.get('name', 'sem-nome')}")
        return True
    
    # Verifica se a entidade existe
    if entity is None or not isinstance(entity, dict):
        logger.debug("Entidade rejeitada: vazia ou não é dicionário")
        return False
    
    # Verifica campos básicos obrigatórios
    if not entity.get('name') or not entity.get('guid') or not entity.get('domain'):
        logger.debug(f"Entidade rejeitada: sem dados básicos obrigatórios - {entity.get('guid', 'sem-guid')}")
        return False
    
    # Rejeita entidades com problemas explícitos de coleta
    if entity.get('problema') in ['INVALID_QUERY', 'NO_DATA', 'NO_VALID_METRICS', 'INVALID_JSON_DETAIL', 'PROCESSING_ERROR', 'NOT_FOUND']:
        logger.debug(f"Entidade rejeitada: problema conhecido - {entity.get('name')} - {entity.get('problema')}")
        return False
        
    # Rejeita entidades sem métricas
    if not entity.get('metricas') or not isinstance(entity.get('metricas'), dict):
        logger.debug(f"Entidade rejeitada: sem métricas ou formato inválido: {entity.get('name')} - domínio: {entity.get('domain')}")
        return False
    
    # Verifica se há pelo menos um período com dados reais
    essential_metrics = ['apdex', 'response_time', 'response_time_max', 'error_rate', 'throughput']
    for periodo_key, periodo_data in entity.get('metricas', {}).items():
        if isinstance(periodo_data, dict) and periodo_data:
            for essential_metric in essential_metrics:
                # Para compatibilidade com dados do create_test_cache.py e data real
                if essential_metric in periodo_data and periodo_data[essential_metric] is not None and periodo_data[essential_metric] != "" and periodo_data[essential_metric] != []:
                    logger.info(f"Entidade aceita: {entity.get('name')} - {essential_metric}={periodo_data[essential_metric]}")
                    return True  # Aceita se encontrar pelo menos uma métrica essencial real
    
    logger.debug(f"Entidade rejeitada: sem nenhuma métrica essencial real: {entity.get('name')}")
    return False

def process_entity_details(entity: Dict) -> Dict:
    """
    Processa os detalhes de uma entidade, garantindo que o formato
    seja consistente e utilizável pelo frontend.
    
    - Converte 'detalhe' de string JSON para objeto estruturado em 'metricas'
    - Remove métricas nulas (None)
    - Valida que a entidade tem pelo menos algum dado útil
    - Garante que métricas essenciais estejam como valores simples
    """
    try:
        # Certifica que temos um dicionário para trabalhar
        if not isinstance(entity, dict):
            logger.warning(f"Entidade deve ser um dicionário, recebido: {type(entity)}")
            return None
        
        # Clone da entidade para não modificar o original
        processed = entity.copy()
        
        # Processa o campo detalhe (string JSON) para metricas (estruturado)
        if 'detalhe' in processed and isinstance(processed['detalhe'], str) and not processed.get('metricas'):
            try:
                # Substitui aspas simples por aspas duplas para garantir JSON válido
                detail_str = processed['detalhe'].replace("'", "\"")
                metrics_data = json.loads(detail_str)
                
                # Adiciona os detalhes processados como métricas estruturadas
                if not processed.get('metricas'):
                    processed['metricas'] = {}
                
                # Para cada período temporal, filtrar campos nulos e vazios
                for period, period_data in metrics_data.items():
                    if not period_data:
                        continue
                    
                    # Inicializa o período se não existe
                    if period not in processed['metricas']:
                        processed['metricas'][period] = {}
                    
                    # Garantir que period_data seja um dicionário se for string JSON
                    if isinstance(period_data, str):
                        try:
                            # Tenta converter string para dicionário se for JSON
                            period_data_str = period_data.replace("'", "\"")
                            period_data = json.loads(period_data_str)
                        except json.JSONDecodeError:
                            # Se não for JSON válido, mantém como string
                            processed['metricas'][period] = period_data
                            continue
                    
                    # Processa cada métrica do período, garantindo que period_data seja um dicionário
                    if isinstance(period_data, dict):
                        # Cria um novo dicionário apenas com métricas válidas
                        valid_metrics = {}
                        for metric_name, metric_data in period_data.items():
                            # Pula métricas vazias, nulas ou em branco
                            if metric_data is None or metric_data == "" or metric_data == []:
                                continue
                            
                            # Se a métrica for uma lista de resultados, extrai o valor principal se possível
                            if isinstance(metric_data, list) and metric_data and isinstance(metric_data[0], dict):
                                # Se for métrica essencial, extrai o valor do primeiro item
                                if metric_name in ['apdex', 'response_time', 'response_time_max', 'error_rate', 'throughput']:
                                    v = metric_data[0]
                                    if isinstance(v, dict) and 'value' in v:
                                        valid_metrics[metric_name] = v['value']
                                    else:
                                        valid_metrics[metric_name] = v
                                else:
                                    # Para outras métricas, mantém a lista filtrada
                                    valid_items = [item for item in metric_data if item and isinstance(item, dict)]
                                    if valid_items:
                                        valid_metrics[metric_name] = valid_items
                            else:
                                # Para métricas simples, adiciona diretamente se não for nula
                                valid_metrics[metric_name] = metric_data
                        
                        # Só adiciona o período se tiver métricas válidas
                        if valid_metrics:
                            # Achata as métricas para facilitar o filtro e o frontend
                            flattened = flatten_metrics(valid_metrics)
                            # Garante que métricas essenciais estejam como valores simples (float/int)
                            for metric_name in ['apdex', 'response_time', 'response_time_max', 'error_rate', 'throughput']:
                                if metric_name in flattened:
                                    val = flattened[metric_name]
                                    # Se ainda for dict ou lista, tenta extrair o valor
                                    if isinstance(val, dict) and 'results' in val and val['results']:
                                        v = val['results'][0]
                                        if isinstance(v, dict) and 'value' in v:
                                            flattened[metric_name] = v['value']
                                        else:
                                            flattened[metric_name] = v
                                    elif isinstance(val, list) and val and isinstance(val[0], dict) and 'value' in val[0]:
                                        flattened[metric_name] = val[0]['value']
                            processed['metricas'][period] = flattened
                        else:
                            # Remove o período se não tem métricas válidas
                            if period in processed['metricas']:
                                del processed['metricas'][period]
                    elif isinstance(period_data, str):
                        # Tenta processar strings como JSON
                        try:
                            json_data = json.loads(period_data.replace("'", "\""))
                            if json_data and isinstance(json_data, dict):
                                # Substitui a string por um dicionário processado
                                processed['metricas'][period] = {}
                                for metric_name, metric_data in json_data.items():
                                    if metric_data:  # Pula dados vazios
                                        processed['metricas'][period][metric_name] = metric_data
                        except:
                            # Não é JSON válido, mantém como está
                            processed['metricas'][period] = period_data
                    else:
                        # Para outros tipos, mantém como está
                        processed['metricas'][period] = period_data
                
                # Se não tem métricas válidas após processamento, marca como problemática
                if not any(period_data for period_data in processed.get('metricas', {}).values()):
                    processed['problema'] = 'NO_VALID_METRICS'
                    
            except json.JSONDecodeError:
                logger.warning(f"JSON inválido em detalhe: {processed['detalhe'][:100]}...")
                processed['problema'] = 'INVALID_JSON_DETAIL'
            except Exception as e:
                logger.warning(f"Erro ao processar detalhe: {str(e)}")
                processed['problema'] = 'PROCESSING_ERROR'
        # Garante que métricas essenciais estejam achatadas mesmo se já vierem em metricas
        if 'metricas' in processed and isinstance(processed['metricas'], dict):
            for period, period_data in processed['metricas'].items():
                if isinstance(period_data, dict):
                    for metric_name in ['apdex', 'response_time', 'response_time_max', 'error_rate', 'throughput']:
                        if metric_name in period_data and isinstance(period_data[metric_name], list) and period_data[metric_name] and isinstance(period_data[metric_name][0], dict):
                            v = period_data[metric_name][0]
                            if isinstance(v, dict) and 'value' in v:
                                processed['metricas'][period][metric_name] = v['value']
                            else:
                                processed['metricas'][period][metric_name] = v
        return processed
    except Exception as e:
        logger.error(f"Erro geral no processamento da entidade: {str(e)}")
        return None

def flatten_metrics(period_data):
    flat = {}
    for metric, value in period_data.items():
        if isinstance(value, dict) and "results" in value and value["results"]:
            v = value["results"][0]
            if isinstance(v, dict) and "value" in v:
                flat[metric] = v["value"]
            else:
                flat[metric] = v
        else:
            flat[metric] = value
    return flat

def filter_entities_with_data(entities: List[Dict]) -> List[Dict]:
    """
    Filtra uma lista de entidades para retornar apenas aquelas 
    com dados válidos e reais para o frontend.
    Também processa cada entidade para garantir formato consistente.
    Aplica critérios RIGOROSOS para economizar tokens.
    Nunca retorna None, sempre retorna lista (pode ser vazia).
    """
    if not entities:
        logger.warning("Nenhuma entidade para filtrar")
        return []
    
    valid_entities = []
    processed_count = 0
    rejected_count = 0
    processed_domains = {}
    metrics_stats = {
        'has_apdex': 0,
        'has_response_time': 0,
        'has_error_rate': 0,
        'has_throughput': 0
    }
    
    logger.info(f"Iniciando filtragem rigorosa de {len(entities)} entidades")
    
    # Primeira passagem: processar todas as entidades e coletar estatísticas
    for entity in entities:
        try:
            # Processa a entidade
            processed = process_entity_details(entity)
            processed_count += 1
            
            # Pula entidades que não puderam ser processadas
            if not processed:
                rejected_count += 1
                logger.debug(f"Entidade rejeitada: erro no processamento: {entity}")
                continue
                
            # Contagem por domínio
            domain = entity.get('domain', 'UNKNOWN')
            processed_domains[domain] = processed_domains.get(domain, 0) + 1
            
            # Verificação pré-validação (estatísticas)
            has_metrics = False
            if processed and processed.get('metricas'):
                for period, period_data in processed['metricas'].items():
                    if isinstance(period_data, dict):
                        # Corrigido: checar 'response_time' além de 'response_time_max'
                        if 'apdex' in period_data and period_data['apdex'] is not None:
                            metrics_stats['has_apdex'] += 1
                            has_metrics = True
                        if (('response_time' in period_data and period_data['response_time'] is not None) or
                            ('response_time_max' in period_data and period_data['response_time_max'] is not None)):
                            metrics_stats['has_response_time'] += 1
                            has_metrics = True
                        if ('error_rate' in period_data and period_data['error_rate'] is not None) or \
                           ('recent_error' in period_data and period_data['recent_error'] is not None):
                            metrics_stats['has_error_rate'] += 1
                            has_metrics = True
                        if 'throughput' in period_data and period_data['throughput'] is not None:
                            metrics_stats['has_throughput'] += 1
                            has_metrics = True
            
            # Rejeita entidades sem métricas válidas
            if not has_metrics:
                rejected_count += 1
                logger.debug(f"Entidade rejeitada: sem métricas válidas - {processed.get('name')}")
                continue
            
            # Verifica se a entidade é válida usando critérios rigorosos
            if is_entity_valid(processed):
                valid_entities.append(processed)
            else:
                rejected_count += 1
                logger.debug(f"Entidade rejeitada por is_entity_valid: {processed}")
        except Exception as e:
            logger.error(f"Erro ao processar entidade: {str(e)}")
            rejected_count += 1
    
    # Log do resultado do processamento com mais detalhes
    logger.info(f"Entidades processadas: {processed_count}, Válidas: {len(valid_entities)}, Rejeitadas: {rejected_count}")
    logger.info(f"Distribuição por domínio: {processed_domains}")
    logger.info(f"Estatísticas de métricas: Apdex: {metrics_stats['has_apdex']}, " +
               f"Response Time: {metrics_stats['has_response_time']}, " +
               f"Error Rate: {metrics_stats['has_error_rate']}, " +
               f"Throughput: {metrics_stats['has_throughput']}")
    
    return valid_entities