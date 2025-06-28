import asyncio
import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
import random

# Adicionar o diretório atual ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.cache import get_cache, _cache, salvar_cache_no_disco

# Dados de exemplo para gerar alertas e incidentes
APLICACOES = ["API de Pagamentos", "Portal do Cliente", "Serviço de Autenticação", "Backend de Processamento", "Sistema de Notificações"]
SERVIDORES = ["srv-prod-01", "srv-prod-02", "srv-app-01", "db-cluster-01", "cache-server-01"]
SEVERIDADES = ["critical", "warning", "info"]
TIPOS_ALERTA = ["transaction_duration", "apdex_violation", "error_percentage", "memory_usage", "cpu_usage", "disk_space"]

async def gerar_dados_exemplo():
    """Gera dados de exemplo para alertas e incidentes"""
    try:
        print("Iniciando a geração de dados de exemplo para alertas e incidentes...")
        
        # Obter cache atual
        cache = await get_cache()
        
        # Gerar alertas de exemplo
        num_alertas = random.randint(3, 8)  # Entre 3 e 8 alertas
        print(f"Gerando {num_alertas} alertas de exemplo...")
        
        alertas = []
        agora = datetime.now()
        
        for i in range(num_alertas):
            # Calcular momento aleatório nos últimos 7 dias
            horas_atras = random.randint(1, 168)  # Até 7 dias (168 horas)
            timestamp = agora - timedelta(hours=horas_atras)
            
            # Dados do alerta
            aplicacao = random.choice(APLICACOES)
            servidor = random.choice(SERVIDORES)
            severidade = random.choice(SEVERIDADES)
            tipo = random.choice(TIPOS_ALERTA)
            
            # Criar alerta
            alerta = {
                "id": f"alert-{i+1}-{int(timestamp.timestamp())}",
                "name": f"Alerta de {tipo} em {aplicacao}",
                "description": f"Detectado {tipo} acima do limite em {aplicacao} no servidor {servidor}",
                "severity": severidade,
                "timestamp": timestamp.isoformat(),
                "entity": {
                    "name": aplicacao,
                    "type": "APPLICATION" if "API" in aplicacao or "Portal" in aplicacao else "SERVICE",
                    "server": servidor
                },
                "condition": {
                    "type": tipo,
                    "threshold": random.uniform(75, 99) if "percentage" in tipo else random.uniform(2, 10),
                    "duration": f"{random.randint(5, 30)} minutos"
                },
                "current_state": "active" if random.random() < 0.7 else "closed",
                "link": f"https://onenr.io/alert/{i+1}-{int(timestamp.timestamp())}"
            }
            
            alertas.append(alerta)
        
        # Gerar incidentes baseados em alguns dos alertas
        num_incidentes = min(3, num_alertas)  # Até 3 incidentes, não mais que os alertas
        print(f"Gerando {num_incidentes} incidentes de exemplo...")
        
        incidentes = []
        for i in range(num_incidentes):
            alerta_relacionado = alertas[i]
            timestamp = datetime.fromisoformat(alerta_relacionado["timestamp"])
            
            # Status: 70% em andamento, 30% resolvidos
            status = "em_andamento" if random.random() < 0.7 else "resolvido"
            
            # Se resolvido, adicionar data de resolução
            resolvido_em = None
            duracao = None
            if status == "resolvido":
                horas_para_resolver = random.randint(1, 24)
                resolvido_em = timestamp + timedelta(hours=horas_para_resolver)
                duracao = f"{horas_para_resolver} horas"
            
            # Criar incidente
            incidente = {
                "id": f"inc-{i+1}-{int(timestamp.timestamp())}",
                "title": f"Incidente: {alerta_relacionado['name']}",
                "description": f"Incidente aberto a partir do alerta: {alerta_relacionado['description']}",
                "severity": alerta_relacionado["severity"],
                "opened_at": timestamp.isoformat(),
                "resolved_at": resolvido_em.isoformat() if resolvido_em else None,
                "state": status,
                "duration": duracao,
                "impacted_service": alerta_relacionado["entity"]["name"],
                "impacted_server": alerta_relacionado["entity"]["server"],
                "related_alert_ids": [alerta_relacionado["id"]],
                "assigned_to": f"suporte-{random.randint(1, 5)}@empresa.com",
                "actions_taken": [
                    f"Análise inicial em {(timestamp + timedelta(minutes=random.randint(5, 30))).isoformat()}",
                    f"Identificação da causa em {(timestamp + timedelta(minutes=random.randint(30, 60))).isoformat()}"
                ] if random.random() < 0.8 else []
            }
            
            incidentes.append(incidente)
        
        # Adicionar ao cache
        _cache["dados"]["alertas"] = alertas
        _cache["dados"]["incidentes"] = incidentes
        
        # Adicionar métricas da última semana para as entidades
        entidades = cache.get("entidades", [])
        if entidades:
            print(f"Adicionando métricas da última semana para {len(entidades)} entidades...")
            
            for entidade in entidades:
                # Verificar se já tem métricas
                if "metricas" not in entidade:
                    entidade["metricas"] = {}
                
                # Adicionar dados da última semana
                entidade["metricas"]["7d"] = {
                    "uptime": [{"latest.uptime": random.uniform(0.95, 0.999)}],
                    "response_time": [{"latest.response_time": random.uniform(0.2, 2.0)}],
                    "error_rate": [{"latest.error_rate": random.uniform(0.01, 0.05)}],
                    "throughput": [{"latest.throughput": random.uniform(100, 1000)}]
                }
        
        # Salvar cache atualizado
        print("Salvando cache atualizado...")
        await salvar_cache_no_disco()
        
        # Criar relatório
        relatorio = {
            "timestamp": datetime.now().isoformat(),
            "alertas_gerados": num_alertas,
            "incidentes_gerados": num_incidentes,
            "entidades_atualizadas": len(entidades),
            "status": "sucesso"
        }
        
        # Salvar relatório
        Path("historico").mkdir(exist_ok=True)
        relatorio_path = Path("historico") / f"geracao_dados_exemplo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(relatorio_path, "w", encoding="utf-8") as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False)
        
        print(f"\nDados de exemplo gerados com sucesso!")
        print(f"- {num_alertas} alertas")
        print(f"- {num_incidentes} incidentes")
        print(f"- Métricas de 7 dias para {len(entidades)} entidades")
        print(f"\nRelatório salvo em: {relatorio_path}")
        
    except Exception as e:
        print(f"Erro ao gerar dados de exemplo: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(gerar_dados_exemplo())
