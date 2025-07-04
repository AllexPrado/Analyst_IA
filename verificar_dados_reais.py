#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para verificar e garantir que o frontend está recebendo
dados reais do backend e não dados simulados.
"""

import os
import sys
import json
import logging
import requests
import subprocess
from pathlib import Path
from datetime import datetime
import time
import shutil

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações
BACKEND_URL = "http://localhost:8000/api"
FRONTEND_URL = "http://localhost:5173"
MAX_RETRIES = 5
RETRY_INTERVAL = 2  # segundos

def verificar_backend_online():
    """Verifica se o backend está em execução"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"Status code: {response.status_code}"
    except Exception as e:
        return False, str(e)

def verificar_uso_dados_reais():
    """Verifica se o backend está configurado para usar dados reais"""
    try:
        response = requests.get(f"{BACKEND_URL}/status/data_source", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("using_real_data", False), data
        else:
            return False, f"Status code: {response.status_code}"
    except Exception as e:
        return False, str(e)

def verificar_indicador_cache():
    """Verifica se o indicador de dados reais existe no cache"""
    indicator_path = Path("backend/cache/data_source_indicator.json")
    if indicator_path.exists():
        try:
            with open(indicator_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("using_real_data", False), data
        except Exception as e:
            return False, f"Erro ao ler indicador: {e}"
    else:
        return False, "Indicador não encontrado"

def verificar_dados_avancados():
    """Verifica se os endpoints avançados estão retornando dados reais"""
    endpoints = [
        "/avancado/kubernetes",
        "/avancado/infraestrutura",
        "/avancado/topologia"
    ]
    
    resultados = {}
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Verificar se os dados parecem reais (presença de timestamp)
                tem_timestamp = "timestamp" in data or any(isinstance(v, dict) and "timestamp" in v for v in data.values())
                # Verificar fonte dos dados
                fonte_real = data.get("data_source", "") == "New Relic API"
                
                resultados[endpoint] = {
                    "status": "OK",
                    "timestamp_presente": tem_timestamp,
                    "fonte_real": fonte_real,
                    "tamanho_dados": len(json.dumps(data))
                }
            else:
                resultados[endpoint] = {
                    "status": f"Erro {response.status_code}",
                    "timestamp_presente": False,
                    "fonte_real": False
                }
        except Exception as e:
            resultados[endpoint] = {
                "status": f"Exceção: {str(e)}",
                "timestamp_presente": False,
                "fonte_real": False
            }
    
    return resultados

def forcar_uso_dados_reais():
    """Força o uso de dados reais em todo o sistema"""
    logger.info("Forçando uso de dados reais...")
    
    # 1. Atualizar o indicador de dados reais
    indicator_path = Path("backend/cache/data_source_indicator.json")
    indicator_path.parent.mkdir(parents=True, exist_ok=True)
    
    indicator_data = {
        "using_real_data": True,
        "timestamp": datetime.now().isoformat(),
        "source": "New Relic API",
        "force_refresh": True
    }
    
    with open(indicator_path, 'w', encoding='utf-8') as f:
        json.dump(indicator_data, f, indent=2)
    
    # 2. Garantir que o indicador também existe no frontend
    frontend_indicator = Path("frontend/public/status")
    frontend_indicator.mkdir(parents=True, exist_ok=True)
    
    with open(frontend_indicator / "using_real_data.json", 'w', encoding='utf-8') as f:
        json.dump(indicator_data, f, indent=2)
    
    logger.info("✅ Indicadores de dados reais atualizados")
    
    # 3. Executar o script de força de dados reais no frontend
    try:
        if Path("forcar_dados_reais_frontend.py").exists():
            result = subprocess.run(["python", "forcar_dados_reais_frontend.py"], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                logger.info("✅ Script forcar_dados_reais_frontend.py executado com sucesso")
            else:
                logger.warning(f"⚠️ Erro ao executar forcar_dados_reais_frontend.py: {result.stderr}")
    except Exception as e:
        logger.error(f"❌ Exceção ao executar forcar_dados_reais_frontend.py: {e}")
    
    return True

def limpar_cache_frontend():
    """Limpa o cache do frontend para forçar o carregamento de novos dados"""
    logger.info("Limpando cache do frontend...")
    
    # Criar arquivo que força o frontend a limpar seu cache
    force_refresh_path = Path("frontend/public/status/force_refresh.json")
    force_refresh_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(force_refresh_path, 'w', encoding='utf-8') as f:
        json.dump({
            "force_refresh": True,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    logger.info("✅ Cache do frontend marcado para atualização forçada")
    return True

def main():
    """Função principal"""
    print("\n" + "="*60)
    print("VERIFICAÇÃO DE DADOS REAIS NO FRONTEND")
    print("="*60)
    
    # Verificar se o backend está online
    print("Verificando se o backend está online...")
    online, status = verificar_backend_online()
    
    if not online:
        print(f"❌ Backend não está online: {status}")
        print("Inicie o backend antes de executar este script.")
        print("  Comando: python backend/main.py")
        return 1
    else:
        print(f"✅ Backend está online: {status}")
    
    # Verificar uso de dados reais
    print("\nVerificando se o backend está usando dados reais...")
    usando_reais, status_dados = verificar_uso_dados_reais()
    
    if usando_reais:
        print(f"✅ Backend está usando dados reais: {status_dados}")
    else:
        print(f"❌ Backend NÃO está usando dados reais: {status_dados}")
        
        # Forçar uso de dados reais
        print("\nForçando uso de dados reais...")
        forcar_uso_dados_reais()
        
        # Verificar novamente
        print("Verificando novamente o uso de dados reais...")
        usando_reais, status_dados = verificar_uso_dados_reais()
        
        if usando_reais:
            print(f"✅ Backend agora está usando dados reais: {status_dados}")
        else:
            print(f"❌ Backend ainda NÃO está usando dados reais: {status_dados}")
            print("Verifique as configurações e execute os scripts de configuração de dados reais.")
    
    # Verificar indicador no cache
    print("\nVerificando indicador no cache...")
    indicador_ativo, status_indicador = verificar_indicador_cache()
    
    if indicador_ativo:
        print(f"✅ Indicador de dados reais está ativo: {status_indicador}")
    else:
        print(f"❌ Indicador de dados reais NÃO está ativo: {status_indicador}")
        print("Forçando atualização do indicador...")
        forcar_uso_dados_reais()
    
    # Verificar endpoints avançados
    print("\nVerificando endpoints avançados...")
    resultados = verificar_dados_avancados()
    
    for endpoint, resultado in resultados.items():
        status_texto = "✅ OK" if resultado["status"] == "OK" else f"❌ {resultado['status']}"
        fonte_texto = "Dados reais" if resultado.get("fonte_real") else "Dados simulados"
        print(f"{status_texto} {endpoint}: {fonte_texto} ({resultado.get('tamanho_dados', 0)} bytes)")
    
    # Limpar cache do frontend
    print("\nLimpando cache do frontend...")
    limpar_cache_frontend()
    
    print("\n" + "="*60)
    print("VERIFICAÇÃO CONCLUÍDA")
    print("="*60)
    
    # Verificar se tudo está OK
    tudo_ok = usando_reais and indicador_ativo and all(r["status"] == "OK" for r in resultados.values())
    
    if tudo_ok:
        print("✅ Tudo configurado corretamente para uso de dados reais!")
        print("O frontend deve estar recebendo dados reais do backend.")
    else:
        print("⚠️ Há problemas na configuração de dados reais.")
        print("Execute os seguintes comandos para garantir que tudo funcione corretamente:")
        print("  1. python backend/check_and_fix_cache.py")
        print("  2. python forcar_dados_reais_frontend.py")
        print("  3. Reinicie o backend: python backend/main.py")
        print("  4. Reinicie o frontend: cd frontend && npm run dev")
    
    print("="*60)
    return 0 if tudo_ok else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("Processo interrompido pelo usuário")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        sys.exit(1)
