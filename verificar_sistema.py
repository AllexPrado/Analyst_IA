#!/usr/bin/env python3
"""
Script para verificar rapidamente o estado do sistema Analyst_IA.
Realiza testes de conectividade, cache, dados e endpoints.
"""

import os
import sys
import json
import asyncio
import aiohttp
import time
from pathlib import Path
from datetime import datetime

# Diretórios importantes
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"

# Endpoints para testar
ENDPOINTS = [
    {"url": "http://localhost:5000/api/status", "name": "Backend Status"},
    {"url": "http://localhost:5000/api/status/data_source", "name": "Data Source"},
    {"url": "http://localhost:5000/api/entidades", "name": "Entidades"},
    {"url": "http://localhost:5000/api/kpis", "name": "KPIs"},
    {"url": "http://localhost:3000", "name": "Frontend", "method": "GET"}
]

def verificar_env():
    """Verifica se o arquivo .env está configurado corretamente"""
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        print("⚠️ Arquivo .env não encontrado!")
        return False
    
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            conteudo = f.read()
        
        # Verificar configuração para dados reais
        if "USE_SIMULATED_DATA=true" in conteudo.lower():
            print("⚠️ .env está configurado para usar dados simulados!")
            return False
        
        if "USE_SIMULATED_DATA=false" in conteudo.lower():
            print("✅ .env está configurado para usar dados reais")
            return True
            
        print("⚠️ Configuração de USE_SIMULATED_DATA não encontrada em .env")
        return False
    except Exception as e:
        print(f"❌ Erro ao verificar arquivo .env: {e}")
        return False

def verificar_cache():
    """Verifica o estado do cache"""
    cache_path = BACKEND_DIR / "historico" / "cache_completo.json"
    if not cache_path.exists():
        print("❌ Cache não encontrado!")
        return False
    
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            cache = json.load(f)
        
        entidades = cache.get("entidades", [])
        print(f"📊 Entidades no cache: {len(entidades)}")
        
        # Verificar por domínio
        dominios = {}
        for entidade in entidades:
            dominio = entidade.get("domain", "unknown").upper()
            if dominio not in dominios:
                dominios[dominio] = 0
            dominios[dominio] += 1
        
        for dominio, count in dominios.items():
            print(f"  • {dominio}: {count}")
        
        # Verificar metadata
        metadata = cache.get("metadata", {})
        timestamp = metadata.get("timestamp", "desconhecido")
        print(f"📅 Data de atualização: {timestamp}")
        
        # Verificar se há entidades suficientes
        if len(entidades) < 10:
            print("⚠️ Poucas entidades no cache. Sistema pode estar usando dados simulados!")
            return False
        
        print("✅ Cache parece estar em bom estado")
        return True
    except Exception as e:
        print(f"❌ Erro ao verificar cache: {e}")
        return False

async def verificar_endpoints():
    """Verifica se os endpoints do sistema estão respondendo"""
    print("\n🔄 Verificando endpoints do sistema...")
    
    async with aiohttp.ClientSession() as session:
        resultados = []
        
        for endpoint in ENDPOINTS:
            url = endpoint["url"]
            name = endpoint["name"]
            method = endpoint.get("method", "POST")
            
            try:
                start_time = time.time()
                
                if method == "GET":
                    async with session.get(url, timeout=5) as response:
                        elapsed = time.time() - start_time
                        status = response.status
                        
                        if status == 200:
                            print(f"✅ {name} ({url}): OK ({elapsed:.2f}s)")
                            resultados.append(True)
                        else:
                            print(f"❌ {name} ({url}): ERRO {status} ({elapsed:.2f}s)")
                            resultados.append(False)
                else:
                    async with session.post(url, json={}, timeout=5) as response:
                        elapsed = time.time() - start_time
                        status = response.status
                        
                        if status == 200:
                            print(f"✅ {name} ({url}): OK ({elapsed:.2f}s)")
                            resultados.append(True)
                        else:
                            print(f"❌ {name} ({url}): ERRO {status} ({elapsed:.2f}s)")
                            resultados.append(False)
            except Exception as e:
                print(f"❌ {name} ({url}): ERRO {e.__class__.__name__}")
                resultados.append(False)
        
        return all(resultados)

async def verificar_chat():
    """Verifica se o Chat IA está usando dados reais"""
    print("\n🤖 Verificando Chat IA...")
    
    try:
        chat_endpoints_path = BACKEND_DIR / "endpoints" / "chat_endpoints.py"
        if not chat_endpoints_path.exists():
            print("❌ Arquivo chat_endpoints.py não encontrado!")
            return False
        
        with open(chat_endpoints_path, "r", encoding="utf-8") as f:
            conteudo = f.read()
        
        if "KNOWLEDGE_BASE = {" in conteudo and "'''" not in conteudo[:conteudo.find("KNOWLEDGE_BASE")]:
            print("⚠️ Chat IA parece estar usando banco de conhecimento simulado!")
            return False
        
        if "TEMPLATE_RESPOSTAS = {" in conteudo and "'''" not in conteudo[:conteudo.find("TEMPLATE_RESPOSTAS")]:
            print("⚠️ Chat IA parece estar usando templates de resposta!")
            return False
        
        print("✅ Chat IA parece estar configurado para usar apenas dados reais")
        
        # Verificar se o endpoint de chat está funcionando
        async with aiohttp.ClientSession() as session:
            url = "http://localhost:5000/api/chat"
            
            try:
                payload = {"pergunta": "Como está o sistema?"}
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if "resposta" in result:
                            print("✅ Endpoint de chat está respondendo")
                            
                            # Verificar se a resposta parece real ou simulada
                            resposta = result["resposta"]
                            palavras_chave_simuladas = [
                                "dados simulados", "resposta simulada", 
                                "template", "dados fictícios"
                            ]
                            
                            if any(palavra in resposta.lower() for palavra in palavras_chave_simuladas):
                                print("⚠️ A resposta do chat contém referências a dados simulados!")
                                return False
                            
                            print("✅ A resposta do chat parece usar dados reais")
                            return True
                        else:
                            print("⚠️ Resposta do chat não contém campo 'resposta'")
                            return False
                    else:
                        print(f"❌ Endpoint de chat retornou erro: {response.status}")
                        return False
            except Exception as e:
                print(f"❌ Erro ao testar endpoint de chat: {e}")
                return False
    except Exception as e:
        print(f"❌ Erro ao verificar Chat IA: {e}")
        return False

async def main():
    """Função principal"""
    print("=== VERIFICAÇÃO RÁPIDA DO SISTEMA ANALYST_IA ===")
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Diretório base: {BASE_DIR}")
    print("=" * 50)
    
    # Verificar arquivo .env
    env_ok = verificar_env()
    
    # Verificar cache
    cache_ok = verificar_cache()
    
    # Verificar endpoints (apenas se for solicitado)
    endpoints_ok = False
    verificar_ep = input("\nVerificar endpoints? (pode falhar se o sistema não estiver rodando) [s/N]: ")
    if verificar_ep.lower() == 's':
        endpoints_ok = await verificar_endpoints()
    else:
        print("Verificação de endpoints ignorada.")
        endpoints_ok = True
    
    # Verificar chat (apenas se os endpoints estiverem ok)
    chat_ok = False
    if endpoints_ok:
        verificar_ch = input("\nVerificar Chat IA? (pode demorar alguns segundos) [s/N]: ")
        if verificar_ch.lower() == 's':
            chat_ok = await verificar_chat()
        else:
            print("Verificação do Chat IA ignorada.")
            chat_ok = True
    
    # Relatório final
    print("\n" + "=" * 50)
    print("RELATÓRIO DE VERIFICAÇÃO DO SISTEMA")
    print("=" * 50)
    print(f"✓ Configuração .env: {'OK' if env_ok else 'PROBLEMA'}")
    print(f"✓ Estado do cache: {'OK' if cache_ok else 'PROBLEMA'}")
    print(f"✓ Endpoints do sistema: {'OK' if endpoints_ok else 'PROBLEMA'}")
    print(f"✓ Chat IA: {'OK' if chat_ok else 'PROBLEMA'}")
    print("=" * 50)
    
    # Conclusão
    status_geral = all([env_ok, cache_ok, endpoints_ok, chat_ok])
    if status_geral:
        print("\n✅ Sistema verificado com sucesso!")
        print("Você pode iniciar o sistema usando um dos métodos a seguir:")
        print("  • VS Code Task: 'Iniciar Sistema Otimizado'")
        print("  • Windows: iniciar_sistema_otimizado_windows.bat")
        print("  • PowerShell: ./iniciar_sistema_otimizado.ps1")
    else:
        print("\n⚠️ Alguns problemas foram detectados.")
        print("Execute o script otimizar_sistema.py para corrigir os problemas.")

if __name__ == "__main__":
    asyncio.run(main())
