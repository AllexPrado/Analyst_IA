#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para iniciar o sistema Analyst-IA de forma unificada
"""
import os
import subprocess
import time
import sys
from pathlib import Path
import logging
import platform
import requests
import json

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def is_windows():
    """Verifica se o sistema é Windows"""
    return platform.system().lower() == "windows"

def check_and_fix_cache():
    """Executa a verificação e correção do cache"""
    logger.info("Verificando e corrigindo o cache...")
    
    try:
        # Importar e executar o script de verificação de cache
        sys.path.append(str(Path(__file__).parent / "backend"))
        from check_and_fix_cache import check_and_fix_cache
        check_and_fix_cache()
        logger.info("✅ Cache verificado e corrigido com sucesso")
        return True
    except Exception as e:
        logger.error(f"❌ Erro na verificação de cache: {e}")
        return False

def test_backend_api():
    """Testa os endpoints principais da API do backend"""
    logger.info("Testando endpoints da API...")
    
    base_url = "http://localhost:8000/api"
    endpoints = [
        ("/health", "GET", None),
        ("/status", "GET", None),
        ("/kpis", "GET", None),
        ("/chat", "POST", {"pergunta": "Como está o sistema?"})
    ]
    
    results = []
    
    for path, method, data in endpoints:
        url = f"{base_url}{path}"
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:  # POST
                response = requests.post(url, json=data, timeout=10)
                
            success = response.status_code == 200
            results.append({
                "endpoint": url,
                "method": method,
                "status": response.status_code,
                "success": success,
                "response": response.json() if success else None
            })
            
            if success:
                logger.info(f"✅ Endpoint {method} {path} OK")
            else:
                logger.warning(f"⚠️ Endpoint {method} {path} falhou (status {response.status_code})")
                
        except Exception as e:
            logger.error(f"❌ Erro ao testar {method} {path}: {e}")
            results.append({
                "endpoint": url,
                "method": method,
                "error": str(e),
                "success": False
            })
    
    success_count = sum(1 for r in results if r["success"])
    logger.info(f"{success_count}/{len(endpoints)} endpoints funcionando corretamente")
    
    return results

def start_backend():
    """Inicia o servidor backend"""
    logger.info("Iniciando o servidor backend...")
    
    backend_dir = Path(__file__).parent / "backend"
    
    try:
        # Preparar comando para iniciar o servidor
        cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
        
        if is_windows():
            # No Windows, usar um novo processo CMD
            process = subprocess.Popen(
                cmd,
                cwd=str(backend_dir),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Em outros sistemas, usar um processo normal
            process = subprocess.Popen(
                cmd,
                cwd=str(backend_dir)
            )
        
        logger.info(f"✅ Servidor backend iniciado (PID: {process.pid})")
        return process
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar o backend: {e}")
        return None

def start_frontend():
    """Inicia o servidor frontend"""
    logger.info("Iniciando o servidor frontend...")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    if not frontend_dir.exists():
        logger.error(f"❌ Diretório frontend não encontrado: {frontend_dir}")
        return None
    
    try:
        # Preparar comando para iniciar o frontend
        cmd = ["npm", "run", "dev"]
        
        if is_windows():
            # No Windows, usar um novo processo CMD
            process = subprocess.Popen(
                cmd,
                cwd=str(frontend_dir),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Em outros sistemas, usar um processo normal
            process = subprocess.Popen(
                cmd,
                cwd=str(frontend_dir)
            )
        
        logger.info(f"✅ Servidor frontend iniciado (PID: {process.pid})")
        return process
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar o frontend: {e}")
        return None

def test_api_health(max_attempts=5, delay=2):
    """Testa se a API está funcionando corretamente"""
    logger.info("Verificando status da API...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://localhost:8000/api/health")
            if response.status_code == 200:
                logger.info("✅ API está respondendo corretamente")
                return True
            else:
                logger.warning(f"⚠️ API respondeu com status code {response.status_code}")
        except Exception:
            logger.warning(f"⚠️ API ainda não está disponível (tentativa {attempt+1}/{max_attempts})")
        
        # Aguardar antes da próxima tentativa
        time.sleep(delay)
    
    logger.error("❌ API não está respondendo após várias tentativas")
    return False

def main():
    """Função principal para iniciar o sistema"""
    print("=" * 80)
    print(" 🚀 INICIALIZAÇÃO DO SISTEMA ANALYST-IA")
    print("=" * 80)
    
    # Verificar e corrigir o cache
    cache_ok = check_and_fix_cache()
    if not cache_ok:
        logger.warning("⚠️ Problemas na verificação do cache, mas continuando...")
    
    # Iniciar o backend
    backend_process = start_backend()
    if not backend_process:
        logger.error("❌ Falha ao iniciar o backend. Abortando...")
        return
    
    # Verificar se a API está funcionando
    api_ok = test_api_health()
    if not api_ok:
        logger.warning("⚠️ API não está respondendo corretamente, mas continuando...")
    
    # Iniciar o frontend
    frontend_process = start_frontend()
    if not frontend_process:
        logger.error("❌ Falha ao iniciar o frontend. Abortando...")
        if backend_process:
            backend_process.terminate()
        return
    
    # Informações finais
    print("\n" + "=" * 80)
    print(" ✅ SISTEMA ANALYST-IA INICIADO COM SUCESSO")
    print("=" * 80)
    print("Backend: http://localhost:8000")
    print("API Docs: http://localhost:8000/docs")
    print("Frontend: http://localhost:5173")
    print("\nComo usar:")
    print("1. Acesse o frontend em: http://localhost:5173")
    print("2. Interaja com os painéis e o chat IA")
    print("3. Para testar a API diretamente: python backend/test_api_complete.py")
    print("\nPressione Ctrl+C para encerrar este script (os servidores continuarão rodando)")
    
    try:
        # Manter o script em execução até Ctrl+C
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nScript encerrado pelo usuário.")
        print("Os servidores backend e frontend continuam rodando.")
        print("Para encerrá-los, feche as respectivas janelas de terminal.")

if __name__ == "__main__":
    main()
