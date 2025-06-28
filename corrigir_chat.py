#!/usr/bin/env python3
"""
Script para corrigir o problema do chat no Analyst-IA
"""

import requests
import sys
import os
import time
import json
from pathlib import Path

print("=== Correção do Chat do Analyst-IA ===\n")

# Verifica se o backend está em execução
def check_backend():
    try:
        response = requests.get("http://localhost:8000/api/status", timeout=5)
        if response.status_code == 200:
            print("✅ Backend está em execução")
            return True
        else:
            print(f"❌ Backend retornou status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar backend: {str(e)}")
        return False

# Testa o endpoint de chat
def test_chat():
    print("\nTestando endpoint de chat...")
    
    try:
        # Teste com mensagem de saudação
        response = requests.post(
            "http://localhost:8000/api/chat",
            json={"pergunta": "oi"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Endpoint de chat funcionando! Resposta: {data.get('message')[:50]}...")
            return True
        else:
            print(f"❌ Endpoint de chat falhou: Status {response.status_code}")
            print(f"Resposta: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Erro ao testar chat: {str(e)}")
        return False

# Corrige o problema do endpoint de chat no backend
def fix_chat_backend():
    backend_file = Path("backend/unified_backend.py")
    backup_file = Path("backend/unified_backend.py.bak")
    
    if not backend_file.exists():
        print(f"❌ Arquivo {backend_file} não encontrado")
        return False
    
    print(f"Fazendo backup do arquivo {backend_file}...")
    backup_file.write_bytes(backend_file.read_bytes())
    
    # Lê o conteúdo do arquivo
    content = backend_file.read_text(encoding="utf-8")
    
    # Procura pela definição da classe ChatInput
    chat_input_def = "class ChatInput(BaseModel):"
    pergunta_field = 'pergunta: str = Field(..., description="Pergunta para a IA")'
    
    if chat_input_def in content and pergunta_field in content:
        # Adiciona campo message para compatibilidade
        message_field = 'message: Optional[str] = Field(None, description="Campo alternativo para compatibilidade")'
        if message_field not in content:
            print("Adicionando campo 'message' para compatibilidade...")
            content = content.replace(
                pergunta_field,
                pergunta_field + "\n    " + message_field
            )
        
        # Atualiza a função do endpoint para aceitar message
        chat_endpoint = '@app.post("/api/chat")\nasync def chat_endpoint(input: ChatInput):'
        original_line = 'pergunta = input.pergunta'
        compatibility_code = """    # Compatibilidade com clientes que enviam 'message' em vez de 'pergunta'
    if not pergunta and hasattr(input, 'message') and input.message:
        pergunta = input.message
        logger.info(f"Campo 'message' usado em vez de 'pergunta': '{pergunta}'")"""
        
        if chat_endpoint in content and original_line in content and compatibility_code not in content:
            print("Adicionando código de compatibilidade para 'message'...")
            content = content.replace(
                original_line,
                original_line + "\n" + compatibility_code
            )
        
        # Salva o arquivo atualizado
        backend_file.write_text(content, encoding="utf-8")
        print("✅ Backend corrigido com sucesso")
        return True
    else:
        print("❌ Não foi possível encontrar o código para corrigir")
        return False

# Corrige o frontend
def fix_chat_frontend():
    api_file = Path("frontend/src/api/backend.js")
    
    if not api_file.exists():
        print(f"❌ Arquivo {api_file} não encontrado")
        return False
    
    # Lê o conteúdo do arquivo
    content = api_file.read_text(encoding="utf-8")
    
    # Procura pela função getChatResposta
    target_line = "export const getChatResposta = (pergunta) => api.post('/chat', { pergunta })"
    replacement = "export const getChatResposta = (pergunta) => api.post('/chat', { pergunta: pergunta })"
    
    if target_line in content:
        print("Corrigindo chamada da API no frontend...")
        content = content.replace(target_line, replacement)
        api_file.write_text(content, encoding="utf-8")
        print("✅ Frontend corrigido com sucesso")
        return True
    else:
        print("❌ Não foi possível encontrar o código para corrigir no frontend")
        return False

# Verifica conflito de parâmetros no openai_connector.py
def fix_openai_connector():
    connector_file = Path("backend/utils/openai_connector.py")
    
    if not connector_file.exists():
        print(f"❌ Arquivo {connector_file} não encontrado")
        return False
    
    # Lê o conteúdo do arquivo
    content = connector_file.read_text(encoding="utf-8")
    
    # Verifica se há algum parâmetro temperatura na função gerar_resposta_ia
    if "async def gerar_resposta_ia" in content:
        if "temperatura" in content and "temperatura=0.5" not in content:
            print("Verificando problema de parâmetro 'temperatura'...")
            # Encontra declaração e implementação da função
            function_def_idx = content.find("async def gerar_resposta_ia")
            
            if function_def_idx != -1:
                # Verifica se o parâmetro está na assinatura
                function_sig = content[function_def_idx:content.find(")", function_def_idx)]
                
                if "temperatura" not in function_sig and "temperatura" in content[function_def_idx:]:
                    print("Problema identificado: chamando com parâmetro 'temperatura' que não existe na função")
                    print("✅ Este problema já foi corrigido nos arquivos do backend")
                    return True
    
    return True

def main():
    # Verifica se o backend está em execução
    if not check_backend():
        print("\n❌ O backend não está em execução. Por favor, inicie-o com:")
        print("python start_unified_backend.py")
        return 1
    
    # Testa o chat
    if test_chat():
        print("\n✅ O endpoint de chat já está funcionando corretamente!")
    else:
        print("\n❌ Problema detectado no endpoint de chat. Iniciando correções...")
        
        # Corrige o backend
        if fix_chat_backend():
            print("\nBackend corrigido. É necessário reiniciar o servidor.")
            
            # Corrige o frontend
            if fix_openai_connector() and fix_chat_frontend():
                print("\n✅ Todas as correções foram aplicadas!")
                print("\nPor favor, reinicie o backend e o frontend:")
                print("1. Encerre o backend atual")
                print("2. Execute: python start_unified_backend.py")
                print("3. Em outro terminal, reinicie o frontend: cd frontend && npm run dev")
                print("\nOu simplesmente execute: python reiniciar_sistema.py")
            else:
                print("\n❌ Algumas correções falharam. Verifique os erros acima.")
                return 1
        else:
            print("\n❌ Não foi possível corrigir o backend")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
