#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar a integração de dados entre backend e frontend
"""
import requests
import json
import sys
from datetime import datetime
from pathlib import Path
import time
import os

# Configuração básica
BASE_URL = "http://localhost:8000/api"
ENDPOINTS = [
    "/status",
    "/kpis",
    "/tendencias",
    "/cobertura", 
    "/insights"
]

def check_null_values(data, path=""):
    """
    Verifica valores nulos ou inválidos nos dados
    Retorna uma lista de caminhos com valores nulos
    """
    issues = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            new_path = f"{path}.{key}" if path else key
            if value is None:
                issues.append(f"Valor nulo encontrado em: {new_path}")
            elif value == "":
                issues.append(f"String vazia encontrada em: {new_path}")
            elif isinstance(value, (dict, list)):
                issues.extend(check_null_values(value, new_path))
    
    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_path = f"{path}[{i}]"
            if item is None:
                issues.append(f"Valor nulo encontrado em: {new_path}")
            elif item == "":
                issues.append(f"String vazia encontrada em: {new_path}")
            elif isinstance(item, (dict, list)):
                issues.extend(check_null_values(item, new_path))
    
    return issues

def check_endpoint_data(endpoint):
    """Verifica os dados retornados por um endpoint específico"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Verificando endpoint: {endpoint}")
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Falha na requisição: Status code {response.status_code}")
            return False, []
        
        try:
            data = response.json()
            
            # Verificar se é um dicionário vazio
            if isinstance(data, dict) and not data:
                print(f"❌ Endpoint retornou dicionário vazio")
                return False, []
            
            # Verificar se é uma lista vazia
            if isinstance(data, list) and not data:
                print(f"❌ Endpoint retornou lista vazia")
                return False, []
                
            # Verificar valores nulos
            issues = check_null_values(data)
            
            if issues:
                print(f"⚠️ Encontrados {len(issues)} problemas nos dados:")
                for issue in issues[:10]:  # Mostrar apenas os 10 primeiros problemas
                    print(f"  - {issue}")
                if len(issues) > 10:
                    print(f"  ... e mais {len(issues) - 10} problemas")
                return True, issues
            else:
                print(f"✅ Dados validados sem problemas")
                return True, []
                
        except json.JSONDecodeError:
            print(f"❌ Resposta não é JSON válido")
            return False, []
            
    except Exception as e:
        print(f"❌ Erro ao testar endpoint: {str(e)}")
        return False, []

def check_entidade_fields():
    """Verifica se os campos essenciais estão presentes nas entidades"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Verificando dados das entidades")
    
    try:
        response = requests.get(f"{BASE_URL}/entidades", timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Falha na requisição: Status code {response.status_code}")
            return False
            
        entidades = response.json()
        
        if not entidades:
            print("❌ Nenhuma entidade encontrada")
            return False
            
        print(f"✓ Total de entidades: {len(entidades)}")
        
        # Campos essenciais que devem existir
        campos_essenciais = ["name", "domain", "status"]
        campos_metricas = ["apdex", "error_rate", "response_time", "throughput"]
        
        entidades_com_problemas = 0
        
        for i, entidade in enumerate(entidades[:10]):  # Analisar as 10 primeiras entidades
            print(f"\nVerificando entidade {i+1}: {entidade.get('name', 'Sem nome')}")
            
            # Verificar campos essenciais
            for campo in campos_essenciais:
                if campo not in entidade or entidade[campo] is None:
                    print(f"  ❌ Campo essencial ausente: {campo}")
                    entidades_com_problemas += 1
            
            # Verificar métricas
            if "metricas" not in entidade or not entidade["metricas"]:
                print(f"  ❌ Métricas ausentes")
                entidades_com_problemas += 1
                continue
                
            # Verificar período de métricas
            periodos = ["ultima_hora", "24h", "7d", "30d"]
            periodo_encontrado = False
            
            for periodo in periodos:
                if periodo in entidade["metricas"] and entidade["metricas"][periodo]:
                    periodo_encontrado = True
                    print(f"  ✓ Métricas do período '{periodo}' encontradas")
                    
                    # Verificar campos de métricas
                    metricas_periodo = entidade["metricas"][periodo]
                    for metrica in campos_metricas:
                        if metrica not in metricas_periodo or metricas_periodo[metrica] is None:
                            print(f"  ⚠️ Métrica ausente: {metrica} no período {periodo}")
            
            if not periodo_encontrado:
                print(f"  ❌ Nenhum período de métricas válido encontrado")
                entidades_com_problemas += 1
        
        if entidades_com_problemas == 0:
            print("\n✅ Todas as entidades analisadas têm os campos necessários")
            return True
        else:
            print(f"\n⚠️ {entidades_com_problemas} entidades com problemas")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar entidades: {str(e)}")
        return False

def check_chat_response():
    """Testa a qualidade da resposta do chat"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Verificando resposta do chat")
    
    perguntas = [
        "Como está o sistema?",
        "Quais são as principais métricas?",
        "Existem alertas ativos?"
    ]
    
    for pergunta in perguntas:
        print(f"\nPergunta: '{pergunta}'")
        
        try:
            response = requests.post(
                f"{BASE_URL}/chat", 
                json={"pergunta": pergunta},
                timeout=20
            )
            
            if response.status_code != 200:
                print(f"❌ Falha na requisição: Status code {response.status_code}")
                continue
                
            resposta = response.json()
            
            # Verificar se contém dados estruturados ou apenas texto
            if "resposta" not in resposta:
                print("❌ Resposta do chat não contém campo 'resposta'")
                continue
            
            # Verificar tamanho da resposta
            tamanho_resposta = len(resposta.get("resposta", ""))
            print(f"✓ Tamanho da resposta: {tamanho_resposta} caracteres")
            
            if tamanho_resposta < 100:
                print("⚠️ Resposta muito curta, possivelmente superficial")
            
            # Verificar presença de entidades
            if "entidades" in resposta and resposta["entidades"]:
                print(f"✓ Resposta contém {len(resposta['entidades'])} entidades")
            
            # Verificar dados de contexto
            if "contexto" in resposta and resposta["contexto"]:
                print("✓ Resposta contém dados de contexto")
                
            # Verificar se tem resumo de métricas
            if "resumoMetricas" in resposta and resposta["resumoMetricas"]:
                print("✓ Resposta contém resumo de métricas")
                
            # Verificar se a resposta contém valores numéricos
            if any(char.isdigit() for char in resposta.get("resposta", "")):
                print("✓ Resposta contém valores numéricos")
            else:
                print("⚠️ Resposta não contém valores numéricos")
                
            # Verificar se menciona pelo menos uma entidade pelo nome
            entidades_conhecidas = ["API-Pagamentos", "API-Autenticacao", "Database-Principal"]
            if any(entidade in resposta.get("resposta", "") for entidade in entidades_conhecidas):
                print("✓ Resposta menciona entidades pelo nome")
            else:
                print("⚠️ Resposta não menciona entidades pelo nome")
                
            print(f"Resposta: {resposta.get('resposta', '')[:300]}...")
                
        except Exception as e:
            print(f"❌ Erro ao testar chat: {str(e)}")

def main():
    print("=" * 80)
    print(" 🔍 VERIFICAÇÃO DE INTEGRAÇÃO DE DADOS FRONTEND-BACKEND")
    print("=" * 80)
    
    # Verificar se a API está acessível
    print("\nVerificando acesso à API...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API não está acessível. Status: {response.status_code}")
            return
        print("✅ API está acessível")
    except Exception as e:
        print(f"❌ Não foi possível acessar a API: {str(e)}")
        print("Por favor, certifique-se de que o backend está em execução")
        return
    
    # Verificar dados de cada endpoint
    problemas_totais = 0
    for endpoint in ENDPOINTS:
        success, issues = check_endpoint_data(endpoint)
        if success and issues:
            problemas_totais += len(issues)
    
    # Verificar entidades
    if not check_entidade_fields():
        print("\n⚠️ Problemas detectados nas entidades")
    
    # Verificar respostas do chat
    check_chat_response()
    
    print("\n" + "=" * 80)
    if problemas_totais > 0:
        print(f" ⚠️ VERIFICAÇÃO CONCLUÍDA: {problemas_totais} problemas encontrados")
    else:
        print(" ✅ VERIFICAÇÃO CONCLUÍDA: Nenhum problema crítico encontrado")
    print("=" * 80)

if __name__ == "__main__":
    main()
