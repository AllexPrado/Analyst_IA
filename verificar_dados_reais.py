#!/usr/bin/env python3
"""
Script para verificar se o backend está servindo dados reais
e se o frontend consegue acessá-los.
"""

import requests
import json
import sys
from pathlib import Path

def check_backend_endpoints():
    """Verifica se os endpoints do backend estão funcionando"""
    base_url = "http://localhost:8000"
    endpoints = ["/status", "/kpis", "/insights", "/cobertura", "/chat"]
    
    print("🔍 Verificando endpoints do backend...")
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint}: OK")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint}: Backend não está rodando")
        except Exception as e:
            print(f"❌ {endpoint}: {str(e)}")

def check_frontend_access():
    """Verifica se o frontend está acessível"""
    try:
        response = requests.get("http://localhost:5173", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend: Acessível")
        else:
            print(f"❌ Frontend: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Frontend: Não está rodando")
    except Exception as e:
        print(f"❌ Frontend: {str(e)}")

def check_data_files():
    """Verifica se os arquivos de dados existem"""
    print("\n📁 Verificando arquivos de dados...")
    
    data_paths = [
        "backend/dados/kpis.json",
        "backend/dados/insights.json",
        "backend/dados/cobertura.json",
        "historico/cache_completo.json"
    ]
    
    for path in data_paths:
        if Path(path).exists():
            print(f"✅ {path}: Existe")
        else:
            print(f"❌ {path}: Não encontrado")

if __name__ == "__main__":
    print("🚀 VERIFICAÇÃO DE DADOS REAIS - ANALYST IA\n")
    
    check_backend_endpoints()
    print()
    check_frontend_access()
    check_data_files()
    
    print("\n💡 Se houver erros:")
    print("1. Execute: iniciar_backend_frontend.bat")
    print("2. Aguarde alguns segundos para os serviços subirem")
    print("3. Execute este script novamente")
