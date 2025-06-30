"""
Script para forçar a atualização do cache com dados reais do New Relic.
Este script limpa qualquer dados de demonstração ou simulado e força
a coleta de dados reais do New Relic.
"""

import os
import sys
import json
import asyncio
import logging
import shutil
from pathlib import Path
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Adiciona diretório atual ao path para importar os módulos necessários
script_dir = Path(__file__).parent
sys.path.append(str(script_dir))

try:
    from atualizar_cache_completo import atualizar_cache_completo
    from utils.entity_processor import filter_entities_with_data
except ImportError as e:
    logger.error(f"Erro ao importar módulos necessários: {e}")
    sys.exit(1)

# Configurações
CACHE_DIR = script_dir / "historico"
CACHE_FILE = CACHE_DIR / "cache_completo.json"
DADOS_DIR = script_dir / "dados"

async def force_real_data_update():
    """
    Força a atualização do cache com apenas dados reais do New Relic
    """
    try:
        logger.info("=" * 80)
        logger.info("INICIANDO PROCESSO DE LIMPEZA E FORÇANDO DADOS REAIS")
        logger.info("=" * 80)
        
        # 1. Verificar e fazer backup de arquivos existentes
        if CACHE_FILE.exists():
            backup_path = CACHE_FILE.with_suffix('.json.bak')
            shutil.copy2(CACHE_FILE, backup_path)
            logger.info(f"Backup do cache criado: {backup_path}")
        
        # 2. Remover dados de demonstração da pasta "dados"
        if DADOS_DIR.exists():
            demo_files = [
                'kpis.json', 'insights.json', 'cobertura.json', 
                'tendencias.json', 'resumo-geral.json', 'status.json',
                'entidades.json'
            ]
            
            for demo_file in demo_files:
                demo_path = DADOS_DIR / demo_file
                if demo_path.exists():
                    demo_path.unlink()
                    logger.info(f"Arquivo de dados de demonstração removido: {demo_path}")
        else:
            DADOS_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"Diretório de dados criado: {DADOS_DIR}")
        
        # 3. Forçar atualização do cache com dados reais
        logger.info("Forçando atualização do cache com dados reais do New Relic...")
        result = await atualizar_cache_completo()
        
        if not result:
            logger.error("Falha na atualização do cache!")
            return False
        
        # 4. Verificar se o cache foi atualizado com dados reais
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                entidades = cache_data.get("entidades", [])
                logger.info(f"Cache atualizado com {len(entidades)} entidades")
                
                # Verificar se há dados reais
                if len(entidades) == 0:
                    logger.error("ALERTA: O cache não contém nenhuma entidade!")
                    return False
                
                # Aplicar novamente filtro rigoroso para garantir apenas dados de qualidade
                filtered_entities = filter_entities_with_data(entidades)
                cache_data["entidades"] = filtered_entities
                cache_data["total_entidades"] = len(filtered_entities)
                cache_data["timestamp_validacao"] = datetime.now().isoformat()
                
                # Salvar cache com entidades filtradas
                with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Cache filtrado: {len(filtered_entities)} entidades de qualidade de {len(entidades)} originais")
                
                # 5. Mostrar resumo dos domínios coletados
                dominios = {}
                for e in filtered_entities:
                    dominio = e.get("domain", "UNKNOWN")
                    dominios[dominio] = dominios.get(dominio, 0) + 1
                
                logger.info("Entidades por domínio:")
                for dominio, count in dominios.items():
                    logger.info(f"  - {dominio}: {count} entidades")
                
                return True
            except Exception as e:
                logger.error(f"Erro ao processar o cache: {e}")
                return False
        else:
            logger.error("Arquivo de cache não foi criado!")
            return False
        
    except Exception as e:
        logger.error(f"Erro durante a atualização forçada: {e}")
        return False

async def main():
    """Função principal"""
    logger.info("Iniciando processo de atualização forçada com dados reais")
    
    success = await force_real_data_update()
    
    if success:
        logger.info("✅ Atualização forçada concluída com sucesso!")
        logger.info("O sistema agora está usando apenas dados reais do New Relic.")
        return 0
    else:
        logger.error("❌ Falha na atualização forçada!")
        logger.error("Verifique a conexão com o New Relic e tente novamente.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Processo interrompido pelo usuário")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Erro fatal: {e}", exc_info=True)
        sys.exit(1)
