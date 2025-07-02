"""
Script de diagnóstico para verificar a conectividade e dados do módulo de infraestrutura avançada
"""

import os
import sys
import json
import requests
import logging
from pathlib import Path
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("diagnostico_infra_avancada")

def check_cache_files():
    """Verifica a existência e conteúdo dos arquivos de cache para infraestrutura avançada"""
    logger.info("Verificando arquivos de cache para infraestrutura avançada...")
    
    cache_files = [
        "kubernetes_metrics.json",
        "infrastructure_detailed.json",
        "service_topology.json"
    ]
    
    cache_paths = [
        "backend/cache",
        "cache"
    ]
    
    results = []
    
    for path in cache_paths:
        for file in cache_files:
            file_path = os.path.join(path, file)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        size = os.path.getsize(file_path)
                        results.append({
                            "file": file_path,
                            "status": "OK",
                            "size": f"{size / 1024:.1f} KB",
                            "timestamp": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                            "content_valid": True
                        })
                except Exception as e:
                    results.append({
                        "file": file_path,
                        "status": "ERRO",
                        "error": str(e),
                        "content_valid": False
                    })
            else:
                results.append({
                    "file": file_path,
                    "status": "NÃO ENCONTRADO",
                    "content_valid": False
                })
    
    return results

def check_backend_endpoints():
    """Verifica se os endpoints de infraestrutura avançada do backend estão respondendo"""
    logger.info("Verificando endpoints do backend...")
    
    endpoints = [
        "http://localhost:8000/api/health",
        "http://localhost:8000/api/avancado/kubernetes",
        "http://localhost:8000/api/avancado/infraestrutura",
        "http://localhost:8000/api/avancado/topologia"
    ]
    
    results = []
    
    for endpoint in endpoints:
        try:
            logger.info(f"Tentando acessar {endpoint}...")
            response = requests.get(endpoint, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                results.append({
                    "endpoint": endpoint,
                    "status": "OK",
                    "status_code": response.status_code,
                    "response_time": f"{response.elapsed.total_seconds():.2f}s",
                    "data_valid": True,
                    "data_size": f"{len(response.text) / 1024:.1f} KB"
                })
            else:
                results.append({
                    "endpoint": endpoint,
                    "status": "ERRO",
                    "status_code": response.status_code,
                    "response_time": f"{response.elapsed.total_seconds():.2f}s",
                    "data_valid": False,
                    "error": response.text
                })
        except Exception as e:
            results.append({
                "endpoint": endpoint,
                "status": "FALHA",
                "error": str(e),
                "data_valid": False
            })
    
    return results

def run_diagnostics():
    """Executa o diagnóstico completo"""
    logger.info("=== DIAGNÓSTICO DE INFRAESTRUTURA AVANÇADA ===")
    
    # Verificar arquivos de cache
    cache_results = check_cache_files()
    
    logger.info("\nResultados da verificação de cache:")
    for result in cache_results:
        status_icon = "✅" if result.get("content_valid") else "❌"
        logger.info(f"{status_icon} {result['file']}: {result['status']}")
        if result.get("size"):
            logger.info(f"   Tamanho: {result['size']}")
        if result.get("timestamp"):
            logger.info(f"   Última modificação: {result['timestamp']}")
        if result.get("error"):
            logger.info(f"   Erro: {result['error']}")
    
    # Verificar endpoints
    endpoint_results = check_backend_endpoints()
    
    logger.info("\nResultados da verificação de endpoints:")
    for result in endpoint_results:
        status_icon = "✅" if result.get("data_valid") else "❌"
        logger.info(f"{status_icon} {result['endpoint']}: {result['status']}")
        logger.info(f"   Código de status: {result.get('status_code', 'N/A')}")
        if result.get("response_time"):
            logger.info(f"   Tempo de resposta: {result['response_time']}")
        if result.get("data_size"):
            logger.info(f"   Tamanho dos dados: {result['data_size']}")
        if result.get("error"):
            logger.info(f"   Erro: {result['error']}")
    
    # Verificação geral
    cache_valid = any(r.get("content_valid", False) for r in cache_results)
    endpoints_valid = any(r.get("data_valid", False) for r in endpoint_results)
    
    logger.info("\n=== RESUMO DO DIAGNÓSTICO ===")
    logger.info(f"Cache disponível: {'Sim' if cache_valid else 'Não'}")
    logger.info(f"Endpoints respondendo: {'Sim' if endpoints_valid else 'Não'}")
    
    if not cache_valid and not endpoints_valid:
        logger.error("\n❌ PROBLEMA CRÍTICO: Sem cache e sem resposta dos endpoints!")
        logger.error("   Sugestão: Verifique se o backend está em execução e execute check_and_fix_cache.py")
    elif not cache_valid:
        logger.warning("\n⚠️ ALERTA: Cache não disponível, mas os endpoints estão respondendo.")
        logger.warning("   Sugestão: Execute check_and_fix_cache.py para gerar os arquivos de cache")
    elif not endpoints_valid:
        logger.warning("\n⚠️ ALERTA: Endpoints não estão respondendo, mas o cache está disponível.")
        logger.warning("   Sugestão: Verifique se o backend está em execução")
    else:
        logger.info("\n✅ TUDO OK: Cache e endpoints estão funcionando corretamente")
    
    return {
        "cache": cache_results,
        "endpoints": endpoint_results,
        "cache_valid": cache_valid,
        "endpoints_valid": endpoints_valid
    }

if __name__ == "__main__":
    try:
        results = run_diagnostics()
        
        # Salvar resultados em um arquivo
        output_file = "diagnostico_infra_avancada.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\nResultados salvos em {output_file}")
        
        # Retornar código de saída baseado no diagnóstico
        if not results["cache_valid"] and not results["endpoints_valid"]:
            sys.exit(2)  # Erro crítico
        elif not results["cache_valid"] or not results["endpoints_valid"]:
            sys.exit(1)  # Aviso
        else:
            sys.exit(0)  # Tudo ok
    except Exception as e:
        logger.error(f"Erro durante o diagnóstico: {e}")
        sys.exit(3)  # Erro inesperado
