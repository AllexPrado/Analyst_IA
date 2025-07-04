"""
Script para manutenção e limpeza do projeto Analyst_IA
Este script remove arquivos de log antigos e desnecessários, 
limpa o cache histórico e reorganiza o projeto para melhorar
a performance e reduzir o tamanho do projeto.
"""
import os
import sys
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def limpar_logs(dias_a_manter=7):
    """
    Limpa arquivos de log mais antigos que o número de dias especificado.
    Usa pathlib para maior robustez e busca recursiva em subdiretórios de logs.
    """
    logger.info("\n==============================")
    logger.info(f"🧹 Limpando logs mais antigos que {dias_a_manter} dias...")
    pastas_logs = [
        Path("logs"),
        Path("backend/logs"),
        Path("frontend/logs"),
        Path(".")  # Raiz do projeto
    ]
    data_corte = datetime.now() - timedelta(days=dias_a_manter)
    total_removidos = 0
    tamanho_liberado = 0
    for pasta in pastas_logs:
        if not pasta.exists():
            continue
        logger.info(f"🔎 Verificando logs em '{pasta}'...")
        # Busca recursiva por arquivos de log
        for caminho_arquivo in pasta.rglob("*"):
            if caminho_arquivo.is_file() and (caminho_arquivo.suffix == ".log" or "log" in caminho_arquivo.name.lower()):
                data_mod = datetime.fromtimestamp(caminho_arquivo.stat().st_mtime)
                if data_mod < data_corte:
                    try:
                        tamanho = caminho_arquivo.stat().st_size
                        caminho_arquivo.unlink()
                        total_removidos += 1
                        tamanho_liberado += tamanho
                        logger.info(f"🗑️ Removido: {caminho_arquivo} ({tamanho / (1024*1024):.2f} MB)")
                    except Exception as e:
                        logger.error(f"❌ Erro ao remover {caminho_arquivo}: {str(e)}")
                else:
                    tamanho = caminho_arquivo.stat().st_size
                    if tamanho > 50 * 1024 * 1024:  # 50MB
                        try:
                            with caminho_arquivo.open('r+', encoding='utf-8', errors='ignore') as f:
                                conteudo = f.readlines()
                                # Truncar mantendo as últimas 1000 linhas
                                ultimas_linhas = conteudo[-1000:] if len(conteudo) > 1000 else conteudo
                                f.seek(0)
                                f.truncate()
                                f.writelines(ultimas_linhas)
                                f.flush()
                            novo_tamanho = caminho_arquivo.stat().st_size
                            tamanho_liberado += (tamanho - novo_tamanho)
                            logger.info(f"✂️ Truncado: {caminho_arquivo} de {tamanho / (1024*1024):.2f} MB para {novo_tamanho / (1024*1024):.2f} MB (mantidas as últimas {len(ultimas_linhas)} linhas)")
                        except Exception as e:
                            logger.error(f"❌ Erro ao truncar {caminho_arquivo}: {str(e)}")
    logger.info(f"✅ Limpeza de logs concluída. Removidos {total_removidos} arquivos, liberando {tamanho_liberado / (1024*1024):.2f} MB")
    logger.info("==============================\n")
    return total_removidos, tamanho_liberado

def limpar_historico_consultas(max_consultas=100):
    """Limpa o histórico de consultas mantendo apenas as mais recentes"""
    logger.info(f"Limpando histórico de consultas (mantendo as {max_consultas} mais recentes)...")
    
    pasta_historico = "backend/historico/consultas"
    if not os.path.exists(pasta_historico):
        logger.info(f"Pasta {pasta_historico} não encontrada. Pulando.")
        return 0, 0
    
    # Listar arquivos de consulta
    arquivos = []
    for arquivo in os.listdir(pasta_historico):
        caminho = os.path.join(pasta_historico, arquivo)
        if os.path.isfile(caminho) and "consulta_" in arquivo:
            data_mod = datetime.fromtimestamp(os.path.getmtime(caminho))
            tamanho = os.path.getsize(caminho)
            arquivos.append((caminho, data_mod, tamanho))
    
    # Ordenar por data (mais recentes primeiro)
    arquivos.sort(key=lambda x: x[1], reverse=True)
    
    # Manter apenas os mais recentes
    arquivos_a_remover = arquivos[max_consultas:]
    total_removidos = 0
    tamanho_liberado = 0
    
    for caminho, data, tamanho in arquivos_a_remover:
        try:
            os.remove(caminho)
            total_removidos += 1
            tamanho_liberado += tamanho
            logger.info(f"Removido: {caminho} ({tamanho / (1024*1024):.2f} MB)")
        except Exception as e:
            logger.error(f"Erro ao remover {caminho}: {str(e)}")
    
    logger.info(f"✅ Limpeza de histórico concluída. Removidos {total_removidos} arquivos, liberando {tamanho_liberado / (1024*1024):.2f} MB")
    return total_removidos, tamanho_liberado

def limpar_caches_antigos(max_caches=10):
    """Limpa caches antigos mantendo apenas os mais recentes"""
    logger.info(f"Limpando caches antigos (mantendo os {max_caches} mais recentes)...")
    
    pasta_cache = "backend/historico"
    if not os.path.exists(pasta_cache):
        logger.info(f"Pasta {pasta_cache} não encontrada. Pulando.")
        return 0, 0
    
    # Listar arquivos de cache
    arquivos = []
    for arquivo in os.listdir(pasta_cache):
        caminho = os.path.join(pasta_cache, arquivo)
        if os.path.isfile(caminho) and "cache" in arquivo.lower() and arquivo.endswith(".json"):
            data_mod = datetime.fromtimestamp(os.path.getmtime(caminho))
            tamanho = os.path.getsize(caminho)
            arquivos.append((caminho, data_mod, tamanho))
    
    # Ordenar por data (mais recentes primeiro)
    arquivos.sort(key=lambda x: x[1], reverse=True)
    
    # Manter apenas os mais recentes
    arquivos_a_remover = arquivos[max_caches:]
    total_removidos = 0
    tamanho_liberado = 0
    
    for caminho, data, tamanho in arquivos_a_remover:
        try:
            os.remove(caminho)
            total_removidos += 1
            tamanho_liberado += tamanho
            logger.info(f"Removido: {caminho} ({tamanho / (1024*1024):.2f} MB)")
        except Exception as e:
            logger.error(f"Erro ao remover {caminho}: {str(e)}")
    
    logger.info(f"✅ Limpeza de caches concluída. Removidos {total_removidos} arquivos, liberando {tamanho_liberado / (1024*1024):.2f} MB")
    return total_removidos, tamanho_liberado

def configurar_para_dados_reais():
    """Configura o sistema para usar dados reais do New Relic"""
    logger.info("Configurando sistema para usar dados reais...")
    
    # Atualizar arquivo .env
    env_path = ".env"
    if os.path.exists(env_path):
        try:
            with open(env_path, "r") as f:
                linhas = f.readlines()
                
            with open(env_path, "w") as f:
                for linha in linhas:
                    if linha.startswith("USE_SIMULATED_DATA="):
                        f.write("USE_SIMULATED_DATA=false\n")
                    else:
                        f.write(linha)
            
            logger.info("✅ Arquivo .env atualizado para usar dados reais")
        except Exception as e:
            logger.error(f"Erro ao atualizar arquivo .env: {str(e)}")
    
    # Atualizar indicador de dados reais
    indicador_path = "backend/cache/data_source_indicator.json"
    try:
        indicador = {
            "using_real_data": True,
            "timestamp": datetime.now().isoformat(),
            "source": "New Relic API",
            "configured_by": "script_manutencao.py"
        }
        
        # Garantir que a pasta existe
        os.makedirs(os.path.dirname(indicador_path), exist_ok=True)
        
        with open(indicador_path, "w") as f:
            json.dump(indicador, f, indent=2)
        
        logger.info(f"✅ Indicador de dados reais atualizado em {indicador_path}")
    except Exception as e:
        logger.error(f"Erro ao criar indicador de dados reais: {str(e)}")

def consolidar_scripts_teste():
    """Consolidar scripts de teste em uma pasta dedicada para organização"""
    logger.info("Consolidando scripts de teste...")
    
    pasta_testes = "tests"
    os.makedirs(pasta_testes, exist_ok=True)
    
    # Padrões para identificar scripts de teste
    padroes_teste = ["test_", "testar_", "verificar_"]
    
    # Arquivos a ignorar
    ignorar = ["test_newrelic_connection.py", "verificar_conexao_newrelic.py", "test_cache.py"]
    
    total_movidos = 0
    
    for arquivo in os.listdir("."):
        if os.path.isfile(arquivo) and arquivo.endswith(".py"):
            for padrao in padroes_teste:
                if padrao in arquivo.lower() and arquivo not in ignorar:
                    try:
                        destino = os.path.join(pasta_testes, arquivo)
                        # Só move se ainda não existe na pasta de testes
                        if not os.path.exists(destino):
                            shutil.move(arquivo, destino)
                            total_movidos += 1
                            logger.info(f"Movido: {arquivo} -> {destino}")
                    except Exception as e:
                        logger.error(f"Erro ao mover {arquivo}: {str(e)}")
                    break  # Sai do loop se encontrou um padrão
    
    logger.info(f"✅ Consolidação de scripts de teste concluída. Movidos {total_movidos} arquivos para a pasta {pasta_testes}")
    return total_movidos

def main():
    """Função principal"""
    logger.info("="*50)
    logger.info("Script de manutenção e limpeza do Analyst_IA")
    logger.info("="*50)
    
    # Limpar logs
    total_logs, tamanho_logs = limpar_logs()
    
    # Limpar histórico de consultas
    total_consultas, tamanho_consultas = limpar_historico_consultas()
    
    # Limpar caches antigos
    total_caches, tamanho_caches = limpar_caches_antigos()
    
    # Consolidar scripts de teste
    total_scripts = consolidar_scripts_teste()
    
    # Configurar para dados reais
    configurar_para_dados_reais()
    
    # Resumo
    logger.info("="*50)
    logger.info("Resumo da manutenção:")
    logger.info(f"- Logs removidos: {total_logs} ({tamanho_logs / (1024*1024):.2f} MB)")
    logger.info(f"- Histórico de consultas removido: {total_consultas} ({tamanho_consultas / (1024*1024):.2f} MB)")
    logger.info(f"- Caches antigos removidos: {total_caches} ({tamanho_caches / (1024*1024):.2f} MB)")
    logger.info(f"- Scripts de teste consolidados: {total_scripts}")
    logger.info(f"- Total de espaço liberado: {(tamanho_logs + tamanho_consultas + tamanho_caches) / (1024*1024):.2f} MB")
    logger.info("="*50)
    logger.info("✅ Manutenção concluída!")
    logger.info("="*50)

if __name__ == "__main__":
    main()
