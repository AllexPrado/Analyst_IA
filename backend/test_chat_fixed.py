#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar o endpoint de chat do Analyst-IA
"""
import requests
import json
import sys
from pathlib import Path

# Configuração básica
print("=" * 80)
print(" 🧪 TESTE DO ENDPOINT DE CHAT")
print("=" * 80)

# URL do endpoint
url = "http://localhost:8000/api/chat"
pergunta = "Como está o sistema?"

try:
    print(f"Enviando pergunta: '{pergunta}'")
    response = requests.post(url, json={"pergunta": pergunta})
    
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Conexão bem-sucedida")
        try:
            data = response.json()
            print(f"Resposta: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print("✅ Resposta JSON válida")
        except json.JSONDecodeError:
            print(f"❌ Resposta não é um JSON válido: {response.text}")
    else:
        print(f"❌ Status code inesperado: {response.status_code}")
        print(f"Resposta: {response.text}")
        
except Exception as e:
    print(f"❌ Erro ao fazer requisição: {str(e)}")
    
print("=" * 80)
