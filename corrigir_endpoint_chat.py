#!/usr/bin/env python3
"""
Script para verificar o status do endpoint de chat e corrigir problemas comuns
"""

import os
import sys
import json
import logging
import requests
from pathlib import Path
import asyncio
import importlib.util

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Constantes
BACKEND_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{BACKEND_URL}/api/chat"
STATUS_ENDPOINT = f"{BACKEND_URL}/api/status"

def check_backend_running():
    """Verifica se o backend está em execução"""
    try:
        response = requests.get(STATUS_ENDPOINT, timeout=5)
        if response.status_code == 200:
            logger.info("✅ Backend está em execução")
            return True
        else:
            logger.error(f"❌ Backend retornou status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Erro ao verificar backend: {str(e)}")
        return False

def test_chat_endpoint():
    """Testa o endpoint de chat com diferentes payloads"""
    if not check_backend_running():
        logger.error("Backend não está em execução. Não é possível testar o endpoint de chat.")
        return False

    test_messages = [
        {"pergunta": "oi"},
        {"pergunta": "mensagem_inicial"},
        {"message": "oi"},  # Teste com campo incorreto
    ]
    
    success = False
    for i, payload in enumerate(test_messages, 1):
        try:
            logger.info(f"\nTeste {i}: Enviando payload: {payload}")
            response = requests.post(CHAT_ENDPOINT, json=payload, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"✅ Teste {i} bem-sucedido!")
                logger.info(f"Resposta recebida ({len(response.text)} caracteres): {response.text[:100]}...")
                success = True
                break
            else:
                logger.error(f"❌ Teste {i} falhou. Status code: {response.status_code}")
                logger.error(f"Resposta: {response.text[:200]}")
        except Exception as e:
            logger.error(f"❌ Erro no Teste {i}: {str(e)}")
    
    return success

def fix_chat_endpoint():
    """Corrige o endpoint de chat"""
    # Caminho para o arquivo unified_backend.py
    unified_backend_path = Path("backend/unified_backend.py")
    
    if not unified_backend_path.exists():
        logger.error(f"❌ Arquivo {unified_backend_path} não encontrado")
        return False
    
    # Lê o conteúdo do arquivo
    content = unified_backend_path.read_text(encoding="utf-8")
    
    # Define um backup
    backup_path = unified_backend_path.with_suffix(".py.bak")
    backup_path.write_text(content, encoding="utf-8")
    logger.info(f"Backup criado em {backup_path}")
    
    # Verifica e adiciona um tratamento para compatibilidade com "message"
    class_def_line = "class ChatInput(BaseModel):"
    message_line = '    pergunta: str = Field(..., description="Mensagem enviada pelo usuário")'
    campo_message_line = '    message: Optional[str] = Field(None, description="Campo alternativo para compatibilidade")'
    
    if class_def_line in content and message_line in content and campo_message_line not in content:
        # Adiciona o campo message
        modified_content = content.replace(
            message_line,
            message_line + "\n" + campo_message_line
        )
        
        # Adiciona lógica para mapear message para pergunta
        endpoint_start = "@app.post(\"/api/chat\")\nasync def chat_endpoint(input: ChatInput):"
        pergunta_line = "    pergunta = input.pergunta"
        message_check = """    # Compatibilidade com clientes que enviam 'message' em vez de 'pergunta'
    if not pergunta and hasattr(input, 'message') and input.message:
        pergunta = input.message
        logger.info(f"Campo 'message' usado em vez de 'pergunta': '{pergunta}'")"""
        
        if endpoint_start in modified_content and pergunta_line in modified_content:
            modified_content = modified_content.replace(
                pergunta_line,
                pergunta_line + "\n" + message_check
            )
            
            # Salva o arquivo modificado
            unified_backend_path.write_text(modified_content, encoding="utf-8")
            logger.info("✅ Arquivo unified_backend.py modificado com sucesso")
            return True
    
    logger.error("❌ Não foi possível modificar o arquivo unified_backend.py")
    return False

def wait_for_backend_restart():
    """Aguarda o backend reiniciar"""
    logger.info("Aguardando o backend reiniciar...")
    attempts = 0
    max_attempts = 30  # 30 segundos
    
    while attempts < max_attempts:
        try:
            response = requests.get(STATUS_ENDPOINT, timeout=1)
            if response.status_code == 200:
                logger.info("✅ Backend reiniciado com sucesso!")
                return True
        except:
            pass
        
        attempts += 1
        if attempts % 5 == 0:
            logger.info(f"Ainda aguardando... ({attempts}s)")
        
        time.sleep(1)
    
    logger.error("❌ Tempo esgotado aguardando o backend reiniciar")
    return False

def main():
    """Função principal"""
    logger.info("=== Verificador e Corretor do Endpoint de Chat ===\n")
    
    # Verifica se o backend está rodando
    if not check_backend_running():
        logger.error("Por favor, inicie o backend antes de executar este script")
        return 1
    
    # Testa o endpoint de chat
    logger.info("\n=== Testando endpoint de chat ===")
    chat_success = test_chat_endpoint()
    
    if not chat_success:
        logger.info("\n=== Corrigindo endpoint de chat ===")
        if fix_chat_endpoint():
            logger.info("\n=== Por favor reinicie o backend e execute este script novamente ===")
            return 0
        else:
            logger.error("Não foi possível corrigir o endpoint de chat automaticamente")
            return 1
    else:
        logger.info("\n✅ O endpoint de chat está funcionando corretamente!")
    
    return 0

if __name__ == "__main__":
    import time
    sys.exit(main())
