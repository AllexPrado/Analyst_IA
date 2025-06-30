"""
[OBSOLETO] Script para gerar dados de demonstração para o frontend.
Este script foi desabilitado para garantir que apenas dados reais do New Relic sejam usados.
"""
import os
import json
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Configurar o logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Função principal que gera todos os dados
def main():
    """Função principal do script - DESABILITADA"""
    logger.warning("ATENÇÃO: Este script está desabilitado para garantir que apenas dados reais sejam utilizados.")
    logger.warning("Por favor, use 'atualizar_cache_completo.py' para coletar dados reais do New Relic.")
    return False

if __name__ == "__main__":
    logger.error("======================================================================")
    logger.error("ERRO: Este script está desabilitado e não deve mais ser utilizado.")
    logger.error("O sistema Analyst IA agora requer apenas dados reais do New Relic.")
    logger.error("Por favor, use 'python atualizar_cache_completo.py' para atualizar o cache.")
    logger.error("======================================================================")
    sys.exit(1)

# Todas as funções de geração de dados simulados foram mantidas apenas para referência,
# mas não devem ser chamadas em nenhuma circunstância.

# O restante do arquivo original foi mantido para documentação.

def generate_insights_data():
    """Gera dados de insights para o frontend"""
    return {
        "roiMonitoramento": round(random.uniform(3.5, 8.5), 1),
        "roiAumento": round(random.uniform(5, 15), 1),
        "aumentoProdutividade": round(random.uniform(15, 35), 1),
        "produtividadeComparativo": round(random.uniform(5, 15), 1),
        "horasEconomizadas": round(random.uniform(80, 150)),
        "economiaTotal": round(random.uniform(25000, 75000), 2),
        "economiaAumento": round(random.uniform(5, 20), 1),
        "incidentesEvitados": round(random.uniform(15, 45)),
        "satisfacao": round(random.uniform(7.5, 9.5), 1),
        "satisfacaoAumento": round(random.uniform(0.2, 1.2), 1),
        "avaliacoes": round(random.uniform(20, 50)),
        "impactoSeries": [
            {
                "name": "Atual",
                "data": [
                    round(random.uniform(12000, 18000)),
                    round(random.uniform(20000, 30000)), 
                    round(random.uniform(30000, 40000)),
                    round(random.uniform(15000, 22000)),
                    round(random.uniform(25000, 35000))
                ]
            },
            {
                "name": "Potencial com otimizações",
                "data": [
                    round(random.uniform(15000, 22000)),
                    round(random.uniform(27000, 37000)),
                    round(random.uniform(37000, 47000)),
                    round(random.uniform(20000, 28000)),
                    round(random.uniform(32000, 42000))
                ]
            }
        ],
        "problemasSeries": [
            {
                "name": "Incidentes Ocorridos",
                "data": [18, 15, 12, 8, 7, 5, 4]
            },
            {
                "name": "Incidentes Evitados",
                "data": [5, 8, 12, 15, 18, 22, 25]
            }
        ],
        "recomendacoes": [
            {
                "titulo": "Otimização de queries SQL lentas",
                "descricao": "Adicionar índices para as queries que estão consumindo mais recursos",
                "categoria": "performance",
                "prioridade": "Alta",
                "impacto": 8.5,
                "esforco": "Médio"
            },
            {
                "titulo": "Implementar cache de dados de sessão",
                "descricao": "Reduzir chamadas ao banco utilizando Redis para armazenar dados de sessão",
                "categoria": "eficiencia",
                "prioridade": "Média",
                "impacto": 7.0,
                "esforco": "Baixo"
            },
            {
                "titulo": "Consolidar servidores de aplicação",
                "descricao": "Reduzir a quantidade de servidores subutilizados no ambiente de homologação",
                "categoria": "custo",
                "prioridade": "Média",
                "impacto": 6.5,
                "esforco": "Alto"
            },
            {
                "titulo": "Atualizar bibliotecas de segurança",
                "descricao": "Atualizar componentes com vulnerabilidades conhecidas",
                "categoria": "seguranca",
                "prioridade": "Alta",
                "impacto": 9.0,
                "esforco": "Médio"
            },
            {
                "titulo": "Implementar rate limiting em APIs públicas",
                "descricao": "Prevenir abusos e ataques DoS em endpoints públicos",
                "categoria": "seguranca",
                "prioridade": "Alta",
                "impacto": 8.0,
                "esforco": "Baixo"
            },
            {
                "titulo": "Otimizar carregamento de assets frontend",
                "descricao": "Implementar lazy loading e compressão avançada para melhorar UX",
                "categoria": "performance",
                "prioridade": "Baixa",
                "impacto": 5.0,
                "esforco": "Baixo"
            }
        ]
    }

def generate_kpis_data():
    """Gera dados de KPIs para o frontend"""
    return {
        "performance": {
            "apdex": round(random.uniform(0.7, 0.95), 2),
            "tempo_resposta": round(random.uniform(0.1, 2.0), 2),
            "tendencia": round(random.uniform(-10, 10), 1),
            "historico": [0.72, 0.75, 0.78, 0.82, 0.85, 0.89]
        },
        "disponibilidade": {
            "uptime": round(random.uniform(98, 99.99), 2),
            "total_servicos": random.randint(40, 60),
            "servicos_disponiveis": random.randint(35, 59),
            "tendencia": round(random.uniform(-1, 1), 2),
            "historico": [98.5, 98.7, 99.1, 99.3, 99.5, 99.7]
        },
        "erros": {
            "taxa_erro": round(random.uniform(0.1, 3.0), 2),
            "tendencia": round(random.uniform(-20, 5), 1),
            "total_requisicoes": random.randint(100000, 500000),
            "requisicoes_com_erro": random.randint(100, 5000),
            "historico": [2.5, 2.2, 1.8, 1.5, 1.2, 0.8]
        },
        "throughput": {
            "requisicoes_por_minuto": random.randint(1000, 5000),
            "tendencia": round(random.uniform(-5, 15), 1),
            "pico": random.randint(5000, 10000),
            "historico": [2200, 2500, 2800, 3100, 3500, 3800]
        }
    }

def generate_cobertura_data():
    """Gera dados de cobertura para o frontend"""
    total_entidades = random.randint(150, 200)
    monitoradas = random.randint(int(total_entidades * 0.7), total_entidades)
    
    return {
        "total_entidades": total_entidades,
        "monitoradas": monitoradas,
        "porcentagem": round((monitoradas / total_entidades) * 100, 1),
        "por_dominio": {
            "APM": {
                "total": random.randint(40, 60),
                "monitoradas": random.randint(30, 50),
                "criticas": random.randint(5, 15)
            },
            "BROWSER": {
                "total": random.randint(30, 40),
                "monitoradas": random.randint(20, 30),
                "criticas": random.randint(3, 10)
            },
            "INFRA": {
                "total": random.randint(60, 80),
                "monitoradas": random.randint(50, 70),
                "criticas": random.randint(10, 20)
            },
            "MOBILE": {
                "total": random.randint(10, 20),
                "monitoradas": random.randint(5, 15),
                "criticas": random.randint(2, 8)
            }
        },
        "historico": {
            "labels": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"],
            "series": [
                {
                    "name": "Cobertura (%)",
                    "data": [65, 70, 75, 78, 82, round((monitoradas / total_entidades) * 100, 1)]
                }
            ]
        }
    }

def generate_tendencias_data():
    """Gera dados de tendências para o frontend"""
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"]
    return {
        "apdex": {
            "labels": meses,
            "series": [
                {
                    "name": "Web",
                    "data": [0.72, 0.75, 0.78, 0.82, 0.85, 0.87]
                },
                {
                    "name": "Mobile",
                    "data": [0.68, 0.71, 0.75, 0.79, 0.82, 0.84]
                },
                {
                    "name": "API",
                    "data": [0.81, 0.83, 0.84, 0.86, 0.88, 0.91]
                }
            ]
        },
        "erros": {
            "labels": meses,
            "series": [
                {
                    "name": "Erros por minuto",
                    "data": [42, 38, 35, 30, 25, 18]
                }
            ]
        },
        "tempos_resposta": {
            "labels": meses,
            "series": [
                {
                    "name": "Web (ms)",
                    "data": [320, 310, 290, 275, 260, 240]
                },
                {
                    "name": "Mobile (ms)",
                    "data": [380, 360, 340, 330, 315, 300]
                },
                {
                    "name": "API (ms)",
                    "data": [120, 115, 110, 105, 100, 95]
                }
            ]
        },
        "throughput": {
            "labels": meses,
            "series": [
                {
                    "name": "Requisições/min",
                    "data": [2200, 2500, 2800, 3100, 3400, 3800]
                }
            ]
        },
        "usos_recursos": {
            "labels": meses,
            "series": [
                {
                    "name": "CPU (%)",
                    "data": [65, 68, 72, 75, 78, 72]
                },
                {
                    "name": "Memória (%)",
                    "data": [58, 62, 68, 72, 75, 70]
                },
                {
                    "name": "Disco (%)",
                    "data": [45, 48, 52, 55, 58, 62]
                }
            ]
        }
    }

def generate_resumo_geral_data():
    """Gera dados de resumo geral para o frontend"""
    return {
        "status_geral": random.choice(["SAUDÁVEL", "ATENÇÃO", "CRÍTICO"]),
        "alertas_ativos": random.randint(0, 5),
        "entidades_monitoradas": random.randint(150, 200),
        "indicadores": {
            "apdex": round(random.uniform(0.7, 0.95), 2),
            "erro": round(random.uniform(0.1, 3.0), 2),
            "latencia": round(random.uniform(0.1, 2.0), 2),
            "throughput": random.randint(1000, 5000),
        },
        "entidades_por_status": {
            "saudaveis": random.randint(100, 150),
            "atencao": random.randint(10, 30),
            "criticas": random.randint(0, 10)
        },
        "principais_alertas": [
            {
                "entidade": "api-gateway",
                "severidade": "CRÍTICO",
                "mensagem": "Latência elevada nas chamadas externas",
                "desde": "2025-06-29T08:15:30Z"
            },
            {
                "entidade": "payment-service",
                "severidade": "ATENÇÃO",
                "mensagem": "Taxa de erro acima do limiar",
                "desde": "2025-06-29T09:30:00Z"
            },
            {
                "entidade": "user-db",
                "severidade": "ATENÇÃO",
                "mensagem": "Uso de CPU elevado",
                "desde": "2025-06-28T23:45:10Z"
            }
        ]
    }

def generate_status_data():
    """Gera dados de status para o frontend"""
    return {
        "servidor": "online",
        "cache": "atualizado",
        "ultima_atualizacao": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "servicos": {
            "coleta": "ativo",
            "analise": "ativo",
            "alerta": "ativo"
        },
        "metricas": {
            "entidades_monitoradas": 157,
            "dados_coletados_mb": 1230,
            "alertas_ativos": 3
        }
    }

def generate_fake_entidades():
    """Gera entidades simuladas com dados avançados"""
    dominios = ["APM", "BROWSER", "MOBILE", "INFRA"]
    entidades = []
    
    for i in range(random.randint(30, 60)):
        dominio = random.choice(dominios)
        entidade = {
            "id": f"ent-{i}-{dominio.lower()}",
            "guid": f"NR-{dominio}-{random.randint(10000, 99999)}",
            "name": f"{dominio.lower()}-entity-{i}",
            "domain": dominio,
            "status": random.choice(["OK", "ALERTA", "ERRO"]),
            "metricas": {
                "ultima_hora": {
                    "apdex": random.uniform(0.7, 0.98),
                    "response_time_max": random.uniform(100, 2000),
                    "throughput": random.uniform(10, 1000),
                    "error_rate": random.uniform(0, 5)
                }
            },
            # Dados avançados
            "logs": [
                {
                    "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 60))).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "level": random.choice(["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"]),
                    "message": f"Log message {i}-{j}",
                    "context": {"service": f"{dominio.lower()}-entity-{i}", "request_id": f"req-{random.randint(1000, 9999)}"}
                }
                for j in range(random.randint(0, 5))
            ],
            "traces": [
                {
                    "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 60))).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "name": f"transaction-{i}-{j}",
                    "duration": random.uniform(10, 2000),
                    "endpoint": f"/api/{random.choice(['users', 'orders', 'products', 'auth'])}/{random.randint(1, 100)}",
                    "spans": [
                        {
                            "name": f"span-{k}",
                            "duration": random.uniform(1, 200)
                        }
                        for k in range(random.randint(0, 8))
                    ]
                }
                for j in range(random.randint(0, 3))
            ],
            "queries": [
                {
                    "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 60))).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "database": "postgres",
                    "operation": random.choice(["SELECT", "INSERT", "UPDATE", "DELETE"]),
                    "duration": random.uniform(1, 500),
                    "query": f"SELECT * FROM table_{random.randint(1, 10)} WHERE id = {random.randint(1, 1000)}"
                }
                for j in range(random.randint(0, 4))
            ],
            "errors": [
                {
                    "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 60))).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "message": f"Error in service: {random.choice(['connection refused', 'timeout', 'validation error', 'null reference'])}",
                    "type": random.choice(["RuntimeError", "ConnectionError", "ValidationError", "TypeError"]),
                    "stack": f"at function_{random.randint(1, 100)} (line {random.randint(10, 500)})\n" +
                            f"at module_{random.randint(1, 20)} (line {random.randint(10, 500)})"
                }
                for j in range(random.randint(0, 2))
            ]
        }
        entidades.append(entidade)
    
    return entidades
