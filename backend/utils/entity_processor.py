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
    
    Critérios relaxados para garantir mais dados disponíveis para análise,
    mesmo que eles não sejam completamente ideais.
    """
    if not entity:
        logger.debug("Entidade rejeitada: vazia")
        return False
    
    # Verifica campos básicos obrigatórios
    if not entity.get('name') or not entity.get('domain'):
        logger.debug(f"Entidade rejeitada: sem nome ou domínio - {entity.get('guid', 'sem-guid')}")
        return False
    
    # Rejeita entidades com problemas explícitos de coleta
    if entity.get('problema') in ['INVALID_QUERY', 'NO_DATA', 'RATE_LIMITED']:
        logger.info(f"Entidade rejeitada: problema conhecido - {entity.get('name')} - {entity.get('problema')}")
        return False
        
    # Requer métricas para análise de qualidade
    if not entity.get('metricas'):
        logger.debug(f"Entidade rejeitada: sem métricas - {entity.get('name')}")
        return False
    
    # Verificação de métricas úteis, com critérios mais relaxados
    has_real_data = False
    metrics_quality_score = 0
    
    # Métricas essenciais para análise de APIs (especialmente lentas)
    required_metrics = ['apdex', 'response_time', 'throughput', 'error_rate', 'recent_error']
    
    # Métricas adicionais relevantes para análise de SQL e causa raiz
    advanced_metrics = ['database', 'sql', 'query', 'transaction', 'db_call', 'stacktrace', 'error_detail', 'trace']
    
    # Verifica se há pelo menos alguma métrica real útil
    for period, metrics in entity.get('metricas', {}).items():
        if not metrics:
            continue
            
        # Verifica todas as métricas do período
        for metric_name, metric_data in metrics.items():
            # Ignora métricas vazias
            if not metric_data:
                continue
                
            # Se for uma lista com dados reais 
            if isinstance(metric_data, list) and len(metric_data) > 0:
                has_real_data = True
                
                # Calcula um score de qualidade pelas métricas importantes
                if any(required in metric_name.lower() for required in required_metrics):
                    metrics_quality_score += 1
                    
                # Métricas avançadas recebem score extra (2 pontos) pois são mais valiosas para análise de causa raiz
                if any(advanced in metric_name.lower() for advanced in advanced_metrics):
                    metrics_quality_score += 2
                    
                # Métricas específicas para a pergunta sobre APIs lentas (pontuação extra)
                if 'api' in metric_name.lower() or 'latency' in metric_name.lower() or 'slow' in metric_name.lower():
                    metrics_quality_score += 2
            
            # Se não for lista, mas for um valor escalar não nulo
            elif metric_data is not None and metric_data != "":
                has_real_data = True
                
                # Calcula um score de qualidade pelas métricas importantes
                if any(required in metric_name.lower() for required in required_metrics):
                    metrics_quality_score += 1
                
                # Métricas avançadas recebem score extra
                if any(advanced in metric_name.lower() for advanced in advanced_metrics):
                    metrics_quality_score += 2
                    
                # Métricas específicas para APIs lentas
                if 'api' in metric_name.lower() or 'latency' in metric_name.lower() or 'slow' in metric_name.lower():
                    metrics_quality_score += 2
    
    # Menos rigoroso: Se tiver dados reais, aceita mesmo com score baixo
    if not has_real_data:
        logger.debug(f"Entidade rejeitada: sem dados reais nas métricas - {entity.get('name')}")
        return False
    
    # MODIFICAÇÃO: Aceita mesmo entidades com score 0 (se tiver algum dado real)
    if metrics_quality_score <= 0 and has_real_data:
        logger.info(f"Entidade aceita com score zero porque tem dados reais: {entity.get('name')} - Score: {metrics_quality_score}")
        entity['dados_parciais'] = True
        return True
    
    # MODIFICAÇÃO: Não rejeita mais entidades com score 0 como critério pois isso pode estar filtrando demais
    # if metrics_quality_score == 0:
    #    logger.info(f"Entidade rejeitada - dados insuficientes: {entity.get('name')} - Score: {metrics_quality_score}")
    #    return False
        
    # Se o score for baixo (apenas 1 métrica), marca como dados parciais mas ainda aceita
    if metrics_quality_score <= 1:
        logger.info(f"Entidade com poucos dados aceitáveis: {entity.get('name')} - Score: {metrics_quality_score}")
        entity['dados_parciais'] = True
    
    return True

def process_entity_details(entity: Dict) -> Dict:
    """
    Processa os detalhes de uma entidade, garantindo que o formato
    seja consistente e utilizável pelo frontend.
    
    - Converte 'detalhe' de string JSON para objeto estruturado em 'metricas'
    - Remove métricas nulas (None)
    - Valida que a entidade tem pelo menos algum dado útil
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
                    
                    # Processa cada métrica do período
                    for metric_name, metric_data in period_data.items():
                        # Pula métricas vazias ou nulas
                        if not metric_data:
                            continue
                            
                        # Se a métrica for uma lista de resultados, filtra resultados nulos
                        if isinstance(metric_data, list):
                            # Filtra itens nulos da lista
                            valid_items = []
                            for item in metric_data:
                                if item and isinstance(item, dict):
                                    # Remove chaves com valores nulos do dicionário
                                    item = {k: v for k, v in item.items() if v is not None}
                                    if item:  # Se ainda tem dados após filtrar
                                        valid_items.append(item)
                            
                            if valid_items:  # Só adiciona se tiver itens válidos
                                processed['metricas'][period][metric_name] = valid_items
                        else:
                            # Para métricas simples, adiciona diretamente se não for nula
                            processed['metricas'][period][metric_name] = metric_data
                
                # Se não tem métricas válidas após processamento, marca como problemática
                if not any(period_data for period_data in processed.get('metricas', {}).values()):
                    processed['problema'] = 'NO_VALID_METRICS'
                    
            except json.JSONDecodeError:
                logger.warning(f"JSON inválido em detalhe: {processed['detalhe'][:100]}...")
                processed['problema'] = 'INVALID_JSON_DETAIL'
            except Exception as e:
                logger.warning(f"Erro ao processar detalhe: {str(e)}")
                processed['problema'] = 'PROCESSING_ERROR'
        
        return processed
    except Exception as e:
        logger.error(f"Erro geral no processamento da entidade: {str(e)}")
        return None

def filter_entities_with_data(entities: List[Dict]) -> List[Dict]:
    """
    Filtra uma lista de entidades para retornar apenas aquelas 
    com dados válidos para o frontend.
    
    Também processa cada entidade para garantir formato consistente.
    Aplica critérios rigorosos para garantir qualidade dos dados.
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
    
    logger.info(f"Iniciando filtragem de {len(entities)} entidades")
    
    for entity in entities:
        try:
            # Processa a entidade
            processed = process_entity_details(entity)
            processed_count += 1
            
            # Contagem por domínio
            domain = entity.get('domain', 'UNKNOWN')
            processed_domains[domain] = processed_domains.get(domain, 0) + 1
            
            # Verificação pré-validação (estatísticas)
            if processed and processed.get('metricas'):
                for period in processed['metricas'].values():
                    if 'apdex' in period:
                        metrics_stats['has_apdex'] += 1
                    if 'response_time_max' in period:
                        metrics_stats['has_response_time'] += 1
                    if 'error_rate' in period or 'recent_error' in period:
                        metrics_stats['has_error_rate'] += 1
                    if 'throughput' in period:
                        metrics_stats['has_throughput'] += 1
            
            # Verifica se a entidade processada é válida
            if processed and is_entity_valid(processed):
                valid_entities.append(processed)
            else:
                rejected_count += 1
                
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
    
    # Taxa de rejeição para alerta
    rejection_rate = rejected_count / processed_count if processed_count > 0 else 0
    if rejection_rate > 0.5:  # Se mais de 50% das entidades foram rejeitadas
        logger.warning(f"ALERTA: Taxa de rejeição muito alta ({rejection_rate:.1%})! " +
                      "Verifique a instrumentação do New Relic ou as queries.")
    
    # Verificação final de qualidade
    if not valid_entities:
        logger.critical("CRÍTICO: Nenhuma entidade válida após filtragem!")
        # Mesmo sem entidades válidas, retorna uma lista vazia para evitar None
    elif len(valid_entities) < 5 and processed_count > 10:
        logger.warning(f"ALERTA: Apenas {len(valid_entities)} entidades válidas de {processed_count}!")
    
    return valid_entities

if __name__ == "__main__":
    """
    Módulo para teste independente do processador de entidades.
    """
    # Configuração de logging para testes
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # Tenta carregar o cache do disco
        print("🔍 Testando processador de entidades...")
        cache_file = Path("historico/cache_completo.json")
        
        if not cache_file.exists():
            print(f"❌ Arquivo de cache não encontrado: {cache_file}")
            sys.exit(1)
            
        with open(cache_file, "r", encoding="utf-8") as f:
            cache = json.load(f)
            
        entidades = cache.get("entidades", [])
        print(f"📊 Total de entidades no cache: {len(entidades)}")
        
        if not entidades:
            print("❌ Nenhuma entidade encontrada no cache!")
            sys.exit(1)
            
        # Processar as entidades
        entidades_processadas = []
        entidades_validas = []
        metricas_nulas = 0
        metricas_totais = 0
        
        for i, entity in enumerate(entidades):
            if i < 3:
                print(f"\n🔍 Analisando entidade: {entity.get('name', 'Unknown')}")
                print(f"   Domain: {entity.get('domain', 'Unknown')}")
                print(f"   Tem detalhe: {'✅' if entity.get('detalhe') else '❌'}")
                print(f"   Tem métricas: {'✅' if entity.get('metricas') else '❌'}")
                
            processed = process_entity_details(entity)
            if processed:
                entidades_processadas.append(processed)
                
                # Contar métricas nulas
                detalhe = processed.get('detalhe', '{}')
                if isinstance(detalhe, str):
                    try:
                        detalhe_dict = json.loads(detalhe.replace("'", "\""))
                        for period, metrics in detalhe_dict.items():
                            if isinstance(metrics, dict):
                                for metric_name, metric_value in metrics.items():
                                    metricas_totais += 1
                                    if metric_value is None:
                                        metricas_nulas += 1
                    except:
                        pass
                
                # Verificar se é válida
                if is_entity_valid(processed):
                    entidades_validas.append(processed)
        
        print(f"\n✅ Processamento concluído:")
        print(f"   - Entidades processadas: {len(entidades_processadas)}")
        print(f"   - Entidades válidas: {len(entidades_validas)}")
        print(f"   - Métricas nulas: {metricas_nulas}/{metricas_totais} ({round(metricas_nulas/max(1,metricas_totais)*100, 2)}%)")
        
        # Verificar o resultado para uma entidade exemplo
        if entidades_validas:
            exemplo = entidades_validas[0]
            print("\n🔍 Exemplo de entidade processada:")
            print(f"   Nome: {exemplo.get('name', 'N/A')}")
            print(f"   Domínio: {exemplo.get('domain', 'N/A')}")
            print(f"   GUID: {exemplo.get('guid', 'N/A')}")
            print(f"   Problema: {exemplo.get('problema', 'Nenhum')}")
            
            # Mostrar estrutura de métricas
            metricas = exemplo.get('metricas', {})
            if metricas:
                print(f"   Períodos disponíveis: {', '.join(metricas.keys())}")
                if '30min' in metricas:
                    print(f"   Métricas em 30min: {', '.join(metricas['30min'].keys())}")
            else:
                print("   Sem métricas processadas")
                
        print("\n✅ Teste concluído!")
        
    except Exception as e:
        print(f"❌ Erro ao testar processador de entidades: {e}")
        import traceback
        traceback.print_exc()