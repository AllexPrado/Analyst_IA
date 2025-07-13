"""
Script para verificar quando o New Relic estará disponível novamente após exceder o limite de 100 GB.
Este script monitora o status do plano e alerta quando o New Relic voltar a estar disponível.
"""

import os
import sys
import json
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
import argparse
from dotenv import load_dotenv

# Adicionar o diretório pai ao PATH para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger_config import setup_logger

# Configurar logger
logger = setup_logger('newrelic_status')

# Arquivo para armazenar status do New Relic
STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                         "cache", "newrelic_status.json")

async def verificar_status_newrelic():
    """Verifica o status atual do New Relic - se está disponível ou com limite excedido"""
    # Carregar variáveis de ambiente
    load_dotenv()
    api_key = os.getenv('NEW_RELIC_API_KEY')
    account_id = os.getenv('NEW_RELIC_ACCOUNT_ID')
    
    if not api_key or not account_id:
        logger.error("Chaves de API New Relic não encontradas no arquivo .env")
        return {"status": "erro", "mensagem": "Credenciais não configuradas"}
    
    try:
        # URL da API do New Relic para verificar conta
        url = f"https://api.newrelic.com/v2/accounts/{account_id}"
        headers = {
            "Api-Key": api_key,
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    # Plano está ativo
                    logger.info("New Relic está disponível")
                    return {"status": "disponivel", "mensagem": "New Relic está disponível"}
                elif response.status == 402:
                    # Pagamento necessário / limite excedido
                    logger.warning("New Relic não está disponível: limite excedido (402)")
                    return {"status": "indisponivel", "mensagem": "Limite excedido (402)", "codigo": 402}
                elif response.status == 403:
                    # Acesso negado - pode indicar restrições do plano gratuito
                    logger.warning("New Relic com acesso restrito (403)")
                    return {"status": "restrito", "mensagem": "Acesso restrito (403)", "codigo": 403}
                else:
                    logger.error(f"Erro desconhecido ao acessar New Relic: {response.status}")
                    return {"status": "erro", "mensagem": f"Erro desconhecido ({response.status})", "codigo": response.status}
    except Exception as e:
        logger.error(f"Erro ao verificar status do New Relic: {e}")
        return {"status": "erro", "mensagem": str(e)}

def salvar_status(status):
    """Salva o status atual do New Relic no arquivo de cache"""
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    
    # Adicionar timestamp e histórico
    status_completo = {
        "timestamp": datetime.now().isoformat(),
        "status": status
    }
    
    # Carregar histórico anterior, se existir
    historico = []
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                dados = json.load(f)
                if "historico" in dados:
                    historico = dados["historico"]
        except:
            pass
    
    # Limitar histórico a 30 entradas
    historico.append(status_completo)
    if len(historico) > 30:
        historico = historico[-30:]
    
    # Salvar com histórico
    with open(STATUS_FILE, 'w') as f:
        json.dump({
            "atual": status,
            "ultima_verificacao": datetime.now().isoformat(),
            "historico": historico
        }, f, indent=2)

def carregar_status():
    """Carrega o status mais recente do New Relic do arquivo de cache"""
    if not os.path.exists(STATUS_FILE):
        return None
    
    try:
        with open(STATUS_FILE, 'r') as f:
            dados = json.load(f)
            return dados
    except:
        return None

def estimar_proxima_disponibilidade():
    """Estima quando o New Relic estará disponível novamente baseado no histórico"""
    dados = carregar_status()
    if not dados or "historico" not in dados or not dados["historico"]:
        return None
    
    # Procurar padrão de mudança de status
    disponibilidades = []
    indisponibilidades = []
    
    for item in dados["historico"]:
        try:
            timestamp = datetime.fromisoformat(item["timestamp"])
            status = item["status"]["status"]
            
            if status == "disponivel":
                disponibilidades.append(timestamp)
            elif status == "indisponivel" or status == "restrito":
                indisponibilidades.append(timestamp)
        except:
            pass
    
    # Se não houver histórico suficiente, estimar baseado no padrão típico mensal
    if not disponibilidades or not indisponibilidades:
        # Estimar primeiro dia do próximo mês como data de reset
        hoje = datetime.now()
        proximo_mes = hoje.replace(day=1) + timedelta(days=32)
        primeiro_dia_proximo_mes = proximo_mes.replace(day=1)
        
        return {
            "proxima_disponibilidade": primeiro_dia_proximo_mes.isoformat(),
            "dias_restantes": (primeiro_dia_proximo_mes - hoje).days,
            "confianca": "baixa",
            "metodo": "estimativa baseada no ciclo mensal padrão"
        }
    
    # Tentar detectar padrão baseado no histórico
    # Este é um modelo simplificado - na vida real, você pode precisar de mais dados
    return {
        "proxima_disponibilidade": (datetime.now() + timedelta(days=30)).isoformat(),
        "dias_restantes": 30,
        "confianca": "média",
        "metodo": "estimativa baseada no histórico limitado"
    }

async def main():
    parser = argparse.ArgumentParser(description="Verificar status do New Relic")
    parser.add_argument("--silent", action="store_true", help="Executa sem saída no console")
    args = parser.parse_args()
    
    logger.info("Verificando status do New Relic...")
    status = await verificar_status_newrelic()
    salvar_status(status)
    
    if not args.silent:
        print("\n" + "=" * 80)
        print("STATUS DO NEW RELIC")
        print("=" * 80)
        
        print(f"\nData/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"Status: {status['status'].upper()}")
        print(f"Mensagem: {status['mensagem']}")
        
        if status['status'] != "disponivel":
            estimativa = estimar_proxima_disponibilidade()
            
            if estimativa:
                data_estimada = datetime.fromisoformat(estimativa["proxima_disponibilidade"]).strftime("%d/%m/%Y")
                print(f"\nEstimativa de disponibilidade:")
                print(f"- Data estimada: {data_estimada}")
                print(f"- Dias restantes: {estimativa['dias_restantes']}")
                print(f"- Confiança: {estimativa['confianca']}")
                print(f"- Método: {estimativa['metodo']}")
            
            print("\nRecomendação:")
            print("- Continue usando o monitoramento local (monitoramento_local.py)")
            print("- Verifique regularmente o status do New Relic")
            print("- Quando voltar a ficar disponível, reconfigure-o com limites de uso")
        else:
            print("\nRecomendação:")
            print("- New Relic está disponível! Execute:")
            print("  python reativar_newrelic.py --otimizado")
            print("- Configure limites estritos de coleta para não exceder 100 GB novamente")
        
        print("=" * 80)
    
    return status

if __name__ == "__main__":
    asyncio.run(main())
