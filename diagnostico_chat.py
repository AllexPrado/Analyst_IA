"""
Script para diagnosticar problemas no chat do Analyst IA.
Verifica a qualidade dos dados enviados para o modelo OpenAI.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
import asyncio
import traceback

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Adicionar diretórios ao path para importar módulos
current_dir = Path(__file__).parent
backend_dir = current_dir / "backend"
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(backend_dir))

try:
    from backend.utils.entity_processor import filter_entities_with_data, is_entity_valid
    from backend.utils.context_enricher import ContextEnricher
    from backend.utils.intent_extractor import extract_metrics_for_query
    from backend.utils.learning_integration import learning_integration
except ImportError as import_error:
    logger.error(f"Erro ao importar módulos do backend: {import_error}")
    print(f"Erro ao importar módulos do backend: {import_error}")
    sys.exit(1)

async def diagnosticar_cache():
    """
    Verifica o cache de entidades e diagnóstica problemas.
    """
    print("\n🔍 DIAGNÓSTICO DO CACHE DE ENTIDADES\n")
    
    cache_path = Path("historico/cache_completo.json")
    if not cache_path.exists():
        print("❌ Erro: Arquivo de cache não encontrado!")
        return
    
    # Carrega o cache
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            cache = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao carregar o cache: {e}")
        return
    
    # Analisa o timestamp
    timestamp = cache.get("timestamp", "")
    print(f"📅 Timestamp do cache: {timestamp}")
    
    try:
        data_cache = datetime.fromisoformat(timestamp)
        agora = datetime.now()
        diff_dias = (agora - data_cache).days
        diff_horas = (agora - data_cache).total_seconds() / 3600
        
        if diff_dias > 0:
            print(f"⚠️ Cache desatualizado! {diff_dias} dias atrás")
        elif diff_horas > 3:
            print(f"⚠️ Cache potencialmente desatualizado: {diff_horas:.1f} horas atrás")
        else:
            print(f"✅ Cache recente: {diff_horas:.1f} horas atrás")
    except:
        print("⚠️ Impossível determinar idade do cache")
    
    # Analisa as entidades
    entidades = cache.get("entidades", [])
    print(f"\n📊 Entidades no cache: {len(entidades)}")
    
    if not entidades:
        print("❌ CRÍTICO: Nenhuma entidade no cache!")
        return
    
    # Analisa domínios
    dominios = {}
    for e in entidades:
        dominio = e.get('domain', 'Desconhecido')
        dominios[dominio] = dominios.get(dominio, 0) + 1
    
    print("\n📊 Distribuição por domínios:")
    for dominio, contagem in dominios.items():
        print(f"- {dominio}: {contagem}")
    
    # Filtra entidades e verifica qualidade
    print("\n🧪 Testando filtro de entidades...")
    entidades_filtradas = filter_entities_with_data(entidades)
    
    print(f"✅ Entidades válidas após filtro: {len(entidades_filtradas)} de {len(entidades)} ({len(entidades_filtradas)/len(entidades)*100:.1f}%)")
    
    if len(entidades_filtradas) == 0:
        print("\n❌ CRÍTICO: Todas as entidades foram filtradas! O chat não terá dados para análise.")
    
    # Amostra de entidades filtradas
    if entidades_filtradas:
        print("\n📋 Amostra de entidades válidas:")
        for i, e in enumerate(entidades_filtradas[:3]):
            metricas_count = sum(1 for periodo in e.get('metricas', {}).values() for metrica in periodo if periodo[metrica])
            print(f"{i+1}. {e.get('name')} [{e.get('domain')}] - {metricas_count} métricas")

async def simular_processamento_pergunta(pergunta):
    """
    Simula o processamento de uma pergunta sem enviar para a API OpenAI.
    """
    print("\n🔍 SIMULAÇÃO DE PROCESSAMENTO DE PERGUNTA\n")
    print(f"❓ Pergunta: \"{pergunta}\"")
    
    # Carrega o cache
    cache_path = Path("historico/cache_completo.json")
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            cache = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao carregar o cache: {e}")
        return
    
    entidades = cache.get("entidades", [])
    alertas = cache.get("alertas", [])
    
    # Filtra as entidades
    entidades_filtradas = filter_entities_with_data(entidades)
    print(f"🔍 Filtragem: {len(entidades_filtradas)} entidades válidas de {len(entidades)}")
    
    # Extrai intenção
    try:
        intent_info = extract_metrics_for_query(pergunta, entidades_filtradas)
        print(f"🎯 Intenção detectada: {intent_info['tipo_consulta']}")
        print(f"🔍 Filtros aplicados: {intent_info['filtros_aplicados']}")
        
        if intent_info['entidades_relevantes']:
            entidades_filtradas = intent_info['entidades_relevantes']
            print(f"✅ Entidades relevantes selecionadas: {len(entidades_filtradas)}")
    except Exception as e:
        print(f"⚠️ Erro ao extrair intenção: {e}")
    
    # Enriquecimento de contexto
    try:
        context_enricher = ContextEnricher()
        contexto = {"entidades": entidades_filtradas, "alertas": alertas}
        contexto_enriquecido = context_enricher.enriquecer_contexto(pergunta, contexto)
        
        print("\n📊 ANÁLISES GERADAS:")
        
        # Performance
        if contexto_enriquecido.get("analises", {}).get("performance"):
            perf = contexto_enriquecido["analises"]["performance"]
            print(f"✅ Análise de Performance: {len(str(perf))} caracteres")
        else:
            print("❌ Análise de Performance: Não gerada")
            
        # Erros
        if contexto_enriquecido.get("analises", {}).get("erros"):
            erros = contexto_enriquecido["analises"]["erros"]
            print(f"✅ Análise de Erros: {len(str(erros))} caracteres")
            
            # Stacktraces
            stacktraces = erros.get("stacktraces", [])
            print(f"📋 Stacktraces encontrados: {len(stacktraces)}")
            
            # Exemplos completos (novo)
            exemplos = erros.get("exemplos_completos", [])
            print(f"📋 Exemplos completos formatados: {len(exemplos)}")
            
            # Amostra de stacktrace
            if exemplos:
                print("\n📋 EXEMPLO DE STACKTRACE FORMATADO:")
                print(exemplos[0].get('formatted', 'Não disponível'))
        else:
            print("❌ Análise de Erros: Não gerada")
        
        # Correlação
        if contexto_enriquecido.get("analises", {}).get("correlacao"):
            corr = contexto_enriquecido["analises"]["correlacao"]
            print(f"✅ Análise de Correlação: {len(str(corr))} caracteres")
        else:
            print("❌ Análise de Correlação: Não gerada")
            
    except Exception as e:
        print(f"❌ Erro no enriquecimento de contexto: {e}")
        traceback.print_exc()

async def verificar_sistema_aprendizado():
    """
    Verifica o estado do sistema de aprendizado contínuo.
    """
    print("\n🧠 DIAGNÓSTICO DO SISTEMA DE APRENDIZADO\n")
    
    if not learning_integration.is_enabled():
        print("❌ Sistema de aprendizado desativado!")
        return
        
    try:
        # Verifica estatísticas
        stats = await learning_integration.obter_estatisticas()
        print(f"📊 Estatísticas do sistema de aprendizado:")
        for key, value in stats.items():
            print(f"- {key}: {value}")
        
        # Verifica contextos salvos
        contexts_dir = Path("backend/contexts")
        if contexts_dir.exists():
            contextos = list(contexts_dir.glob("*.json"))
            print(f"\n📁 Contextos encontrados: {len(contextos)}")
            
            if contextos:
                print("\n📋 Contextos recentes:")
                # Ordena por data de modificação (mais recentes primeiro)
                contextos.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                
                for ctx_path in contextos[:3]:
                    mod_time = datetime.fromtimestamp(os.path.getmtime(ctx_path))
                    print(f"- {ctx_path.name} ({mod_time.strftime('%Y-%m-%d %H:%M:%S')})")
                    
                    # Tenta ler o conteúdo
                    try:
                        with open(ctx_path, "r", encoding="utf-8") as f:
                            ctx_data = json.load(f)
                        
                        feedbacks = ctx_data.get("feedbacks", [])
                        print(f"  ✓ {len(feedbacks)} feedbacks registrados")
                    except Exception as e:
                        print(f"  ❌ Erro ao ler contexto: {e}")
        else:
            print("\n❌ Diretório de contextos não encontrado!")
            
    except Exception as e:
        print(f"❌ Erro ao verificar sistema de aprendizado: {e}")
        traceback.print_exc()

async def main():
    parser = argparse.ArgumentParser(description="Ferramenta de diagnóstico do chat Analyst IA")
    parser.add_argument("--cache", action="store_true", help="Analisa o cache de entidades")
    parser.add_argument("--pergunta", type=str, help="Simula processamento de uma pergunta")
    parser.add_argument("--aprendizado", action="store_true", help="Verifica sistema de aprendizado")
    parser.add_argument("--tudo", action="store_true", help="Executa todos os diagnósticos")
    
    args = parser.parse_args()
    
    print("====================================================")
    print("🔍 DIAGNÓSTICO DO SYSTEM CHAT ANALYST IA")
    print("====================================================")
    
    if args.tudo or (not args.cache and not args.pergunta and not args.aprendizado):
        await diagnosticar_cache()
        await simular_processamento_pergunta("Quais aplicações tiveram erros nas últimas 24 horas?")
        await verificar_sistema_aprendizado()
    else:
        if args.cache:
            await diagnosticar_cache()
        if args.pergunta:
            await simular_processamento_pergunta(args.pergunta)
        if args.aprendizado:
            await verificar_sistema_aprendizado()
            
    print("\n====================================================")
    print("🏁 DIAGNÓSTICO CONCLUÍDO")
    print("====================================================")

if __name__ == "__main__":
    asyncio.run(main())
