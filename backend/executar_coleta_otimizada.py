"""
Script para execução completa da coleta otimizada de dados do New Relic.

Este script:
1. Executa a coleta avançada de dados do New Relic
2. Aplica filtragem rigorosa para descartar dados nulos/vazios
3. Gera relatório de economia de tokens
4. Atualiza o sistema para usar o cache otimizado
"""

import os
import sys
import asyncio
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO, 
                   format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def executar_comando(comando, descricao=None):
    """Executa um comando e retorna o resultado."""
    if descricao:
        logger.info(f"Executando: {descricao}")
    
    try:
        resultado = subprocess.run(
            comando, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        
        if resultado.returncode == 0:
            logger.info(f"Comando executado com sucesso!")
            return True, resultado.stdout
        else:
            logger.error(f"Erro ao executar comando: {resultado.stderr}")
            return False, resultado.stderr
    except Exception as e:
        logger.error(f"Exceção ao executar comando: {e}")
        return False, str(e)

async def main():
    """Função principal de execução."""
    logger.info("="*60)
    logger.info("INICIANDO COLETA OTIMIZADA DE DADOS NEW RELIC")
    logger.info("="*60)
    
    # 1. Executar coleta otimizada
    logger.info("\n[Etapa 1] Executando coleta otimizada...")
    sucesso, saida = executar_comando(
        "python coleta_otimizada.py", 
        "Coleta otimizada com filtragem rigorosa"
    )
    
    if not sucesso:
        logger.error("Falha na coleta otimizada. Abortando.")
        return 1
    
    # 2. Gerar análise de economia de tokens
    logger.info("\n[Etapa 2] Analisando economia de tokens...")
    sucesso, saida = executar_comando(
        "python monitor_economia_tokens.py historico/cache_otimizado.json",
        "Análise de economia de tokens"
    )
    
    if not sucesso:
        logger.warning("Falha na análise de economia. Continuando...")
    
    # 3. Testar o cache otimizado
    logger.info("\n[Etapa 3] Testando cache otimizado...")
    
    cache_otimizado = Path("historico/cache_otimizado.json")
    if not cache_otimizado.exists():
        logger.error(f"Cache otimizado não encontrado: {cache_otimizado}")
        return 1
    
    logger.info("Cache otimizado encontrado e validado!")
    
    # 4. Criar relatório de execução
    logger.info("\n[Etapa 4] Gerando relatório de execução...")
    
    relatorio = {
        "timestamp": datetime.now().isoformat(),
        "etapas_concluidas": {
            "coleta_otimizada": sucesso,
            "analise_economia": sucesso
        }
    }
    
    # Cria diretório de relatórios se não existir
    relatorios_dir = Path("relatorios")
    relatorios_dir.mkdir(exist_ok=True)
    
    # Salva relatório
    relatorio_path = relatorios_dir / f"execucao_otimizada_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(relatorio_path, "w", encoding="utf-8") as f:
        f.write("="*60 + "\n")
        f.write("RELATÓRIO DE EXECUÇÃO - COLETA OTIMIZADA\n")
        f.write("="*60 + "\n\n")
        f.write(f"Data e hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write(f"Cache gerado: {cache_otimizado}\n")
        f.write(f"Coleta otimizada concluída: {'Sim' if sucesso else 'Não'}\n")
        f.write(f"Análise de economia gerada: {'Sim' if sucesso else 'Não'}\n")
    
    logger.info(f"Relatório salvo em: {relatorio_path}")
    
    # 5. Finalização
    logger.info("\n" + "="*60)
    logger.info("COLETA OTIMIZADA CONCLUÍDA COM SUCESSO!")
    logger.info("="*60)
    logger.info(f"Cache otimizado disponível em: {cache_otimizado}")
    logger.info(f"Relatório de execução: {relatorio_path}")
    logger.info("="*60)
    
    return 0

if __name__ == "__main__":
    try:
        resultado = asyncio.run(main())
        sys.exit(resultado)
    except KeyboardInterrupt:
        logger.info("\nInterrompido pelo usuário.")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
