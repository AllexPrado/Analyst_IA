import asyncio
import logging
import json
import sys
from pathlib import Path
from datetime import datetime

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Importar as funções do coletor do New Relic
from utils.newrelic_collector import buscar_todas_entidades, coletar_contexto_completo
import aiohttp

# Diretório para salvar os resultados
CACHE_DIR = Path("historico")
CACHE_DIR.mkdir(exist_ok=True)

async def salvar_resultados(dados, nome_arquivo):
    """Salva os dados em um arquivo JSON."""
    caminho = CACHE_DIR / f"{nome_arquivo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)
    logger.info(f"Dados salvos em {caminho}")
    return caminho

async def teste_buscar_entidades():
    """Testa a função buscar_todas_entidades e salva o resultado."""
    logger.info("Iniciando teste de buscar_todas_entidades...")
    try:
        async with aiohttp.ClientSession() as session:
            entidades = await buscar_todas_entidades(session)
            logger.info(f"Total de entidades encontradas: {len(entidades)}")
            
            # Análise das entidades por domínio
            dominios = {}
            for e in entidades:
                domain = e.get("domain", "UNKNOWN")
                if domain not in dominios:
                    dominios[domain] = 0
                dominios[domain] += 1
            
            logger.info(f"Distribuição por domínio: {dominios}")
            
            # Salvar resultados
            caminho = await salvar_resultados(entidades, "entidades")
            
            # Retornar True apenas se encontrou pelo menos uma entidade
            return len(entidades) > 0, caminho
    except Exception as e:
        logger.error(f"Erro ao buscar entidades: {e}")
        return False, None

async def teste_coletar_contexto():
    """Testa a função coletar_contexto_completo e salva o resultado."""
    logger.info("Iniciando teste de coletar_contexto_completo...")
    try:
        contexto = await coletar_contexto_completo()
        
        # Análise do contexto
        dominios = {}
        total_entidades = 0
        total_com_metricas = 0
        
        for dominio, entidades in contexto.items():
            if dominio == "alertas":
                continue
            dominios[dominio] = len(entidades)
            total_entidades += len(entidades)
        
        logger.info(f"Total de entidades no contexto: {total_entidades}")
        logger.info(f"Distribuição por domínio no contexto: {dominios}")
        
        # Formatar a saída para impressão
        resumo = {
            "timestamp": datetime.now().isoformat(),
            "total_entidades": total_entidades,
            "dominios": dominios
        }
        
        # Salvar o contexto completo
        caminho_contexto = await salvar_resultados(contexto, "contexto_completo")
        # Salvar o resumo
        caminho_resumo = await salvar_resultados(resumo, "contexto_resumo")
        
        return total_entidades > 0, caminho_contexto
    except Exception as e:
        logger.error(f"Erro ao coletar contexto: {e}", exc_info=True)
        return False, None

async def atualizar_cache_manual():
    """Executa ambos os testes e atualiza o cache manualmente."""
    logger.info("=== INICIANDO ATUALIZAÇÃO MANUAL DO CACHE ===")
    
    # Teste de buscar entidades
    sucesso_entidades, caminho_entidades = await teste_buscar_entidades()
    if sucesso_entidades:
        logger.info(f"✅ Teste de buscar entidades concluído com sucesso!")
    else:
        logger.error("❌ Falha ao buscar entidades!")
        return False
    
    # Teste de coletar contexto
    sucesso_contexto, caminho_contexto = await teste_coletar_contexto()
    if sucesso_contexto:
        logger.info(f"✅ Teste de coletar contexto concluído com sucesso!")
    else:
        logger.error("❌ Falha ao coletar contexto!")
        return False
    
    logger.info("=== ATUALIZAÇÃO MANUAL DO CACHE CONCLUÍDA COM SUCESSO ===")
    logger.info(f"Entidades salvas em: {caminho_entidades}")
    logger.info(f"Contexto salvo em: {caminho_contexto}")
    
    # Copiar o contexto para o local usado pelo cache automático
    from utils.cache import CACHE_FILE, salvar_cache_no_disco, _cache
    
    try:
        with open(caminho_contexto, 'r', encoding='utf-8') as f:
            contexto = json.load(f)
            
        # Atualizar o cache em memória
        _cache["dados"] = contexto
        _cache["metadados"]["ultima_atualizacao"] = datetime.now().isoformat()
        _cache["metadados"]["atualizacao_forcada"] = True
        _cache["metadados"]["tipo_ultima_atualizacao"] = "manual"
        
        # Salvar no local padrão
        await salvar_cache_no_disco()
        logger.info(f"Cache atualizado manualmente e salvo em {CACHE_FILE}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar cache: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    logger.info("Iniciando script de atualização manual do cache...")
    try:
        sucesso = asyncio.run(atualizar_cache_manual())
        if sucesso:
            logger.info("Script finalizado com SUCESSO!")
            sys.exit(0)
        else:
            logger.error("Script finalizado com ERROS!")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Script interrompido pelo usuário")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Erro não tratado: {e}", exc_info=True)
        sys.exit(1)
