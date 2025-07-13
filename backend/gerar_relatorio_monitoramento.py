"""
Script para gerar relatórios baseados nos dados do monitoramento local.
Este script analisa os dados coletados e gera um relatório resumido.
"""

import os
import sys
import json
import csv
from datetime import datetime, timedelta
import argparse
import matplotlib.pyplot as plt
from tabulate import tabulate

# Adicionar o diretório pai ao PATH para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Diretório onde os dados de monitoramento são salvos
MONITOR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monitoramento_local")
HISTORY_DIR = os.path.join(MONITOR_DIR, "historico")
REPORT_DIR = os.path.join(MONITOR_DIR, "relatorios")

def carregar_dados_recentes(dias=1):
    """Carrega dados de monitoramento dos últimos X dias"""
    dados = []
    
    # Verificar arquivo CSV de métricas
    csv_path = os.path.join(MONITOR_DIR, "metricas.csv")
    if os.path.exists(csv_path):
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Converter string de timestamp para objeto datetime
                    try:
                        timestamp = datetime.fromisoformat(row["timestamp"])
                        if datetime.now() - timestamp <= timedelta(days=dias):
                            dados.append(row)
                    except (ValueError, KeyError):
                        # Ignorar linhas com formato incorreto
                        pass
        except Exception as e:
            print(f"Erro ao ler arquivo CSV: {e}")
    
    # Se não tiver dados do CSV, tentar carregar dos arquivos JSON
    if not dados:
        try:
            # Procurar arquivos JSON no diretório de histórico
            for filename in os.listdir(HISTORY_DIR):
                if filename.endswith(".json"):
                    file_path = os.path.join(HISTORY_DIR, filename)
                    
                    # Verificar se o arquivo é recente
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if datetime.now() - file_time <= timedelta(days=dias):
                        try:
                            with open(file_path, 'r') as f:
                                dados.append(json.load(f))
                        except:
                            # Ignorar arquivos com formato incorreto
                            pass
        except Exception as e:
            print(f"Erro ao buscar arquivos de histórico: {e}")
    
    return dados

def calcular_estatisticas(dados):
    """Calcula estatísticas básicas dos dados de monitoramento"""
    if not dados:
        return {
            "periodo": {
                "inicio": None,
                "fim": None,
                "registros": 0
            },
            "sistema": {
                "cpu_medio": 0,
                "memoria_media": 0,
                "disco_medio": 0
            },
            "servicos": {
                "total": 0,
                "disponiveis": 0,
                "indisponiveis": 0,
                "tempo_resposta_medio": 0,
                "detalhes": []
            }
        }
    
    # Estatísticas do sistema
    cpu_valores = []
    memoria_valores = []
    disco_valores = []
    
    # Estatísticas de serviços
    servicos_status = {}
    servicos_tempo = {}
    
    # Período
    timestamps = []
    
    for item in dados:
        # Processar CSV ou JSON dependendo do formato
        if "timestamp" in item and "cpu_percent" in item:
            # Formato CSV
            timestamps.append(datetime.fromisoformat(item["timestamp"]))
            cpu_valores.append(float(item.get("cpu_percent", 0)))
            memoria_valores.append(float(item.get("memory_percent", 0)))
            disco_valores.append(float(item.get("disk_percent", 0)))
            
            # Processar status dos serviços
            for key, value in item.items():
                if key.startswith("service_"):
                    service_name = key[8:].replace('_', ' ')  # Remover "service_" e substituir _ por espaço
                    if service_name not in servicos_status:
                        servicos_status[service_name] = {"ok": 0, "error": 0}
                    
                    if value == "1" or value == 1:
                        servicos_status[service_name]["ok"] += 1
                    else:
                        servicos_status[service_name]["error"] += 1
        
        elif isinstance(item, dict) and "timestamp" in item and "system" in item:
            # Formato JSON
            timestamps.append(datetime.fromisoformat(item["timestamp"]))
            
            # Sistema
            try:
                cpu_valores.append(item["system"]["cpu"]["percent"])
                memoria_valores.append(item["system"]["memory"]["percent"])
                disco_valores.append(item["system"]["disk"]["percent"])
            except (KeyError, TypeError):
                pass
            
            # Serviços
            try:
                for service in item["services"]:
                    name = service["name"]
                    if name not in servicos_status:
                        servicos_status[name] = {"ok": 0, "error": 0}
                    
                    status = service["result"]["status"]
                    if status == "ok":
                        servicos_status[name]["ok"] += 1
                        
                        # Registrar tempo de resposta
                        if "response_time" in service["result"]:
                            if name not in servicos_tempo:
                                servicos_tempo[name] = []
                            servicos_tempo[name].append(service["result"]["response_time"])
                    else:
                        servicos_status[name]["error"] += 1
            except (KeyError, TypeError):
                pass
    
    # Calcular estatísticas finais
    cpu_medio = sum(cpu_valores) / len(cpu_valores) if cpu_valores else 0
    memoria_media = sum(memoria_valores) / len(memoria_valores) if memoria_valores else 0
    disco_medio = sum(disco_valores) / len(disco_valores) if disco_valores else 0
    
    # Estatísticas de serviços
    servicos_detalhes = []
    servicos_disponiveis = 0
    servicos_indisponiveis = 0
    
    for name, stats in servicos_status.items():
        total = stats["ok"] + stats["error"]
        disponibilidade = stats["ok"] / total if total > 0 else 0
        
        if disponibilidade >= 0.9:  # Considerando disponível se uptime >= 90%
            servicos_disponiveis += 1
        else:
            servicos_indisponiveis += 1
        
        tempo_medio = 0
        if name in servicos_tempo and servicos_tempo[name]:
            tempo_medio = sum(servicos_tempo[name]) / len(servicos_tempo[name])
        
        servicos_detalhes.append({
            "nome": name,
            "disponibilidade": disponibilidade * 100,
            "tempo_resposta_medio": tempo_medio,
            "checagens_total": total,
            "checagens_ok": stats["ok"],
            "checagens_erro": stats["error"]
        })
    
    # Tempo médio de resposta global
    todos_tempos = []
    for tempos in servicos_tempo.values():
        todos_tempos.extend(tempos)
    
    tempo_resposta_medio = sum(todos_tempos) / len(todos_tempos) if todos_tempos else 0
    
    # Organizar resultado
    return {
        "periodo": {
            "inicio": min(timestamps) if timestamps else None,
            "fim": max(timestamps) if timestamps else None,
            "registros": len(dados)
        },
        "sistema": {
            "cpu_medio": cpu_medio,
            "memoria_media": memoria_media,
            "disco_medio": disco_medio
        },
        "servicos": {
            "total": len(servicos_status),
            "disponiveis": servicos_disponiveis,
            "indisponiveis": servicos_indisponiveis,
            "tempo_resposta_medio": tempo_resposta_medio,
            "detalhes": servicos_detalhes
        }
    }

def gerar_graficos(dados, estatisticas, output_dir):
    """Gera gráficos baseados nos dados coletados"""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        from matplotlib.dates import DateFormatter
        
        # Criar diretório para gráficos se não existir
        os.makedirs(output_dir, exist_ok=True)
        
        # Preparar dados para gráficos
        timestamps = []
        cpu_values = []
        memory_values = []
        disk_values = []
        
        for item in dados:
            try:
                if "timestamp" in item and "cpu_percent" in item:
                    # Formato CSV
                    timestamps.append(datetime.fromisoformat(item["timestamp"]))
                    cpu_values.append(float(item.get("cpu_percent", 0)))
                    memory_values.append(float(item.get("memory_percent", 0)))
                    disk_values.append(float(item.get("disk_percent", 0)))
                elif isinstance(item, dict) and "timestamp" in item and "system" in item:
                    # Formato JSON
                    timestamps.append(datetime.fromisoformat(item["timestamp"]))
                    cpu_values.append(item["system"]["cpu"]["percent"])
                    memory_values.append(item["system"]["memory"]["percent"])
                    disk_values.append(item["system"]["disk"]["percent"])
            except (ValueError, KeyError, TypeError):
                pass
        
        if not timestamps:
            print("Sem dados suficientes para gerar gráficos")
            return
        
        # Ordenar por timestamp
        sorted_data = sorted(zip(timestamps, cpu_values, memory_values, disk_values))
        timestamps = [x[0] for x in sorted_data]
        cpu_values = [x[1] for x in sorted_data]
        memory_values = [x[2] for x in sorted_data]
        disk_values = [x[3] for x in sorted_data]
        
        # 1. Gráfico de uso de recursos
        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, cpu_values, 'r-', label='CPU (%)')
        plt.plot(timestamps, memory_values, 'b-', label='Memória (%)')
        plt.plot(timestamps, disk_values, 'g-', label='Disco (%)')
        plt.title('Uso de Recursos do Sistema')
        plt.xlabel('Data/Hora')
        plt.ylabel('Utilização (%)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'recursos_sistema.png'))
        plt.close()
        
        # 2. Gráfico de disponibilidade de serviços
        servicos = estatisticas["servicos"]["detalhes"]
        if servicos:
            nomes = [s["nome"] for s in servicos]
            disponibilidade = [s["disponibilidade"] for s in servicos]
            
            plt.figure(figsize=(10, 6))
            bars = plt.bar(nomes, disponibilidade)
            plt.title('Disponibilidade dos Serviços')
            plt.xlabel('Serviço')
            plt.ylabel('Disponibilidade (%)')
            plt.axhline(y=99.9, color='r', linestyle='-', alpha=0.3, label='SLA 99.9%')
            plt.grid(True, axis='y', linestyle='--', alpha=0.7)
            plt.xticks(rotation=45)
            
            # Colorir barras baseado na disponibilidade
            for i, bar in enumerate(bars):
                if disponibilidade[i] >= 99.9:
                    bar.set_color('green')
                elif disponibilidade[i] >= 95:
                    bar.set_color('yellow')
                else:
                    bar.set_color('red')
            
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'disponibilidade_servicos.png'))
            plt.close()
            
            # 3. Gráfico de tempo de resposta
            tempos = [s["tempo_resposta_medio"] for s in servicos if s["tempo_resposta_medio"] > 0]
            nomes = [s["nome"] for s in servicos if s["tempo_resposta_medio"] > 0]
            
            if tempos:
                plt.figure(figsize=(10, 6))
                plt.bar(nomes, tempos)
                plt.title('Tempo Médio de Resposta')
                plt.xlabel('Serviço')
                plt.ylabel('Tempo (segundos)')
                plt.grid(True, axis='y', linestyle='--', alpha=0.7)
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.savefig(os.path.join(output_dir, 'tempo_resposta.png'))
                plt.close()
        
        print(f"Gráficos gerados com sucesso em {output_dir}")
        return True
    except Exception as e:
        print(f"Erro ao gerar gráficos: {e}")
        return False

def gerar_relatorio_html(estatisticas, output_file, graficos_dir):
    """Gera um relatório HTML com as estatísticas e gráficos"""
    try:
        # Criar diretório para relatórios se não existir
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        periodo_inicio = estatisticas["periodo"]["inicio"].strftime("%d/%m/%Y %H:%M") if estatisticas["periodo"]["inicio"] else "N/A"
        periodo_fim = estatisticas["periodo"]["fim"].strftime("%d/%m/%Y %H:%M") if estatisticas["periodo"]["fim"] else "N/A"
        
        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Monitoramento - Analyst_IA</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #2980b9;
            margin-top: 20px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px 15px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .card {{
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
            background-color: #fff;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .metric {{
            display: inline-block;
            padding: 15px;
            margin: 10px;
            text-align: center;
            border-radius: 8px;
            background-color: #f8f9fa;
            min-width: 150px;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            margin: 10px 0;
            color: #2c3e50;
        }}
        .metric-label {{
            font-size: 14px;
            color: #7f8c8d;
        }}
        .ok {{
            color: green;
        }}
        .warning {{
            color: orange;
        }}
        .error {{
            color: red;
        }}
        .graphs {{
            display: flex;
            flex-wrap: wrap;
            justify-content: space-around;
        }}
        .graph-container {{
            margin: 15px;
            text-align: center;
        }}
        .graph-container img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        footer {{
            margin-top: 30px;
            text-align: center;
            font-size: 12px;
            color: #7f8c8d;
            border-top: 1px solid #eee;
            padding-top: 10px;
        }}
    </style>
</head>
<body>
    <h1>Relatório de Monitoramento - Analyst_IA</h1>
    <p>Relatório gerado em {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</p>
    
    <div class="card">
        <h2>Período do Relatório</h2>
        <p><strong>Início:</strong> {periodo_inicio}</p>
        <p><strong>Fim:</strong> {periodo_fim}</p>
        <p><strong>Total de Registros:</strong> {estatisticas["periodo"]["registros"]}</p>
    </div>
    
    <div class="card">
        <h2>Métricas do Sistema</h2>
        <div>
            <div class="metric">
                <div class="metric-label">Uso Médio de CPU</div>
                <div class="metric-value {cpu_class(estatisticas["sistema"]["cpu_medio"])}">{estatisticas["sistema"]["cpu_medio"]:.1f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Uso Médio de Memória</div>
                <div class="metric-value {memory_class(estatisticas["sistema"]["memoria_media"])}">{estatisticas["sistema"]["memoria_media"]:.1f}%</div>
            </div>
            <div class="metric">
                <div class="metric-label">Uso Médio de Disco</div>
                <div class="metric-value {disk_class(estatisticas["sistema"]["disco_medio"])}">{estatisticas["sistema"]["disco_medio"]:.1f}%</div>
            </div>
        </div>
    </div>
    
    <div class="card">
        <h2>Status dos Serviços</h2>
        <div>
            <div class="metric">
                <div class="metric-label">Total de Serviços</div>
                <div class="metric-value">{estatisticas["servicos"]["total"]}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Serviços Disponíveis</div>
                <div class="metric-value ok">{estatisticas["servicos"]["disponiveis"]}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Serviços Indisponíveis</div>
                <div class="metric-value {error_class(estatisticas["servicos"]["indisponiveis"])}">{estatisticas["servicos"]["indisponiveis"]}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Tempo Médio de Resposta</div>
                <div class="metric-value">{estatisticas["servicos"]["tempo_resposta_medio"]:.3f}s</div>
            </div>
        </div>
        
        <h3>Detalhes dos Serviços</h3>
        <table>
            <tr>
                <th>Serviço</th>
                <th>Disponibilidade</th>
                <th>Tempo Médio de Resposta</th>
                <th>Total de Verificações</th>
                <th>Verificações OK</th>
                <th>Verificações com Erro</th>
            </tr>
            {gerar_linhas_tabela_servicos(estatisticas["servicos"]["detalhes"])}
        </table>
    </div>
    
    <div class="card">
        <h2>Gráficos</h2>
        <div class="graphs">
            <div class="graph-container">
                <h3>Uso de Recursos</h3>
                <img src="recursos_sistema.png" alt="Gráfico de uso de recursos">
            </div>
            <div class="graph-container">
                <h3>Disponibilidade dos Serviços</h3>
                <img src="disponibilidade_servicos.png" alt="Gráfico de disponibilidade">
            </div>
            <div class="graph-container">
                <h3>Tempo de Resposta</h3>
                <img src="tempo_resposta.png" alt="Gráfico de tempo de resposta">
            </div>
        </div>
    </div>
    
    <footer>
        <p>Gerado pelo sistema de monitoramento local Analyst_IA</p>
        <p>Sistema de monitoramento alternativo ao New Relic</p>
    </footer>
</body>
</html>"""
        
        with open(output_file, 'w') as f:
            f.write(html)
        
        print(f"Relatório HTML gerado com sucesso: {output_file}")
        return True
    except Exception as e:
        print(f"Erro ao gerar relatório HTML: {e}")
        return False

def cpu_class(valor):
    return "ok" if valor < 70 else "warning" if valor < 90 else "error"

def memory_class(valor):
    return "ok" if valor < 70 else "warning" if valor < 90 else "error"

def disk_class(valor):
    return "ok" if valor < 75 else "warning" if valor < 85 else "error"

def error_class(valor):
    return "ok" if valor == 0 else "warning" if valor == 1 else "error"

def gerar_linhas_tabela_servicos(servicos):
    """Gera as linhas da tabela de serviços no HTML"""
    linhas = ""
    for servico in servicos:
        disponibilidade_class = "ok" if servico["disponibilidade"] >= 99.0 else "warning" if servico["disponibilidade"] >= 90.0 else "error"
        
        linhas += f"""
            <tr>
                <td>{servico["nome"]}</td>
                <td class="{disponibilidade_class}">{servico["disponibilidade"]:.2f}%</td>
                <td>{servico["tempo_resposta_medio"]:.3f}s</td>
                <td>{servico["checagens_total"]}</td>
                <td>{servico["checagens_ok"]}</td>
                <td>{servico["checagens_erro"]}</td>
            </tr>"""
    
    return linhas

def main():
    parser = argparse.ArgumentParser(description="Gerador de relatórios de monitoramento local")
    parser.add_argument("--dias", type=int, default=1, help="Número de dias a considerar no relatório")
    parser.add_argument("--output", type=str, default="", help="Diretório para salvar o relatório")
    args = parser.parse_args()
    
    print("Gerando relatório de monitoramento local...")
    print(f"Considerando dados dos últimos {args.dias} dias")
    
    # Diretório para salvar relatórios
    if args.output:
        report_dir = args.output
    else:
        report_dir = REPORT_DIR
    
    os.makedirs(report_dir, exist_ok=True)
    
    # Carregar dados
    dados = carregar_dados_recentes(args.dias)
    print(f"Dados carregados: {len(dados)} registros")
    
    if not dados:
        print("Sem dados para gerar relatório. Execute o monitoramento primeiro.")
        return False
    
    # Calcular estatísticas
    estatisticas = calcular_estatisticas(dados)
    print("Estatísticas calculadas")
    
    # Gerar gráficos
    gerar_graficos(dados, estatisticas, report_dir)
    
    # Gerar relatório
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(report_dir, f"relatorio_{timestamp}.html")
    gerar_relatorio_html(estatisticas, report_file, report_dir)
    
    print(f"\nRelatório gerado com sucesso!")
    print(f"Arquivo: {report_file}")
    
    return True

if __name__ == "__main__":
    try:
        import matplotlib
        import numpy
        import tabulate
    except ImportError:
        print("Instalando dependências necessárias...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib", "numpy", "tabulate"])
    
    main()
