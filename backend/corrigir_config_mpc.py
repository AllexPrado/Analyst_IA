"""
Script para corrigir a configuração do MPC

Este script garante que a configuração do MPC esteja correta,
especialmente a URL base para comunicação com os agentes.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/fix_mpc_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("fix_mpc_config")

def verificar_portas_mpc():
    """Verifica em qual porta o servidor MPC está rodando"""
    import requests
    
    portas_conhecidas = [10876, 9876, 8765]
    
    for porta in portas_conhecidas:
        try:
            logger.info(f"Verificando porta {porta}...")
            response = requests.get(f"http://localhost:{porta}/", timeout=2)
            if response.status_code == 200:
                logger.info(f"✅ Servidor encontrado na porta {porta}")
                return porta
        except Exception:
            pass
    
    logger.warning("⚠️ Nenhum servidor MPC encontrado nas portas conhecidas")
    return None

def corrigir_configuracao_mpc(porta=None):
    """Corrige a configuração do MPC"""
    config_dir = os.path.join("config")
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "mpc_agents.json")
    
    # Se não foi especificada uma porta, tentar descobrir
    if porta is None:
        porta = verificar_portas_mpc()
        if porta is None:
            logger.warning("⚠️ Usando porta padrão 10876 já que nenhum servidor foi detectado")
            porta = 10876
    
    logger.info(f"Corrigindo configuração para usar porta {porta}...")
    
    # Configuração base
    config_base = {
        "agents": [
            {
                "id": "agno",
                "name": "Agno - Agente Principal",
                "description": "Agente principal de orquestração que processa comandos em linguagem natural",
                "endpoint": "/agno",
                "enabled": True
            },
            {
                "id": "agent-s",
                "name": "Agent-S - Agente de Serviço",
                "description": "Agente de serviço que executa tarefas sob orientação do Agno",
                "endpoint": "/agent-s",
                "enabled": True
            },
            {
                "id": "diagnostico",
                "name": "Agente de Diagnóstico",
                "description": "Realiza diagnósticos do sistema e identifica problemas",
                "endpoint": "/diagnose",
                "enabled": True
            }
        ],
        "base_url": f"http://localhost:{porta}/agent",
        "timeout": 30,
        "retry_attempts": 3,
        "retry_delay": 5
    }
    
    # Se a configuração já existe, preservar os agentes configurados
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config_atual = json.load(f)
            
            # Preservar lista de agentes se existir
            if "agents" in config_atual and isinstance(config_atual["agents"], list):
                config_base["agents"] = config_atual["agents"]
            
            logger.info(f"Configuração existente atualizada para usar porta {porta}")
        except Exception as e:
            logger.error(f"Erro ao ler configuração existente: {e}")
    
    # Salvar configuração
    try:
        with open(config_path, "w") as f:
            json.dump(config_base, f, indent=2)
        
        logger.info(f"✅ Configuração salva em {config_path}")
        
        # Mostrar configuração salva
        logger.info("Configuração atualizada:")
        logger.info(f"- URL Base: {config_base['base_url']}")
        logger.info(f"- Timeout: {config_base['timeout']} segundos")
        logger.info(f"- Agentes: {len(config_base['agents'])}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao salvar configuração: {e}")
        return False

def criar_script_inicializacao_mpc(porta=10876):
    """Cria/atualiza script de inicialização do MPC"""
    # Caminho para o script de inicialização
    script_path = os.path.join("iniciar_servidor_mpc.bat")
    
    logger.info(f"Criando script de inicialização na porta {porta}...")
    
    # Conteúdo do script batch para Windows
    conteudo = f"""@echo off
echo Iniciando servidor MPC na porta {porta}...
python mpc_server.py --port {porta}
"""

    try:
        with open(script_path, "w") as f:
            f.write(conteudo)
        
        logger.info(f"✅ Script de inicialização criado: {script_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao criar script de inicialização: {e}")
        return False

def criar_script_teste_comunicacao():
    """Cria um script simples para testar a comunicação com o Agno"""
    script_path = os.path.join("testar_comunicacao_agno.py")
    
    logger.info("Criando script de teste de comunicação...")
    
    conteudo = """\"\"\"
Script simples para testar comunicação com o Agno
\"\"\"

import asyncio
import json
from core_inteligente.agno_interface import AgnoInterface

async def main():
    print("Testando comunicação com o Agno...")
    
    # Criar interface
    agno = AgnoInterface()
    agno.iniciar_sessao()
    
    # Verificar status
    print("\\n1. Verificando status...")
    status = await agno.verificar_status()
    print(f"Resultado do status: {json.dumps(status, indent=2)}")
    
    # Enviar mensagem
    print("\\n2. Enviando mensagem simples...")
    resposta = await agno.enviar_mensagem("Olá, Agno! Como está funcionando?")
    print(f"Resposta: {json.dumps(resposta, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
"""

    try:
        with open(script_path, "w") as f:
            f.write(conteudo)
        
        logger.info(f"✅ Script de teste criado: {script_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao criar script de teste: {e}")
        return False

def main():
    """Função principal"""
    logger.info("=== Iniciando correção da configuração MPC ===")
    
    # Verificar porta do servidor MPC
    porta = verificar_portas_mpc()
    
    # Corrigir configuração
    if corrigir_configuracao_mpc(porta):
        logger.info("✅ Configuração MPC corrigida com sucesso")
    else:
        logger.error("❌ Falha ao corrigir configuração MPC")
    
    # Criar script de inicialização
    if criar_script_inicializacao_mpc(porta or 10876):
        logger.info("✅ Script de inicialização atualizado")
    
    # Criar script de teste
    if criar_script_teste_comunicacao():
        logger.info("✅ Script de teste de comunicação criado")
    
    logger.info("\n=== Próximos passos ===")
    logger.info("1. Reinicie o servidor MPC usando o script iniciar_servidor_mpc.bat")
    logger.info("2. Execute o script testar_comunicacao_agno.py para verificar a comunicação")
    logger.info("3. Use o script diagnosticar_agno.py para diagnóstico completo")

if __name__ == "__main__":
    # Criar diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)
    
    # Executar correção
    main()
