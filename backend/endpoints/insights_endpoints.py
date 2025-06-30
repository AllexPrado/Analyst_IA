from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import random
from pathlib import Path

# Configuração do logger
logger = logging.getLogger(__name__)

# Criar o router
router = APIRouter()

# Dados simulados para desenvolvimento - serão substituídos por dados reais
def generate_sample_insights_data():
    """Gera dados de insights para desenvolvimento"""
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
        ],
        "oportunidades": [
            {
                "nome": "Migração para serverless",
                "descricao": "Migrar serviços de baixo uso para arquitetura serverless",
                "potencialEconomia": round(random.uniform(15000, 30000)),
                "esforco": 7,
                "status": "Em análise",
                "impacto": 8
            },
            {
                "nome": "Otimização de custos de storage",
                "descricao": "Implementar políticas de lifecycle para dados antigos",
                "potencialEconomia": round(random.uniform(5000, 15000)),
                "esforco": 3,
                "status": "Implementado",
                "impacto": 6
            },
            {
                "nome": "Consolidação de serviços redundantes",
                "descricao": "Unificar serviços que executam funções similares",
                "potencialEconomia": round(random.uniform(20000, 40000)),
                "esforco": 8,
                "status": "Não iniciado",
                "impacto": 9
            }
        ],
        "projetos": {
            "em_andamento": [
                {
                    "nome": "Migração para Kubernetes",
                    "progresso": 65,
                    "status": "No prazo",
                    "economia_projetada": 32000
                },
                {
                    "nome": "Implementação de observabilidade avançada",
                    "progresso": 80,
                    "status": "No prazo",
                    "economia_projetada": 15000
                }
            ],
            "concluidos": [
                {
                    "nome": "Otimização de performance de APIs",
                    "data_conclusao": "2025-05-15",
                    "economia_realizada": 18500
                },
                {
                    "nome": "Consolidação de bases de dados",
                    "data_conclusao": "2025-04-02",
                    "economia_realizada": 22000
                }
            ],
            "planejados": [
                {
                    "nome": "Migração para arquitetura de microserviços",
                    "inicio_previsto": "2025-08-10",
                    "economia_estimada": 45000
                }
            ]
        }
    }

# Endpoint para insights
@router.get("/insights")
async def get_insights():
    try:
        # Lista de possíveis localizações para o arquivo de insights
        possible_paths = [
            "dados/insights.json",               # Relativo ao diretório atual
            "backend/dados/insights.json",       # Relativo ao diretório raiz
            "../dados/insights.json",            # Um nível acima (se estamos em backend)
            "../backend/dados/insights.json"     # Um nível acima, então em backend
        ]
        
        # Tentar cada caminho
        for insights_path in possible_paths:
            if os.path.exists(insights_path):
                try:
                    with open(insights_path, 'r', encoding='utf-8') as file:
                        insights_data = json.load(file)
                        logger.info(f"Dados de insights carregados do arquivo: {insights_path}")
                        return insights_data
                except Exception as e:
                    logger.error(f"Erro ao ler dados de insights do arquivo {insights_path}: {e}")
        
        # Se não encontrou em nenhum lugar, procurar em qualquer lugar usando Path.glob
        root_dir = Path('.').resolve()
        for data_file in root_dir.glob('**/dados/insights.json'):
            try:
                with open(data_file, 'r', encoding='utf-8') as file:
                    insights_data = json.load(file)
                    logger.info(f"Dados de insights carregados do arquivo (busca global): {data_file}")
                    return insights_data
            except Exception as e:
                logger.error(f"Erro ao ler dados de insights do arquivo {data_file}: {e}")
        
        # Se não houver arquivo ou houver erro, gerar dados simulados
        logger.warning("Nenhum arquivo de dados de insights encontrado. Gerando dados simulados.")
        insights_data = generate_sample_insights_data()
        
        # Salvar os dados gerados para uso futuro
        os.makedirs("dados", exist_ok=True)
        with open(insights_path, 'w') as file:
            json.dump(insights_data, file)
        
        logger.info("Dados de insights gerados e salvos")
        return insights_data
    except Exception as e:
        logger.error(f"Erro ao processar request de insights: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar insights: {str(e)}")

# Outros endpoints podem ser adicionados aqui
