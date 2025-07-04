"""
Script para verificar se o backend e o frontend estão funcionando corretamente
"""

import requests
import sys
import os
import logging
import json
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URLs para teste
BACKEND_URL = "http://localhost:8000/api/health"
FRONTEND_URL = "http://localhost:5173"

def verificar_backend():
    """Verificar se o backend está respondendo"""
    try:
        logger.info("Testando conexão com o backend...")
        response = requests.get(BACKEND_URL, timeout=5)
        response.raise_for_status()
        
        logger.info(f"✅ Backend OK: {response.status_code}")
        logger.info(f"✅ Resposta: {response.json()}")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erro no backend: {str(e)}")
        return False

def verificar_entidades():
    """Verificar se o endpoint de entidades está retornando dados válidos"""
    try:
        logger.info("Testando endpoint de entidades...")
        response = requests.get("http://localhost:8000/api/entidades", timeout=5)
        response.raise_for_status()
        
        entidades = response.json()
        
        if not entidades:
            logger.warning("⚠️ Endpoint de entidades retornou uma lista vazia!")
            return False
            
        logger.info(f"✅ Endpoint de entidades retornou {len(entidades)} registros")
        
        # Vamos verificar a primeira entidade
        if entidades:
            first_entity = entidades[0]
            logger.info(f"📂 Primeira entidade: {first_entity.get('name')} ({first_entity.get('domain')})")
            
            # Verificar se tem métricas
            metrics = first_entity.get('metricas', {})
            if metrics:
                periods = list(metrics.keys())
                logger.info(f"📊 Períodos disponíveis: {', '.join(periods)}")
                
                # Verificar métricas do primeiro período
                if periods:
                    first_period = periods[0]
                    first_period_metrics = metrics.get(first_period, {})
                    logger.info(f"📈 Métricas para {first_period}: {len(first_period_metrics)} métricas")
            else:
                logger.warning("⚠️ Entidade sem métricas!")
        
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erro no endpoint de entidades: {str(e)}")
        return False

def verificar_chat():
    """Verificar se o endpoint de chat está funcionando"""
    try:
        logger.info("Testando endpoint de chat...")
        
        payload = {"pergunta": "Resumo do status do sistema"}
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(
            "http://localhost:8000/api/chat", 
            json=payload,
            headers=headers,
            timeout=10  # Chat pode levar mais tempo
        )
        
        response.raise_for_status()
        
        logger.info(f"✅ Endpoint de chat respondeu: {response.status_code}")
        
        # Verificar resposta
        data = response.json()
        if 'resposta' in data:
            # Mostrar apenas os primeiros 100 caracteres da resposta
            resposta = data['resposta'][:100] + "..." if len(data['resposta']) > 100 else data['resposta']
            logger.info(f"💬 Resposta: {resposta}")
            return True
        else:
            logger.warning("⚠️ Resposta do chat sem campo 'resposta'")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erro no endpoint de chat: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=== VERIFICAÇÃO DE SERVIÇOS ===")
    
    # Verificar backend
    backend_ok = verificar_backend()
    
    if backend_ok:
        # Verificar entidades
        entidades_ok = verificar_entidades()
        
        # Verificar chat (opcional)
        chat_ok = verificar_chat()
        
        # Resumo
        logger.info("\n=== RESUMO DA VERIFICAÇÃO ===")
        logger.info(f"Backend: {'✅ Funcionando' if backend_ok else '❌ Com problemas'}")
        logger.info(f"Endpoint Entidades: {'✅ Funcionando' if entidades_ok else '❌ Com problemas'}")
        logger.info(f"Endpoint Chat: {'✅ Funcionando' if chat_ok else '❌ Com problemas'}")
        
        if backend_ok and entidades_ok:
            logger.info("\n✅ Sistema básico funcionando corretamente!")
            
            # Sugestões para o usuário
            logger.info("\n--- RECOMENDAÇÕES ---")
            logger.info("1. Inicie o frontend: cd frontend && npm run dev")
            logger.info("2. Acesse a interface em: http://localhost:5173")
            logger.info("3. Se visualizar 'N/A' nos cards, verifique se as entidades têm métricas reais")
        else:
            logger.info("\n⚠️ Sistema funcionando parcialmente. Verifique os erros acima.")
    else:
        logger.error("\n❌ Backend não está funcionando! Verifique o serviço.")
        logger.info("  Tente iniciar o backend: cd backend && python start_simple.py")
        
    logger.info("\n=== FIM DA VERIFICAÇÃO ===")
