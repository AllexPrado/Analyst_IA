"""
Sistema de inicialização e verificação de integridade do cache.
Este módulo implementa funções para garantir que o cache seja inicializado
corretamente e contém dados válidos para o funcionamento da aplicação.
"""

import os
import json
import logging
import asyncio
import traceback
from datetime import datetime
from pathlib import Path
import aiofiles
import shutil

# Configuração de logging
logger = logging.getLogger(__name__)

# Importações internas
from .cache import (
    CACHE_FILE, CACHE_HISTORICO_DIR, CACHE_CONSULTA_DIR,
    _cache, salvar_cache_no_disco, carregar_cache_do_disco,
    atualizar_cache_completo
)

async def inicializar_cache(coletar_contexto_fn):
    """
    Inicializa o sistema de cache, garantindo que o arquivo de cache exista
    e contenha dados válidos. Se o arquivo não existir ou estiver corrompido,
    uma nova coleta é realizada.
    
    Args:
        coletar_contexto_fn: Função assíncrona para coletar contexto completo
        
    Returns:
        bool: True se a inicialização foi bem-sucedida, False caso contrário
    """
    logger.info("Iniciando verificação e inicialização do cache")
    
    # Garantir que os diretórios existam
    os.makedirs(CACHE_HISTORICO_DIR, exist_ok=True)
    os.makedirs(CACHE_CONSULTA_DIR, exist_ok=True)
    
    # Verificar se o cache em disco existe
    cache_exists = CACHE_FILE.exists()
    cache_valid = False
    cache_backup = None
    
    if cache_exists:
        logger.info(f"Arquivo de cache encontrado: {CACHE_FILE}")
        try:
            # Tentar carregar o cache atual
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                
            # Verificar se o cache tem a estrutura correta
            if isinstance(cache_data, dict) and 'timestamp' in cache_data:
                logger.info("Estrutura do cache válida")
                cache_valid = True
                cache_backup = cache_data
            else:
                logger.warning("Arquivo de cache tem estrutura inválida")
        except json.JSONDecodeError:
            logger.error("Arquivo de cache está corrompido (JSON inválido)")
        except Exception as e:
            logger.error(f"Erro ao verificar arquivo de cache: {e}")
            logger.error(traceback.format_exc())
    else:
        logger.warning("Arquivo de cache não encontrado")
    
    # Se o cache não for válido, criar um backup do arquivo atual (se existir)
    if cache_exists and not cache_valid:
        try:
            backup_path = CACHE_HISTORICO_DIR / f"cache_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            shutil.copy2(CACHE_FILE, backup_path)
            logger.info(f"Backup do cache criado em {backup_path}")
        except Exception as e:
            logger.error(f"Erro ao criar backup do cache: {e}")
    
    # Se o cache não existir ou não for válido, tentar criar novo
    if not cache_valid:
        logger.info("Iniciando coleta de dados para criar novo cache")
        
        # Tentar até 3 vezes para garantir sucesso
        for attempt in range(3):
            try:
                logger.info(f"Tentativa {attempt + 1}/3 de criar novo cache")
                
                # Coleta de dados do New Relic
                contexto = await coletar_contexto_fn()
                
                if contexto and isinstance(contexto, dict):
                    # Verificar se o contexto tem dados válidos
                    entidades = contexto.get('entidades', [])
                    
                    if entidades:
                        logger.info(f"Coleta bem-sucedida: {len(entidades)} entidades")
                        
                        # Adicionar timestamp
                        contexto['timestamp'] = datetime.now().isoformat()
                        
                        # Atualizar o cache em memória e salvar em disco
                        _cache["dados"] = contexto
                        _cache["metadados"]["ultima_atualizacao"] = datetime.now().isoformat()
                        _cache["metadados"]["tipo_ultima_atualizacao"] = "initialization"
                        
                        await salvar_cache_no_disco()
                        logger.info("Novo cache criado e salvo com sucesso")
                        return True
                    else:
                        logger.warning("Contexto coletado não contém entidades")
                else:
                    logger.warning("Contexto coletado inválido ou vazio")
                
            except Exception as e:
                logger.error(f"Erro na tentativa {attempt + 1} de criar cache: {e}")
                logger.error(traceback.format_exc())
            
            # Esperar antes da próxima tentativa
            if attempt < 2:  # não espera após a última tentativa
                await asyncio.sleep(5)
        
        # Se todas as tentativas falharem e temos um backup, usar ele
        if cache_backup:
            logger.warning("Todas as tentativas falharam. Restaurando backup do cache")
            _cache["dados"] = cache_backup
            _cache["metadados"]["ultima_atualizacao"] = datetime.now().isoformat()
            _cache["metadados"]["tipo_ultima_atualizacao"] = "recovery_from_backup"
            
            await salvar_cache_no_disco()
            logger.info("Cache restaurado do backup")
            return True
        
        logger.error("CRÍTICO: Não foi possível inicializar o cache")
        return False
    
    # Se chegou aqui, o cache é válido
    logger.info("Cache já existe e é válido")
    
    # Carregar o cache existente na memória
    await carregar_cache_do_disco()
    
    return True

async def verificar_integridade_cache():
    """
    Verifica se o cache está íntegro e contém todos os componentes necessários.
    Retorna diagnóstico detalhado sobre o estado do cache.
    
    Returns:
        dict: Diagnóstico do estado do cache
    """
    diagnóstico = {
        "timestamp": datetime.now().isoformat(),
        "arquivo_cache": str(CACHE_FILE),
        "arquivo_existe": CACHE_FILE.exists(),
        "tamanho_bytes": 0,
        "integridade": False,
        "ultima_atualizacao": None,
        "idade_horas": None,
        "total_entidades": 0,
        "entidades_por_dominio": {},
        "erros": []
    }
    
    # Verificar se o arquivo existe
    if not diagnóstico["arquivo_existe"]:
        diagnóstico["erros"].append("Arquivo de cache não encontrado")
        return diagnóstico
    
    # Verificar tamanho do arquivo
    try:
        diagnóstico["tamanho_bytes"] = CACHE_FILE.stat().st_size
    except Exception as e:
        diagnóstico["erros"].append(f"Erro ao verificar tamanho do arquivo: {e}")
    
    # Tentar carregar o cache
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # Verificar timestamp
        if "timestamp" in cache_data:
            diagnóstico["ultima_atualizacao"] = cache_data["timestamp"]
            
            try:
                data_cache = datetime.fromisoformat(cache_data["timestamp"])
                agora = datetime.now()
                diagnóstico["idade_horas"] = (agora - data_cache).total_seconds() / 3600
            except:
                diagnóstico["erros"].append("Formato de timestamp inválido")
        else:
            diagnóstico["erros"].append("Cache não contém timestamp")
        
        # Verificar entidades
        entidades = cache_data.get('entidades', [])
        diagnóstico["total_entidades"] = len(entidades)
        
        # Contar entidades por domínio
        dominios = {}
        for e in entidades:
            dominio = e.get('domain', 'UNKNOWN')
            dominios[dominio] = dominios.get(dominio, 0) + 1
        
        diagnóstico["entidades_por_dominio"] = dominios
        
        # Verificar se temos entidades de diferentes domínios
        if len(dominios) < 3 and diagnóstico["total_entidades"] > 0:
            diagnóstico["erros"].append("Cache tem poucos domínios")
        
        # Verificar integridade geral
        diagnóstico["integridade"] = (
            diagnóstico["total_entidades"] > 0 and
            diagnóstico["ultima_atualizacao"] is not None and
            len(diagnóstico["erros"]) == 0
        )
        
    except json.JSONDecodeError:
        diagnóstico["erros"].append("Arquivo de cache corrompido (JSON inválido)")
    except Exception as e:
        diagnóstico["erros"].append(f"Erro ao analisar cache: {e}")
    
    return diagnóstico

async def main():
    """Função para teste direto deste módulo"""
    from .newrelic_collector import coletar_contexto_completo
    
    # Configurar logging para teste
    logging.basicConfig(level=logging.INFO)
    
    print("== VERIFICAÇÃO DE INTEGRIDADE ==")
    diagnostico = await verificar_integridade_cache()
    print(f"Arquivo: {diagnostico['arquivo_cache']}")
    print(f"Existe: {diagnostico['arquivo_existe']}")
    print(f"Tamanho: {diagnostico['tamanho_bytes'] / 1024:.2f} KB")
    print(f"Última atualização: {diagnostico['ultima_atualizacao']}")
    print(f"Idade: {diagnostico['idade_horas']:.2f} horas")
    print(f"Total de entidades: {diagnostico['total_entidades']}")
    print(f"Domínios: {diagnostico['entidades_por_dominio']}")
    print(f"Erros: {diagnostico['erros']}")
    print(f"Integridade: {diagnostico['integridade']}")
    
    if not diagnostico['integridade']:
        print("\n== INICIANDO INICIALIZAÇÃO DO CACHE ==")
        result = await inicializar_cache(coletar_contexto_completo)
        print(f"Inicialização bem-sucedida: {result}")
        
        if result:
            print("\n== VERIFICANDO NOVAMENTE ==")
            diagnostico = await verificar_integridade_cache()
            print(f"Integridade após inicialização: {diagnostico['integridade']}")
            print(f"Total de entidades: {diagnostico['total_entidades']}")

if __name__ == "__main__":
    asyncio.run(main())
