"""
Analisa o método collect_entity_dependencies e verifica sua integração com outros componentes.
"""
import inspect
import logging
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("validation_results.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Adicionar diretório raiz ao PATH
sys.path.append(str(Path(__file__).parent))

def validate_implementation():
    """Valida a implementação do método collect_entity_dependencies."""
    from utils.newrelic_collector import NewRelicCollector
    
    logger.info("=" * 80)
    logger.info("VALIDANDO IMPLEMENTAÇÃO DO COLLECT_ENTITY_DEPENDENCIES")
    logger.info("=" * 80)
    
    # Verificar se o método existe
    if not hasattr(NewRelicCollector, 'collect_entity_dependencies'):
        logger.error("❌ Método collect_entity_dependencies NÃO foi encontrado na classe NewRelicCollector")
        return False
    
    # Obter o código fonte do método
    method = getattr(NewRelicCollector, 'collect_entity_dependencies')
    source_code = inspect.getsource(method)
    
    # Verificar componentes essenciais que devem estar no método
    checks = [
        ('Coleta upstream', 'upstreamRelationships' in source_code),
        ('Coleta downstream', 'downstreamRelationships' in source_code),
        ('Tratamento de exceções', 'except Exception' in source_code),
        ('Logging de erros', ('logger.error' in source_code) or ('logger.warning' in source_code)),
        ('Resposta vazia em caso de erro', 'return {' in source_code and '"metadata":' in source_code and '"error":' in source_code)
    ]
    
    all_passed = True
    for name, passed in checks:
        status = "✅ PRESENTE" if passed else "❌ AUSENTE"
        logger.info(f"{name}: {status}")
        all_passed = all_passed and passed
    
    # Verificar outros métodos que devem usar collect_entity_dependencies
    try:
        # Verificar se o método é chamado em collect_entity_metrics
        entity_metrics_source = inspect.getsource(NewRelicCollector.collect_entity_metrics)
        calls_dependencies = 'collect_entity_dependencies' in entity_metrics_source
        
        if calls_dependencies:
            logger.info("✅ O método collect_entity_metrics usa collect_entity_dependencies")
        else:
            logger.warning("⚠️ O método collect_entity_metrics não parece usar collect_entity_dependencies")
            logger.info("👉 SUGESTÃO: Integrar collect_entity_dependencies no método collect_entity_metrics para obter dados completos")
    except Exception as e:
        logger.error(f"❌ Erro ao verificar integração: {e}")
    
    # Verificar integração em collect_entity_metrics
    entity_metrics_source = inspect.getsource(NewRelicCollector.collect_entity_metrics)
    calls_dependencies_in_metrics = 'collect_entity_dependencies' in entity_metrics_source
    
    if calls_dependencies_in_metrics:
        logger.info("✅ O método collect_entity_metrics usa collect_entity_dependencies")
    else:
        logger.warning("⚠️ O método collect_entity_metrics não usa collect_entity_dependencies")
        
    # Salvar resultado em JSON para fácil consulta
    result = {
        "timestamp": datetime.now().isoformat(),
        "method_exists": hasattr(NewRelicCollector, 'collect_entity_dependencies'),
        "validation_checks": {check[0]: check[1] for check in checks},
        "integration_checks": {
            "collect_entity_metrics_integration": calls_dependencies_in_metrics
        },
        "overall_status": "PASSED" if all_passed else "FAILED"
    }
    
    with open("dependency_validation_result.json", "w") as f:
        json.dump(result, f, indent=2)
    logger.info(f"Resultados detalhados salvos em dependency_validation_result.json")
    
    # Resumo final
    logger.info("=" * 80)
    if all_passed:
        logger.info("✅ A implementação do collect_entity_dependencies parece estar completa e correta!")
    else:
        logger.warning("⚠️ A implementação do collect_entity_dependencies pode estar incompleta ou incorreta")
    logger.info("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    validate_implementation()
