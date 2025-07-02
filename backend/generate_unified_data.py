#!/usr/bin/env python3
"""
Script unificado para gerar dados de teste consistentes para todos os módulos
"""

import json
import os
from datetime import datetime
from pathlib import Path
import random
import logging
import shutil

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def generate_unified_data():
    """
    Gera dados de teste unificados para todos os componentes do sistema.
    Isto garante que o formato seja consistente em todos os módulos.
    """
    # Diretórios que precisam existir
    diretorios = [
        Path("historico"),
        Path("dados"),
        Path("dados/historico"),
        Path("historico/consultas")
    ]
    
    # Garantir que todos os diretórios existem
    for dir_path in diretorios:
        os.makedirs(dir_path, exist_ok=True)
        logger.info(f"Diretório verificado: {dir_path}")
    
    # Lista de entidades para teste
    entidades_teste = [
        {
            "name": "API-Pagamentos",
            "domain": "APM",
            "guid": "test-guid-1",
            "entityType": "APPLICATION",
            "reporting": True,
            "testing": True,  # Flag para identificar dados de teste
            "metricas": {
                "30min": {
                    "apdex": 0.85,
                    "response_time": 245.5,  # Adicionado para compatibilidade
                    "response_time_max": 245.5,
                    "error_rate": 2.1,
                    "throughput": 1250.0,
                    "recent_error": "Connection timeout"
                },
                "3h": {
                    "apdex": 0.88,
                    "response_time": 220.3,  # Adicionado para compatibilidade
                    "response_time_max": 220.3,
                    "error_rate": 1.8,
                    "throughput": 1180.0
                },
                "24h": {
                    "apdex": 0.90,
                    "response_time": 180.2,  # Adicionado para compatibilidade
                    "response_time_max": 180.2,
                    "error_rate": 1.5,
                    "throughput": 1100.0
                }
            }
        },
        {
            "name": "API-Autenticacao",
            "domain": "APM",
            "guid": "test-guid-2",
            "entityType": "APPLICATION",
            "reporting": True,
            "testing": True,  # Flag para identificar dados de teste
            "metricas": {
                "30min": {
                    "apdex": 0.92,
                    "response_time": 125.8,  # Adicionado para compatibilidade
                    "response_time_max": 125.8,
                    "error_rate": 0.8,
                    "throughput": 2500.0
                },
                "3h": {
                    "apdex": 0.91,
                    "response_time": 135.2,  # Adicionado para compatibilidade
                    "response_time_max": 135.2,
                    "error_rate": 1.0,
                    "throughput": 2300.0
                },
                "24h": {
                    "apdex": 0.89,
                    "response_time": 150.1,  # Adicionado para compatibilidade
                    "response_time_max": 150.1,
                    "error_rate": 1.2,
                    "throughput": 2200.0
                }
            }
        },
        {
            "name": "Database-Principal",
            "domain": "INFRA",
            "guid": "test-guid-3",
            "entityType": "DATABASE",
            "reporting": True,
            "testing": True,  # Flag para identificar dados de teste
            "metricas": {
                "30min": {
                    "apdex": 0.78,
                    "response_time": 450.2,  # Adicionado para compatibilidade
                    "response_time_max": 450.2,
                    "error_rate": 0.5,
                    "throughput": 800.0
                },
                "3h": {
                    "apdex": 0.80,
                    "response_time": 420.1,  # Adicionado para compatibilidade
                    "response_time_max": 420.1,
                    "error_rate": 0.4,
                    "throughput": 750.0
                },
                "24h": {
                    "apdex": 0.82,
                    "response_time": 380.5,  # Adicionado para compatibilidade
                    "response_time_max": 380.5,
                    "error_rate": 0.3,
                    "throughput": 700.0
                }
            }
        }
    ]

    # Dados para o cache principal
    cache_data = {
        "entidades": entidades_teste,
        "timestamp": datetime.now().isoformat(),
        "total_entidades": len(entidades_teste),
        "contagem_por_dominio": {
            "APM": 2,
            "INFRA": 1
        },
        "timestamp_atualizacao": datetime.now().isoformat(),
        "tipo_coleta": "dados_teste_desenvolvimento",
        "metadados": {
            "ultima_atualizacao": datetime.now().isoformat(),
            "status": "atualizado",
            "integridade": "ok"
        }
    }
    
    # 1. Gerar cache_completo.json
    cache_file = Path("historico") / "cache_completo.json"
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Cache criado em: {cache_file}")
    
    # Criar arquivo de backup
    backup_file = Path("historico") / f"cache_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Backup do cache criado em: {backup_file}")
    
    # 2. Gerar dados/cobertura.json
    coverage_data = {
        "total_entidades": 157,
        "monitoradas": 138,
        "porcentagem": 87.9,
        "por_dominio": {
            "APM": {
                "total": 53,
                "monitoradas": 47,
                "criticas": 12
            },
            "BROWSER": {
                "total": 35,
                "monitoradas": 30,
                "criticas": 8
            },
            "INFRA": {
                "total": 69,
                "monitoradas": 61,
                "criticas": 15
            }
        },
        "historico": {
            "labels": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"],
            "series": [
                {
                    "name": "Cobertura (%)",
                    "data": [65, 70, 75, 78, 82, 87.9]
                }
            ]
        }
    }
    
    cobertura_file = Path("dados") / "cobertura.json"
    with open(cobertura_file, 'w', encoding='utf-8') as f:
        json.dump(coverage_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Dados de cobertura criados em: {cobertura_file}")
    
    # 3. Gerar dados/kpis.json
    kpis_data = {
        "performance": {
            "apdex": 0.87,
            "tempo_resposta": 1.2,
            "tendencia": 5.2,
            "historico": [0.72, 0.75, 0.78, 0.82, 0.85, 0.87]
        },
        "disponibilidade": {
            "uptime": 99.85,
            "total_servicos": 54,
            "servicos_disponiveis": 53,
            "tendencia": 0.3,
            "historico": [98.5, 98.7, 99.1, 99.3, 99.5, 99.7]
        },
        "erros": {
            "taxa_erro": 1.2,
            "tendencia": -12.5,
            "total_requisicoes": 356789,
            "requisicoes_com_erro": 4281,
            "historico": [2.5, 2.2, 1.8, 1.5, 1.2, 0.8]
        },
        "throughput": {
            "requisicoes_por_minuto": 3400,
            "tendencia": 8.2,
            "pico": 7850,
            "historico": [2200, 2500, 2800, 3100, 3400, 3800]
        }
    }
    
    kpis_file = Path("dados") / "kpis.json"
    with open(kpis_file, 'w', encoding='utf-8') as f:
        json.dump(kpis_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Dados de KPIs criados em: {kpis_file}")
    
    # 4. Gerar dados/tendencias.json
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun"]
    tendencias_data = {
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
        }
    }
    
    tendencias_file = Path("dados") / "tendencias.json"
    with open(tendencias_file, 'w', encoding='utf-8') as f:
        json.dump(tendencias_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Dados de tendências criados em: {tendencias_file}")
    
    # 5. Gerar dados/insights.json
    insights_data = [
        {
            "id": "insight-1",
            "tipo": "performance",
            "severidade": "alta",
            "titulo": "Alta latência na API de Pagamentos",
            "descricao": "A API de Pagamentos está apresentando tempos de resposta 45% acima do normal nas últimas 3 horas.",
            "impacto": "Isso está causando lentidão no processamento de transações e possivelmente afetando a experiência do usuário.",
            "causa_provavel": "Aumento no volume de requisições sem escalabilidade adequada.",
            "recomendacao": "Verificar a escalabilidade dos servidores e considerar aumentar recursos temporariamente.",
            "entidades_afetadas": ["API-Pagamentos"],
            "tendencia": "crescente",
            "data_identificacao": "2025-06-29T18:30:00Z"
        },
        {
            "id": "insight-2",
            "tipo": "erro",
            "severidade": "média",
            "titulo": "Aumento na taxa de erro no serviço de Autenticação",
            "descricao": "O serviço de Autenticação está apresentando um aumento de 2.1% na taxa de erro nas últimas 30 minutos.",
            "impacto": "Alguns usuários podem estar enfrentando dificuldades para fazer login na plataforma.",
            "causa_provavel": "Recente implantação de nova funcionalidade pode estar causando falhas.",
            "recomendacao": "Revisar os logs de erro para identificar o padrão específico e considerar rollback se necessário.",
            "entidades_afetadas": ["API-Autenticacao"],
            "tendencia": "estável",
            "data_identificacao": "2025-06-30T10:15:00Z"
        },
        {
            "id": "insight-3",
            "tipo": "recurso",
            "severidade": "baixa",
            "titulo": "Uso elevado de CPU no banco de dados",
            "descricao": "O banco de dados principal está operando com uso de CPU acima de 70% nas últimas 24 horas.",
            "impacto": "Baixo impacto no momento, mas pode causar degradação de performance se aumentar.",
            "causa_provavel": "Queries não otimizadas ou aumento no volume de dados.",
            "recomendacao": "Revisar as queries mais pesadas e considerar otimização.",
            "entidades_afetadas": ["Database-Principal"],
            "tendencia": "decrescente",
            "data_identificacao": "2025-06-28T22:45:00Z"
        }
    ]
    
    insights_file = Path("dados") / "insights.json"
    with open(insights_file, 'w', encoding='utf-8') as f:
        json.dump(insights_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Dados de insights criados em: {insights_file}")
    
    # 6. Gerar dados/status.json
    status_data = {
        "servidor": "online",
        "cache": "atualizado",
        "ultima_atualizacao": datetime.now().isoformat(),
        "servicos": {
            "coleta": "ativo",
            "analise": "ativo",
            "alerta": "ativo"
        },
        "metricas": {
            "entidades_monitoradas": 138,
            "dados_coletados_mb": 756,
            "alertas_ativos": 3
        }
    }
    
    status_file = Path("dados") / "status.json"
    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Dados de status criados em: {status_file}")
    
    # 7. Gerar dados/resumo-geral.json
    resumo_data = {
        "status_geral": "ATENÇÃO",
        "alertas_ativos": 3,
        "entidades_monitoradas": 138,
        "indicadores": {
            "apdex": 0.87,
            "erro": 1.2,
            "latencia": 1.2,
            "throughput": 3400
        },
        "entidades_por_status": {
            "saudaveis": 125,
            "atencao": 11,
            "criticas": 2
        },
        "principais_alertas": [
            {
                "entidade": "API-Pagamentos",
                "severidade": "ALTA",
                "mensagem": "Alta latência nas chamadas externas",
                "desde": "2025-06-29T18:30:00Z"
            },
            {
                "entidade": "API-Autenticacao",
                "severidade": "MÉDIA",
                "mensagem": "Aumento na taxa de erro",
                "desde": "2025-06-30T10:15:00Z"
            },
            {
                "entidade": "Database-Principal",
                "severidade": "BAIXA",
                "mensagem": "Uso elevado de CPU",
                "desde": "2025-06-28T22:45:00Z"
            }
        ]
    }
    
    resumo_file = Path("dados") / "resumo-geral.json"
    with open(resumo_file, 'w', encoding='utf-8') as f:
        json.dump(resumo_data, f, ensure_ascii=False, indent=2)
    logger.info(f"Dados de resumo geral criados em: {resumo_file}")
    
    # Duplicar os arquivos para garantir que possam ser encontrados de qualquer caminho relativo
    for src_file in [cobertura_file, kpis_file, tendencias_file, insights_file, status_file, resumo_file]:
        # Copia para backend/dados
        dest_dir = Path("backend") / "dados"
        os.makedirs(dest_dir, exist_ok=True)
        dest_file = dest_dir / src_file.name
        shutil.copy2(src_file, dest_file)
        logger.info(f"Arquivo copiado para: {dest_file}")
    
    logger.info("✅ Geração de dados unificados concluída com sucesso!")
    return True

if __name__ == "__main__":
    generate_unified_data()
