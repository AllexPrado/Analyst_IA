"""
Script para validar a integração do sistema de cache avançado.
Este script verifica se o cache está funcionando corretamente e se a integração
automática está operacional.
"""

import os
import sys
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("validacao_cache.log")
    ]
)
logger = logging.getLogger(__name__)

# Adiciona diretórios ao path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
backend_dir = current_dir / "backend"
if backend_dir.exists():
    sys.path.append(str(backend_dir))

def exibir_cabecalho(titulo):
    """Exibe um cabeçalho formatado no console"""
    print("\n" + "=" * 80)
    print(f"  {titulo}")
    print("=" * 80)

async def teste_1_importacao():
    """Testa a importação dos módulos de cache"""
    exibir_cabecalho("TESTE 1: Importação de Módulos")
    
    try:
        # Importações do sistema de cache original
        from backend.utils.cache import (
            get_cache, forcar_atualizacao_cache, diagnosticar_cache,
            carregar_cache_do_disco, salvar_cache_no_disco
        )
        print("✅ Módulos de cache original importados com sucesso")
        
        # Importações do sistema de cache avançado
        from backend.utils.cache_advanced import (
            inicializar_sistema_cache, status_cache, 
            atualizar_cache_incremental,
            coletar_contexto_completo_avancado
        )
        print("✅ Módulos de cache avançado importados com sucesso")
        
        from backend.utils.cache_initializer import verificar_integridade_cache, inicializar_cache
        print("✅ Módulo de inicialização de cache importado com sucesso")
        
        from backend.utils.cache_collector import coletar_contexto_completo
        print("✅ Módulo de coleta de contexto importado com sucesso")
        
        # Tenta importar o módulo de integração
        import backend.cache_integration
        print("✅ Módulo de integração importado com sucesso")
        
        return True
    except ImportError as import_error:
        logger.error(f"Erro ao importar módulos: {import_error}")
        print(f"❌ Erro ao importar: {import_error}")
        return False

async def teste_2_verificacao_cache():
    """Verifica o estado atual do cache"""
    exibir_cabecalho("TESTE 2: Estado Atual do Cache")
    
    try:
        from backend.utils.cache import diagnosticar_cache
        from backend.utils.cache_initializer import verificar_integridade_cache
        
        # Diagnóstico padrão
        diag = diagnosticar_cache()
        print(f"Status: {diag.get('status', 'Desconhecido')}")
        print(f"Última atualização: {diag.get('ultima_atualizacao', 'Nunca')}")
        if 'idade_horas' in diag:
            print(f"Idade: {diag['idade_horas']:.2f} horas")
        
        print(f"Total de chaves: {diag.get('total_chaves_dados', 0)}")
        print(f"Chaves: {diag.get('chaves_dados', [])}")
        print(f"Tamanho em disco: {diag.get('tamanho_disco_mb', 0):.2f} MB")
        
        # Diagnóstico avançado
        integridade = await verificar_integridade_cache()
        print("\n-- Integridade do Cache --")
        print(f"Arquivo: {integridade['arquivo_cache']}")
        print(f"Existe: {integridade['arquivo_existe']}")
        print(f"Integridade: {integridade['integridade']}")
        print(f"Total de entidades: {integridade['total_entidades']}")
        
        if integridade['entidades_por_dominio']:
            print("\n-- Entidades por Domínio --")
            for dominio, contagem in integridade['entidades_por_dominio'].items():
                print(f"{dominio}: {contagem}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao verificar estado do cache: {e}")
        print(f"❌ Erro: {e}")
        import traceback
        print(traceback.format_exc())
        return False

async def teste_3_inicializacao_sistema():
    """Testa a inicialização do sistema de cache"""
    exibir_cabecalho("TESTE 3: Inicialização do Sistema de Cache")
    
    try:
        from backend.utils.cache_advanced import inicializar_sistema_cache
        
        print("Inicializando sistema de cache avançado...")
        resultado = await inicializar_sistema_cache()
        
        if resultado:
            print("✅ Sistema de cache inicializado com sucesso!")
            return True
        else:
            print("❌ Falha ao inicializar o sistema de cache")
            return False
    except Exception as e:
        logger.error(f"Erro ao inicializar sistema de cache: {e}")
        print(f"❌ Erro: {e}")
        import traceback
        print(traceback.format_exc())
        return False

async def teste_4_busca_cache():
    """Testa a busca de dados no cache"""
    exibir_cabecalho("TESTE 4: Busca de Dados no Cache")
    
    try:
        from backend.utils.cache import get_cache
        
        print("Buscando dados no cache...")
        cache = await get_cache(forcar_atualizacao=False)
        
        entidades = cache.get("entidades", [])
        if entidades:
            print(f"✅ Cache encontrado com {len(entidades)} entidades")
            
            # Verificar se há dados em algumas entidades
            total_com_dados = sum(1 for e in entidades if e.get("name") and e.get("dados"))
            print(f"Entidades com dados: {total_com_dados} ({total_com_dados/len(entidades)*100:.1f}%)")
            
            # Mostrar algumas entidades de exemplo
            print("\n-- Primeiras 3 Entidades --")
            for i, entidade in enumerate(entidades[:3]):
                print(f"[{i+1}] {entidade.get('name', 'Sem nome')} ({entidade.get('domain', 'Desconhecido')})")
                print(f"    GUID: {entidade.get('guid', 'Não disponível')}")
                print(f"    Possui dados: {'Sim' if entidade.get('dados') else 'Não'}")
            
            return True
        else:
            print("❌ Cache não contém entidades")
            return False
    except Exception as e:
        logger.error(f"Erro ao buscar dados no cache: {e}")
        print(f"❌ Erro: {e}")
        import traceback
        print(traceback.format_exc())
        return False

async def teste_5_status_avancado():
    """Testa o status avançado do cache"""
    exibir_cabecalho("TESTE 5: Status Avançado do Cache")
    
    try:
        from backend.utils.cache_advanced import status_cache
        
        print("Obtendo status detalhado do cache...")
        status = await status_cache()
        
        print(f"Status: {status.get('status', 'Desconhecido')}")
        print(f"Cache válido: {status.get('cache_valido', False)}")
        print(f"Última atualização: {status.get('ultima_atualizacao', 'Desconhecido')}")
        print(f"Idade (horas): {status.get('idade_horas', 'Desconhecido')}")
        print(f"Total de entidades: {status.get('total_entidades', 0)}")
        
        if status.get('entidades_por_dominio'):
            print("\n-- Entidades por Domínio --")
            for dominio, contagem in status['entidades_por_dominio'].items():
                print(f"{dominio}: {contagem}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao obter status avançado do cache: {e}")
        print(f"❌ Erro: {e}")
        import traceback
        print(traceback.format_exc())
        return False

async def main():
    """Função principal que executa todos os testes"""
    print("\n" + "=" * 80)
    print("  VALIDAÇÃO DO SISTEMA DE CACHE AVANÇADO")
    print("=" * 80)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Diretório atual: {os.getcwd()}")
    
    # Executar testes
    resultados = {}
    
    resultados["Importação"] = await teste_1_importacao()
    resultados["Verificação"] = await teste_2_verificacao_cache()
    resultados["Inicialização"] = await teste_3_inicializacao_sistema()
    resultados["Busca"] = await teste_4_busca_cache()
    resultados["Status"] = await teste_5_status_avancado()
    
    # Resumo dos resultados
    exibir_cabecalho("RESUMO DOS RESULTADOS")
    
    for nome, sucesso in resultados.items():
        status = "✅ PASSOU" if sucesso else "❌ FALHOU"
        print(f"{nome}: {status}")
    
    total_sucesso = sum(1 for sucesso in resultados.values() if sucesso)
    print(f"\nTeste concluído: {total_sucesso}/{len(resultados)} testes bem-sucedidos")
    
    # Gera um relatório final em JSON
    relatorio = {
        "data": datetime.now().isoformat(),
        "resultados": resultados,
        "total_testes": len(resultados),
        "testes_sucesso": total_sucesso,
        "status_geral": "OK" if total_sucesso == len(resultados) else "FALHA"
    }
    
    with open("relatorio_validacao_cache.json", "w", encoding="utf-8") as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)
    
    print(f"\nRelatório salvo em relatorio_validacao_cache.json")

if __name__ == "__main__":
    # Executar no event loop asyncio
    asyncio.run(main())
