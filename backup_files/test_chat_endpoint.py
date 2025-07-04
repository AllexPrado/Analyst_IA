"""
Teste do endpoint de chat para verificar se o erro AttributeError foi corrigido
"""

import os
import sys
import asyncio
import json
import logging
from pathlib import Path
from pydantic import BaseModel

# Configura logging
logging.basicConfig(level=logging.INFO,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adiciona diretório pai ao path para poder importar módulos corretamente
script_dir = Path(__file__).parent
sys.path.append(str(script_dir))

# Classe para simular a entrada do endpoint de chat
class ChatInput(BaseModel):
    pergunta: str
    historico: list = []

# Importa a função do endpoint de chat
try:
    from main import chat_endpoint
except ImportError as e:
    logger.error(f"Erro ao importar módulos necessários: {e}")
    sys.exit(1)

async def testar_chat_endpoint():
    """Testa o endpoint de chat que estava apresentando AttributeError"""
    print("\n🔍 Testando endpoint de chat...")
    
    try:
        # Cria objeto de entrada
        entrada = ChatInput(pergunta="Qual o status atual do sistema?")
        
        # Chama o endpoint
        resultado = await chat_endpoint(entrada)
        
        # Se chegou aqui, não houve erros
        print("✅ Endpoint de chat funcionando corretamente!")
        print(f"  - Resposta recebida com {len(resultado.get('resposta', ''))} caracteres")
        
        # Verifica se o contexto foi montado corretamente
        contexto = resultado.get("contexto", {})
        if contexto:
            print(f"  - Contexto gerado com {len(contexto)} elementos")
        
        return True
    except Exception as e:
        print(f"❌ Erro no endpoint de chat: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Iniciando teste do endpoint de chat...")
    sucesso = asyncio.run(testar_chat_endpoint())
    
    if sucesso:
        print("\n✅ Teste concluído com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Teste falhou!")
        sys.exit(1)
