"""
Script para monitoramento local de APMs e VMs sem depender do New Relic.
Esta é uma alternativa simplificada para continuar monitorando seus recursos
sem exceder o limite do plano gratuito do New Relic.
"""

import os
import sys
import json
import time
import logging
import subprocess
import platform
import socket
import psutil
from datetime import datetime, timedelta
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
import csv

# Adicionar o diretório pai ao PATH para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger_config import setup_logger

# Configurar logger
logger = setup_logger('local_monitor')

# Diretório para armazenar dados de monitoramento
MONITOR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monitoramento_local")
HISTORY_DIR = os.path.join(MONITOR_DIR, "historico")

# Lista de serviços/aplicações a monitorar (adapte conforme necessário)
DEFAULT_SERVICES = [
    {"name": "API Sites", "type": "service", "url": "http://localhost:8080/health", "important": True},
    {"name": "API Users", "type": "service", "url": "http://localhost:8081/health", "important": True},
    {"name": "API Pagamentos", "type": "service", "url": "http://localhost:8082/health", "important": True},
    {"name": "Frontend", "type": "service", "url": "http://localhost:3000", "important": True},
    {"name": "Banco de Dados", "type": "database", "host": "localhost", "port": 5432, "important": True},
]

def carregar_config():
    """Carrega a configuração de monitoramento local"""
    config_path = os.path.join(MONITOR_DIR, "config.json")
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
    
    # Configuração padrão
    config = {
        "interval_seconds": 300,  # 5 minutos
        "retention_days": 30,
        "alert_threshold_cpu": 80,  # Porcentagem
        "alert_threshold_memory": 80,  # Porcentagem
        "alert_threshold_disk": 90,  # Porcentagem
        "services": DEFAULT_SERVICES,
        "notify_email": "",
        "notify_slack": "",
        "save_csv": True,
        "save_json": True
    }
    
    # Salvar configuração padrão
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuração padrão salva em {config_path}")
    except Exception as e:
        logger.error(f"Erro ao salvar configuração padrão: {e}")
    
    return config

async def verificar_servico_http(service):
    """Verifica a disponibilidade de um serviço HTTP"""
    url = service.get("url", "")
    if not url:
        return {"status": "error", "reason": "URL não especificada"}
    
    try:
        start_time = time.time()
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as response:
                    response_time = time.time() - start_time
                    
                    return {
                        "status": "ok" if response.status < 400 else "error",
                        "response_code": response.status,
                        "response_time": response_time,
                        "timestamp": datetime.now().isoformat()
                    }
            except asyncio.TimeoutError:
                return {
                    "status": "error",
                    "reason": "timeout",
                    "response_time": time.time() - start_time,
                    "timestamp": datetime.now().isoformat()
                }
    except Exception as e:
        return {
            "status": "error",
            "reason": str(e),
            "timestamp": datetime.now().isoformat()
        }

def verificar_servico_tcp(service):
    """Verifica a disponibilidade de um serviço TCP (ex: banco de dados)"""
    host = service.get("host", "localhost")
    port = service.get("port", 0)
    
    if not port:
        return {"status": "error", "reason": "Porta não especificada"}
    
    try:
        start_time = time.time()
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        result = s.connect_ex((host, port))
        s.close()
        
        response_time = time.time() - start_time
        
        if result == 0:
            return {
                "status": "ok",
                "response_time": response_time,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "reason": f"Não foi possível conectar (código: {result})",
                "response_time": response_time,
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "status": "error",
            "reason": str(e),
            "timestamp": datetime.now().isoformat()
        }

def coletar_metricas_sistema():
    """Coleta métricas do sistema local"""
    try:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # Memória
        mem = psutil.virtual_memory()
        
        # Disco
        disk = psutil.disk_usage('/')
        
        # Rede
        net_io = psutil.net_io_counters()
        
        # Processos
        process_count = len(list(psutil.process_iter()))
        
        # Tempo de atividade
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        return {
            "timestamp": datetime.now().isoformat(),
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "freq_mhz": cpu_freq.current if cpu_freq else None
            },
            "memory": {
                "total_gb": mem.total / (1024**3),
                "used_gb": mem.used / (1024**3),
                "percent": mem.percent
            },
            "disk": {
                "total_gb": disk.total / (1024**3),
                "used_gb": disk.used / (1024**3),
                "percent": disk.percent
            },
            "network": {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            },
            "system": {
                "process_count": process_count,
                "uptime_hours": uptime.total_seconds() / 3600
            }
        }
    except Exception as e:
        logger.error(f"Erro ao coletar métricas do sistema: {e}")
        return {
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

def coletar_processos_importantes():
    """Coleta informações sobre processos importantes"""
    processos_importantes = []
    
    try:
        # Palavras-chave para identificar processos importantes
        keywords = ["python", "node", "java", "analyst", "api", "server", "backend", "frontend"]
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'cmdline', 'cpu_percent', 'memory_percent']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                
                # Verificar se é um processo importante
                if any(keyword in cmdline.lower() for keyword in keywords) or \
                   any(keyword in (proc.info['name'] or "").lower() for keyword in keywords):
                    
                    # Obter mais informações
                    process = psutil.Process(proc.info['pid'])
                    
                    processos_importantes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "user": proc.info['username'],
                        "command": cmdline[:100] + ('...' if len(cmdline) > 100 else ''),
                        "cpu_percent": proc.info['cpu_percent'],
                        "memory_percent": proc.info['memory_percent'],
                        "created": datetime.fromtimestamp(process.create_time()).isoformat()
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        logger.error(f"Erro ao coletar processos importantes: {e}")
    
    return processos_importantes

async def monitorar_servicos(config):
    """Monitora todos os serviços configurados"""
    resultados = []
    
    for service in config["services"]:
        logger.info(f"Verificando serviço: {service['name']}")
        
        if service["type"] == "service":
            resultado = await verificar_servico_http(service)
        elif service["type"] == "database":
            resultado = verificar_servico_tcp(service)
        else:
            resultado = {"status": "unknown", "reason": f"Tipo desconhecido: {service['type']}"}
        
        resultados.append({
            "name": service["name"],
            "type": service["type"],
            "important": service.get("important", False),
            "result": resultado
        })
    
    return resultados

def salvar_resultados(data, config):
    """Salva resultados no formato especificado"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Criar diretórios se não existirem
    os.makedirs(MONITOR_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)
    
    # Salvar em JSON
    if config.get("save_json", True):
        json_path = os.path.join(MONITOR_DIR, "latest.json")
        history_json_path = os.path.join(HISTORY_DIR, f"monitor_{timestamp}.json")
        
        try:
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            with open(history_json_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Dados salvos em {json_path} e {history_json_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar JSON: {e}")
    
    # Salvar em CSV (apenas métricas principais)
    if config.get("save_csv", True):
        csv_path = os.path.join(MONITOR_DIR, "metricas.csv")
        
        # Extrair métricas principais
        row = {
            "timestamp": data["timestamp"],
            "cpu_percent": data["system"]["cpu"]["percent"],
            "memory_percent": data["system"]["memory"]["percent"],
            "disk_percent": data["system"]["disk"]["percent"],
            "process_count": data["system"]["system"]["process_count"],
        }
        
        # Adicionar status dos serviços
        for service in data["services"]:
            status_value = 1 if service["result"]["status"] == "ok" else 0
            row[f"service_{service['name'].replace(' ', '_').lower()}"] = status_value
        
        # Verificar se o arquivo existe
        file_exists = os.path.exists(csv_path)
        
        try:
            with open(csv_path, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=row.keys())
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerow(row)
            
            logger.info(f"Métricas adicionadas a {csv_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar CSV: {e}")
    
    # Limpar arquivos antigos
    limpar_historico(config.get("retention_days", 30))

def limpar_historico(days):
    """Remove arquivos de histórico mais antigos que o número de dias especificado"""
    try:
        limite = datetime.now() - timedelta(days=days)
        
        for filename in os.listdir(HISTORY_DIR):
            filepath = os.path.join(HISTORY_DIR, filename)
            
            if os.path.isfile(filepath):
                file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_time < limite:
                    os.remove(filepath)
                    logger.info(f"Arquivo antigo removido: {filepath}")
    except Exception as e:
        logger.error(f"Erro ao limpar histórico: {e}")

def verificar_alertas(data, config):
    """Verifica se há condições de alerta"""
    alertas = []
    
    # Verificar CPU
    if data["system"]["cpu"]["percent"] > config.get("alert_threshold_cpu", 80):
        alertas.append(f"ALERTA: CPU em {data['system']['cpu']['percent']}% (limite: {config.get('alert_threshold_cpu', 80)}%)")
    
    # Verificar memória
    if data["system"]["memory"]["percent"] > config.get("alert_threshold_memory", 80):
        alertas.append(f"ALERTA: Memória em {data['system']['memory']['percent']}% (limite: {config.get('alert_threshold_memory', 80)}%)")
    
    # Verificar disco
    if data["system"]["disk"]["percent"] > config.get("alert_threshold_disk", 90):
        alertas.append(f"ALERTA: Disco em {data['system']['disk']['percent']}% (limite: {config.get('alert_threshold_disk', 90)}%)")
    
    # Verificar serviços
    for service in data["services"]:
        if service.get("important", False) and service["result"]["status"] != "ok":
            alertas.append(f"ALERTA: Serviço {service['name']} está com problema: {service['result'].get('reason', 'desconhecido')}")
    
    # Registrar alertas
    if alertas:
        logger.warning("\n".join(alertas))
        
        # Salvar alertas
        alert_path = os.path.join(MONITOR_DIR, "alertas.txt")
        try:
            with open(alert_path, 'a') as f:
                f.write(f"\n--- {datetime.now().isoformat()} ---\n")
                f.write("\n".join(alertas))
                f.write("\n\n")
        except Exception as e:
            logger.error(f"Erro ao salvar alertas: {e}")
    
    return alertas

def exibir_dashboard(data, alertas):
    """Exibe um dashboard simples no terminal"""
    print("\n" + "=" * 80)
    print("MONITORAMENTO LOCAL - ANALYST_IA")
    print("=" * 80)
    
    print(f"\nData: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Hostname: {data['system']['hostname']}")
    print(f"Plataforma: {data['system']['platform']}")
    
    print("\nMÉTRICAS DO SISTEMA:")
    print(f"CPU: {data['system']['cpu']['percent']}% | ", end="")
    print(f"Memória: {data['system']['memory']['percent']}% | ", end="")
    print(f"Disco: {data['system']['disk']['percent']}%")
    
    print("\nSTATUS DOS SERVIÇOS:")
    for service in data["services"]:
        status = "✅" if service["result"]["status"] == "ok" else "❌"
        print(f"{status} {service['name']}", end=" | ")
        if service["result"]["status"] == "ok":
            print(f"Tempo de resposta: {service['result'].get('response_time', 0):.3f}s")
        else:
            print(f"Erro: {service['result'].get('reason', 'desconhecido')}")
    
    if alertas:
        print("\nALERTAS:")
        for alerta in alertas:
            print(f"⚠️ {alerta}")
    
    print("\nPROCESSOS IMPORTANTES:")
    for proc in data["processes"][:5]:  # Mostra apenas os 5 primeiros
        print(f"PID {proc['pid']} | {proc['name']} | CPU: {proc['cpu_percent']}% | MEM: {proc['memory_percent']}%")
    
    print("\nArquivos gerados:")
    print(f"- {os.path.join(MONITOR_DIR, 'latest.json')}")
    print(f"- {os.path.join(MONITOR_DIR, 'metricas.csv')}")
    
    print("=" * 80)

async def executar_monitoramento():
    """Executa uma iteração de monitoramento"""
    # Carregar configuração
    config = carregar_config()
    
    logger.info("Iniciando monitoramento local...")
    
    # Coletar métricas do sistema
    system_metrics = coletar_metricas_sistema()
    
    # Coletar processos importantes
    processos = coletar_processos_importantes()
    
    # Monitorar serviços
    servicos = await monitorar_servicos(config)
    
    # Combinar dados
    data = {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "hostname": system_metrics.get("hostname", "desconhecido"),
            "platform": system_metrics.get("platform", "desconhecido"),
            "cpu": system_metrics.get("cpu", {}),
            "memory": system_metrics.get("memory", {}),
            "disk": system_metrics.get("disk", {}),
            "network": system_metrics.get("network", {}),
            "system": system_metrics.get("system", {})
        },
        "services": servicos,
        "processes": processos
    }
    
    # Salvar resultados
    salvar_resultados(data, config)
    
    # Verificar alertas
    alertas = verificar_alertas(data, config)
    
    # Exibir dashboard
    exibir_dashboard(data, alertas)
    
    return data, alertas

async def monitoramento_continuo():
    """Executa monitoramento continuamente"""
    config = carregar_config()
    interval = config.get("interval_seconds", 300)
    
    print(f"\nIniciando monitoramento contínuo (intervalo: {interval} segundos)")
    print("Pressione Ctrl+C para interromper\n")
    
    try:
        while True:
            await executar_monitoramento()
            await asyncio.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitoramento interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro no monitoramento contínuo: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitoramento local de APMs e VMs")
    parser.add_argument("--once", action="store_true", help="Executa apenas uma vez")
    parser.add_argument("--interval", type=int, help="Intervalo em segundos para monitoramento contínuo")
    args = parser.parse_args()
    
    # Criar diretório de monitoramento
    os.makedirs(MONITOR_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)
    
    # Se especificado um novo intervalo, atualiza a configuração
    if args.interval:
        config = carregar_config()
        config["interval_seconds"] = args.interval
        
        config_path = os.path.join(MONITOR_DIR, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Intervalo atualizado para {args.interval} segundos")
    
    if args.once:
        # Executar apenas uma vez
        asyncio.run(executar_monitoramento())
    else:
        # Executar continuamente
        asyncio.run(monitoramento_continuo())
