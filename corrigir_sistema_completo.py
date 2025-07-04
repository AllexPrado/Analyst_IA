#!/usr/bin/env python3
"""
Script para corrigir problemas detectados no sistema:
1. Cache com poucas entidades (3 vs. 190+)
2. Frontend sem dados reais
3. Chat IA com respostas simuladas
"""

import os
import sys
import logging
import asyncio
import json
import shutil
from pathlib import Path
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adicionar o diretório atual e backend ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

# Imports necessários do backend
try:
    from backend.utils.newrelic_advanced_collector import coletar_entidades_avancado
    from backend.utils.cache import atualizar_cache_completo, _cache, salvar_cache_no_disco
    from backend.utils.frontend_data_integrator import FrontendIntegrator
except ImportError:
    try:
        from utils.newrelic_advanced_collector import coletar_entidades_avancado
        from utils.cache import atualizar_cache_completo, _cache, salvar_cache_no_disco
        from utils.frontend_data_integrator import FrontendIntegrator
    except ImportError:
        logger.error("Não foi possível importar módulos do backend. Verifique o ambiente.")
        sys.exit(1)

async def corrigir_cache_dados():
    """
    Corrige o cache forçando a coleta de todas as entidades disponíveis no New Relic
    usando o coletor avançado configurado para buscar o máximo de entidades possível.
    """
    logger.info("=== CORRIGINDO CACHE COM DADOS COMPLETOS DO NEW RELIC ===")
    
    # Backup do cache original
    cache_path = Path("backend/historico/cache_completo.json")
    if cache_path.exists():
        backup_path = cache_path.with_name(f"cache_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        shutil.copy(cache_path, backup_path)
        logger.info(f"Backup do cache criado em: {backup_path}")
    
    logger.info("Coletando todas as entidades disponíveis no New Relic...")
    entidades = await coletar_entidades_avancado(max_entidades=500)
    
    if not entidades:
        logger.error("Falha ao coletar entidades do New Relic!")
        return False
    
    logger.info(f"✅ Coletadas {len(entidades)} entidades do New Relic")
    
    # Organizar por domínio para estatísticas
    dominios = {}
    for entidade in entidades:
        dominio = entidade.get("domain", "unknown").upper()
        if dominio not in dominios:
            dominios[dominio] = 0
        dominios[dominio] += 1
    
    for dominio, count in dominios.items():
        logger.info(f"  • {dominio}: {count} entidades")
    
    # Atualizar cache com as novas entidades
    _cache["entidades"] = entidades
    
    # Organizar por domínios também
    for entidade in entidades:
        domain = entidade.get("domain", "unknown").lower()
        if domain not in _cache:
            _cache[domain] = []
        _cache[domain].append(entidade)
    
    # Adicionar timestamp e metadados
    _cache["metadata"] = {
        "timestamp": datetime.now().isoformat(),
        "source": "New Relic API (Collector Avançado)",
        "total_entities": len(entidades),
        "domains": dominios
    }
    
    # Salvar cache atualizado
    await salvar_cache_no_disco()
    
    logger.info(f"✅ Cache atualizado com {len(entidades)} entidades reais")
    return True

async def atualizar_frontend_dados():
    """
    Processa os dados do cache para o frontend e garante
    que todos os arquivos de dados estão atualizados.
    """
    logger.info("=== ATUALIZANDO DADOS DO FRONTEND ===")
    
    try:
        integrador = FrontendIntegrator()
        resultado = await integrador.process_all_data()
        
        if resultado:
            logger.info("✅ Dados do frontend atualizados com sucesso")
        else:
            logger.error("❌ Falha ao atualizar dados do frontend")
        
        return resultado
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar frontend: {e}")
        return False

async def corrigir_chat_ia():
    """
    Corrige as respostas do chat IA para usar apenas dados reais
    removendo o uso de templates fixos e conhecimento simulado.
    """
    logger.info("=== CORRIGINDO CHAT IA PARA USAR APENAS DADOS REAIS ===")
    
    chat_endpoints_path = Path("backend/endpoints/chat_endpoints.py")
    
    if not chat_endpoints_path.exists():
        logger.error(f"Arquivo não encontrado: {chat_endpoints_path}")
        return False
    
    try:
        with open(chat_endpoints_path, "r", encoding="utf-8") as f:
            conteudo = f.read()
        
        # Verificar se o arquivo contém o banco de conhecimento simulado
        if "KNOWLEDGE_BASE = {" in conteudo:
            logger.info("Removendo banco de conhecimento simulado do chat_endpoints.py")
            
            # Criar backup
            backup_path = chat_endpoints_path.with_name(f"chat_endpoints_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(conteudo)
            
            # Remover o banco de conhecimento simulado
            conteudo_modificado = conteudo.replace(
                "# Banco de conhecimento simulado para respostas mais relevantes\nKNOWLEDGE_BASE = {",
                "# Removido banco de conhecimento simulado - usando apenas dados reais\n'''\nAntigo KNOWLEDGE_BASE = {"
            )
            
            # Fechar o comentário do antigo conhecimento
            conteudo_modificado = conteudo_modificado.replace(
                "}\n\n# Função para encontrar entidades relevantes",
                "}\n'''\n\n# Função para encontrar entidades relevantes"
            )
            
            # Salvar as alterações
            with open(chat_endpoints_path, "w", encoding="utf-8") as f:
                f.write(conteudo_modificado)
            
            logger.info(f"✅ Chat IA corrigido: conhecimento simulado removido")
            return True
        else:
            logger.info("✅ Chat IA já está configurado para usar apenas dados reais")
            return True
    
    except Exception as e:
        logger.error(f"❌ Erro ao corrigir Chat IA: {e}")
        return False

async def main():
    """Função principal que corrige todos os problemas identificados"""
    logger.info("🚀 INICIANDO CORREÇÃO COMPLETA DO SISTEMA")
    
    # 1. Garantir que a variável USE_SIMULATED_DATA está configurada como false no .env
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, "r") as f:
            linhas = f.readlines()
        
        encontrado = False
        with open(env_path, "w") as f:
            for linha in linhas:
                if linha.startswith("USE_SIMULATED_DATA="):
                    f.write("USE_SIMULATED_DATA=false\n")
                    encontrado = True
                else:
                    f.write(linha)
            
            if not encontrado:
                f.write("\n# Importante: Forçar uso de dados reais\nUSE_SIMULATED_DATA=false\n")
        
        logger.info("✅ Arquivo .env atualizado para usar dados reais")
    
    # 2. Corrigir o cache para conter todas as entidades disponíveis
    cache_ok = await corrigir_cache_dados()
    if not cache_ok:
        logger.error("❌ Falha na correção do cache. Abortando.")
        return False
    
    # 3. Atualizar os dados do frontend
    frontend_ok = await atualizar_frontend_dados()
    if not frontend_ok:
        logger.warning("⚠️ Falha na atualização do frontend. Continuando com os outros passos...")
    
    # 4. Corrigir as respostas do chat IA
    chat_ok = await corrigir_chat_ia()
    if not chat_ok:
        logger.warning("⚠️ Falha na correção do Chat IA. Continuando...")
    
    # Atualizar o indicador de dados reais
    indicador_path = Path("backend/cache/data_source_indicator.json")
    indicador_path.parent.mkdir(parents=True, exist_ok=True)
    
    indicador = {
        "using_real_data": True,
        "timestamp": datetime.now().isoformat(),
        "source": "New Relic API",
        "configured_by": "corrigir_sistema_completo.py",
        "entities_count": len(_cache.get("entidades", []))
    }
    
    with open(indicador_path, "w") as f:
        json.dump(indicador, f, indent=2)
    
    logger.info("✅ Indicador de dados reais atualizado")
    
    # Relatório final
    logger.info("\n=== RELATÓRIO DE CORREÇÃO ===")
    logger.info(f"Cache corrigido: {'✅ SIM' if cache_ok else '❌ NÃO'}")
    logger.info(f"Frontend atualizado: {'✅ SIM' if frontend_ok else '❌ NÃO'}")
    logger.info(f"Chat IA corrigido: {'✅ SIM' if chat_ok else '❌ NÃO'}")
    logger.info(f"Entidades no cache: {len(_cache.get('entidades', []))}")
    
    return cache_ok

if __name__ == "__main__":
    asyncio.run(main())
