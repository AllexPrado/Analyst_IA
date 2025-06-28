"""
Script para testar, manter e corrigir o sistema de cache.
Este script permite verificar, inicializar e corrigir o cache do Analyst IA.
"""

import os
import sys
import asyncio
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Adiciona diretórios ao path
current_dir = Path(__file__).parent
if current_dir.name == "backend":
    sys.path.append(str(current_dir.parent))
else:
    sys.path.append(str(current_dir))
    backend_dir = current_dir / "backend"
    if backend_dir.exists():
        sys.path.append(str(backend_dir))

try:
    # Importações do sistema de cache
    from backend.utils.cache import (
        get_cache, forcar_atualizacao_cache, diagnosticar_cache,
        carregar_cache_do_disco, salvar_cache_no_disco
    )
    from backend.utils.cache_advanced import (
        inicializar_sistema_cache, status_cache, 
        coletar_contexto_completo_avancado
    )
    from backend.utils.cache_initializer import verificar_integridade_cache
    from backend.utils.entity_processor import filter_entities_with_data
    
    logger.info("Módulos importados com sucesso")
except ImportError as e:
    logger.error(f"Erro ao importar módulos: {e}")
    sys.exit(1)

async def verificar_cache():
    """Verifica o estado atual do cache"""
    logger.info("Verificando estado do cache...")
    
    # Diagnóstico padrão
    diag = diagnosticar_cache()
    print("\n== DIAGNÓSTICO DO CACHE ==")
    print(f"Status: {diag.get('status', 'Desconhecido')}")
    print(f"Última atualização: {diag.get('ultima_atualizacao', 'Nunca')}")
    if 'idade_horas' in diag:
        print(f"Idade: {diag['idade_horas']:.2f} horas")
    
    print(f"Total de chaves: {diag.get('total_chaves_dados', 0)}")
    print(f"Chaves: {diag.get('chaves_dados', [])}")
    print(f"Tamanho em disco: {diag.get('tamanho_disco_mb', 0):.2f} MB")
    
    # Diagnóstico avançado
    integridade = await verificar_integridade_cache()
    print("\n== INTEGRIDADE DO CACHE ==")
    print(f"Arquivo: {integridade['arquivo_cache']}")
    print(f"Existe: {integridade['arquivo_existe']}")
    print(f"Integridade: {integridade['integridade']}")
    print(f"Total de entidades: {integridade['total_entidades']}")
    print(f"Erros: {integridade['erros']}")
    
    if integridade['entidades_por_dominio']:
        print("\n== ENTIDADES POR DOMÍNIO ==")
        for dominio, contagem in integridade['entidades_por_dominio'].items():
            print(f"{dominio}: {contagem}")
    
    # Verificar cache atual
    cache = await get_cache(forcar_atualizacao=False)
    entidades = cache.get("entidades", [])
    
    if entidades:
        print(f"\nTotal de {len(entidades)} entidades no cache")
        
        # Verifica qualidade dos dados
        entidades_com_dados = filter_entities_with_data(entidades)
        print(f"Entidades com dados válidos: {len(entidades_com_dados)} de {len(entidades)} ({len(entidades_com_dados)/len(entidades)*100:.1f}%)")
    else:
        print("\nNenhuma entidade no cache")

async def inicializar():
    """Inicializa o sistema de cache avançado"""
    logger.info("Inicializando sistema de cache avançado...")
    
    try:
        resultado = await inicializar_sistema_cache()
        if resultado:
            print("\n✅ Sistema de cache inicializado com sucesso!")
        else:
            print("\n❌ Falha ao inicializar sistema de cache")
    except Exception as e:
        logger.error(f"Erro ao inicializar cache: {e}")
        print(f"\n❌ Erro ao inicializar cache: {e}")

async def forcar_atualizacao():
    """Força uma atualização completa do cache"""
    logger.info("Forçando atualização do cache...")
    
    try:
        print("Atualizando cache... (pode levar alguns minutos)")
        start_time = datetime.now()
        
        resultado = await forcar_atualizacao_cache(coletar_contexto_completo_avancado)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if resultado:
            print(f"\n✅ Cache atualizado com sucesso em {duration:.2f} segundos!")
            
            # Verificar resultados
            cache = await get_cache(forcar_atualizacao=False)
            entidades = cache.get("entidades", [])
            print(f"Total de {len(entidades)} entidades no cache")
            
            # Contar por domínio
            dominios = {}
            for e in entidades:
                dominio = e.get('domain', 'Desconhecido')
                dominios[dominio] = dominios.get(dominio, 0) + 1
            
            print("\nEntidades por domínio:")
            for dominio, contagem in dominios.items():
                print(f"- {dominio}: {contagem}")
        else:
            print("\n❌ Falha ao atualizar o cache")
    except Exception as e:
        logger.error(f"Erro ao atualizar cache: {e}")
        print(f"\n❌ Erro ao atualizar cache: {e}")

async def exportar_cache(caminho):
    """Exporta o cache atual para um arquivo JSON"""
    logger.info(f"Exportando cache para {caminho}...")
    
    try:
        cache = await get_cache(forcar_atualizacao=False)
        
        # Salvar em arquivo
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Cache exportado para {caminho}")
        print(f"Tamanho do arquivo: {os.path.getsize(caminho) / (1024*1024):.2f} MB")
    except Exception as e:
        logger.error(f"Erro ao exportar cache: {e}")
        print(f"\n❌ Erro ao exportar cache: {e}")

async def stats_cache():
    """Mostra estatísticas detalhadas do cache"""
    logger.info("Gerando estatísticas do cache...")
    
    try:
        cache = await get_cache(forcar_atualizacao=False)
        entidades = cache.get("entidades", [])
        
        if not entidades:
            print("\n⚠️ Nenhuma entidade no cache")
            return
            
        # Estatísticas básicas
        print("\n== ESTATÍSTICAS DO CACHE ==")
        print(f"Total de entidades: {len(entidades)}")
        timestamp = cache.get("timestamp", "Desconhecido")
        print(f"Timestamp: {timestamp}")
        
        try:
            ts = datetime.fromisoformat(timestamp)
            idade = (datetime.now() - ts).total_seconds() / 3600
            print(f"Idade: {idade:.2f} horas")
        except:
            print("Não foi possível calcular idade do cache")
        
        # Entidades por domínio
        dominios = {}
        tipos = {}
        entidades_com_metricas = 0
        total_metricas = 0
        
        for e in entidades:
            # Contar por domínio
            dominio = e.get('domain', 'Desconhecido')
            dominios[dominio] = dominios.get(dominio, 0) + 1
            
            # Contar por tipo
            tipo = e.get('entityType', 'Desconhecido')
            tipos[tipo] = tipos.get(tipo, 0) + 1
            
            # Contar métricas
            metricas = e.get('metricas', {})
            if metricas:
                entidades_com_metricas += 1
                
                for periodo, valores in metricas.items():
                    total_metricas += sum(1 for v in valores.values() if v is not None)
        
        print("\n== ENTIDADES POR DOMÍNIO ==")
        for dominio, contagem in sorted(dominios.items(), key=lambda x: x[1], reverse=True):
            print(f"{dominio}: {contagem}")
        
        print("\n== ENTIDADES POR TIPO ==")
        for tipo, contagem in sorted(tipos.items(), key=lambda x: x[1], reverse=True)[:10]:  # Top 10
            print(f"{tipo}: {contagem}")
        
        print("\n== MÉTRICAS ==")
        print(f"Entidades com métricas: {entidades_com_metricas} de {len(entidades)} ({entidades_com_metricas/len(entidades)*100:.1f}%)")
        print(f"Total de valores de métricas: {total_metricas}")
        print(f"Média de métricas por entidade: {total_metricas/len(entidades):.2f}")
        
    except Exception as e:
        logger.error(f"Erro ao gerar estatísticas: {e}")
        print(f"\n❌ Erro ao gerar estatísticas: {e}")

async def main():
    parser = argparse.ArgumentParser(description="Ferramenta de manutenção do cache do Analyst IA")
    parser.add_argument("--verificar", action="store_true", help="Verificar estado atual do cache")
    parser.add_argument("--inicializar", action="store_true", help="Inicializar sistema de cache avançado")
    parser.add_argument("--atualizar", action="store_true", help="Forçar atualização do cache")
    parser.add_argument("--exportar", metavar="CAMINHO", help="Exportar cache para arquivo JSON")
    parser.add_argument("--stats", action="store_true", help="Mostrar estatísticas detalhadas do cache")
    
    args = parser.parse_args()
    
    print("===================================================")
    print("🔧 FERRAMENTA DE MANUTENÇÃO DO CACHE - ANALYST IA")
    print("===================================================")
    
    # Se nenhum argumento for fornecido, mostre o status
    if not any([args.verificar, args.inicializar, args.atualizar, args.exportar, args.stats]):
        args.verificar = True
    
    # Executar operações solicitadas
    if args.verificar:
        await verificar_cache()
        
    if args.inicializar:
        await inicializar()
        
    if args.atualizar:
        await forcar_atualizacao()
        
    if args.exportar:
        await exportar_cache(args.exportar)
        
    if args.stats:
        await stats_cache()
    
    print("\n===================================================")
    print("🏁 OPERAÇÕES CONCLUÍDAS")
    print("===================================================")

if __name__ == "__main__":
    asyncio.run(main())
