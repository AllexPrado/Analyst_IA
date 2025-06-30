"""
Script para validar e reparar o cache do Analyst IA.
Este script verifica se o cache está íntegro e acessível para o chat e outros componentes.
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

# Configurações
CACHE_DIR = script_dir / "historico"
CACHE_FILE = CACHE_DIR / "cache_completo.json"
DADOS_DIR = script_dir / "dados"

async def verificar_e_reparar_cache():
    """Verifica e repara o sistema de cache"""
    try:
        logger.info("=" * 80)
        logger.info("INICIANDO VERIFICAÇÃO E REPARO DO CACHE")
        logger.info("=" * 80)
        
        # 1. Verificar se o diretório de cache existe
        if not CACHE_DIR.exists():
            logger.error(f"Diretório de cache não encontrado: {CACHE_DIR}")
            logger.info("Criando diretório de cache...")
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"Diretório de cache criado: {CACHE_DIR}")
        else:
            logger.info(f"Diretório de cache encontrado: {CACHE_DIR}")
        
        # 2. Verificar se o arquivo de cache existe
        if not CACHE_FILE.exists():
            logger.error(f"Arquivo de cache não encontrado: {CACHE_FILE}")
            logger.info("É necessário executar atualizar_cache_completo.py para criar o cache.")
            return False
        
        logger.info(f"Arquivo de cache encontrado: {CACHE_FILE}")
        
        # 3. Verificar integridade do arquivo de cache
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            # Verificar estrutura básica
            if not isinstance(cache_data, dict):
                logger.error("Cache não é um dicionário válido")
                return False
                
            # Verificar campos essenciais
            campos_essenciais = ['timestamp', 'entidades']
            for campo in campos_essenciais:
                if campo not in cache_data:
                    logger.error(f"Campo essencial ausente no cache: {campo}")
                    return False
            
            # Verificar entidades
            entidades = cache_data.get('entidades', [])
            if not entidades:
                logger.warning("Cache não contém entidades")
            else:
                logger.info(f"Cache contém {len(entidades)} entidades")
                
                # Validar estrutura de algumas entidades
                for i, entidade in enumerate(entidades[:3]):  # Verificar as 3 primeiras
                    if not isinstance(entidade, dict):
                        logger.error(f"Entidade {i} não é um dicionário válido")
                        continue
                    
                    # Verificar campos básicos
                    if 'name' not in entidade or 'guid' not in entidade:
                        logger.warning(f"Entidade {i} está faltando campos básicos")
                    
                    # Verificar métricas
                    if 'metricas' not in entidade or not entidade['metricas']:
                        logger.warning(f"Entidade {i} não tem métricas")
                
            logger.info("Cache validado com sucesso")
            logger.info(f"Timestamp do cache: {cache_data.get('timestamp')}")
            
            # 4. Otimizar o cache
            if len(entidades) > 0:
                # Garantir que todos os campos necessários para o chat estejam presentes
                entidades_otimizadas = []
                for entidade in entidades:
                    # Garantir presença de campos essenciais
                    entidade_otimizada = {
                        'name': entidade.get('name', 'Unknown'),
                        'guid': entidade.get('guid', 'unknown-guid'),
                        'domain': entidade.get('domain', 'unknown'),
                        'metricas': {}
                    }
                    
                    # Garantir estrutura de métricas
                    for periodo, metricas in entidade.get('metricas', {}).items():
                        if isinstance(metricas, dict):
                            entidade_otimizada['metricas'][periodo] = metricas
                    
                    # Incluir apenas se tiver métricas
                    if entidade_otimizada['metricas']:
                        entidades_otimizadas.append(entidade_otimizada)
                
                # Atualizar cache com entidades otimizadas
                if entidades_otimizadas:
                    cache_data['entidades'] = entidades_otimizadas
                    cache_data['timestamp_reparo'] = datetime.now().isoformat()
                    
                    # Fazer backup antes de modificar
                    backup_path = CACHE_FILE.with_suffix('.json.bak')
                    shutil.copy2(CACHE_FILE, backup_path)
                    logger.info(f"Backup do cache criado: {backup_path}")
                    
                    # Salvar cache otimizado
                    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                        json.dump(cache_data, f, ensure_ascii=False, indent=2)
                    
                    logger.info(f"Cache otimizado e salvo: {len(entidades_otimizadas)} entidades")
                else:
                    logger.warning("Nenhuma entidade válida encontrada para otimização")
            
            # 5. Verificar acesso ao cache
            try:
                from utils.cache import get_cache, _initialize_cache
                
                # Forçar reinicialização do cache
                await _initialize_cache(force=True)
                
                # Tentar acessar o cache
                cached_data = await get_cache()
                if cached_data and isinstance(cached_data, dict):
                    logger.info("Acesso ao cache bem-sucedido através da função get_cache()")
                    return True
                else:
                    logger.error("Falha ao acessar o cache através da função get_cache()")
                    return False
                
            except Exception as e:
                logger.error(f"Erro ao testar acesso ao cache: {e}")
                return False
            
        except json.JSONDecodeError:
            logger.error("Arquivo de cache não é um JSON válido")
            return False
        except Exception as e:
            logger.error(f"Erro ao validar cache: {e}")
            return False
    except Exception as e:
        logger.error(f"Erro durante verificação e reparo do cache: {e}")
        return False

async def main():
    """Função principal"""
    logger.info("Iniciando verificação e reparo do cache")
    
    success = await verificar_e_reparar_cache()
    
    if success:
        logger.info("✅ Verificação e reparo do cache concluídos com sucesso!")
        return 0
    else:
        logger.error("❌ Falha na verificação e reparo do cache!")
        logger.error("Execute 'python atualizar_cache_completo.py' para criar o cache do zero.")
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
