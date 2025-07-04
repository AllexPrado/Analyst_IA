"""
Script para testar a qualidade dos dados e validar filtragem de entidades
"""

import asyncio
import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from pprint import pprint

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adiciona pasta atual ao path para importar módulos locais
sys.path.append(str(Path(__file__).parent))

async def testar_qualidade_dados():
    """
    Testa a qualidade dos dados nas entidades e a funcionalidade de filtragem
    """
    try:
        print("\n" + "="*80)
        print(" 🧪 INICIANDO TESTE DE QUALIDADE DE DADOS")
        print("="*80)
        
        # Importa utilitários necessários
        from backend.utils.cache import get_cache, limpar_cache_de_entidades_invalidas
        from backend.utils.entity_processor import filter_entities_with_data, is_entity_valid
        
        # Carrega o cache atual
        print("\n📂 Carregando cache atual...")
        cache = await get_cache()
        entidades = cache.get("entidades", [])
        print(f"   ✅ Cache carregado: {len(entidades)} entidades encontradas")
        
        # Estatísticas iniciais
        entidades_com_metricas = sum(1 for e in entidades if e.get("metricas"))
        entidades_sem_metricas = sum(1 for e in entidades if not e.get("metricas"))
        print(f"   📊 Estatísticas iniciais:")
        print(f"      - Com métricas: {entidades_com_metricas} ({entidades_com_metricas/len(entidades)*100:.1f}% do total)")
        print(f"      - Sem métricas: {entidades_sem_metricas} ({entidades_sem_metricas/len(entidades)*100:.1f}% do total)")
        
        # Análise de domínios
        dominios = {}
        for e in entidades:
            domain = e.get("domain", "UNKNOWN")
            if domain not in dominios:
                dominios[domain] = {"total": 0, "com_metricas": 0, "sem_metricas": 0}
            
            dominios[domain]["total"] += 1
            if e.get("metricas"):
                dominios[domain]["com_metricas"] += 1
            else:
                dominios[domain]["sem_metricas"] += 1
        
        print("\n📊 Análise por domínio:")
        for domain, stats in sorted(dominios.items(), key=lambda x: x[1]["total"], reverse=True):
            total = stats["total"]
            com_metricas = stats["com_metricas"]
            taxa = com_metricas/total*100 if total > 0 else 0
            print(f"   - {domain}: {com_metricas}/{total} com métricas ({taxa:.1f}%)")
        
        # Filtragem de entidades inválidas
        print("\n🔍 Testando filtro de entidades inválidas...")
        entidades_filtradas = filter_entities_with_data(entidades)
        print(f"   ✅ Filtro aplicado: {len(entidades_filtradas)}/{len(entidades)} entidades válidas ({len(entidades_filtradas)/len(entidades)*100:.1f}%)")
        
        # Analisando dados das entidades filtradas
        metricas_disponibilidade = sum(1 for e in entidades_filtradas if any('apdex' in p for p in e.get('metricas', {}).values()))
        metricas_latencia = sum(1 for e in entidades_filtradas if any('response_time_max' in p for p in e.get('metricas', {}).values()))
        metricas_erros = sum(1 for e in entidades_filtradas if any('recent_error' in p for p in e.get('metricas', {}).values()))
        
        print(f"\n📈 Métricas disponíveis nas entidades filtradas:")
        print(f"   - Disponibilidade (Apdex): {metricas_disponibilidade} ({metricas_disponibilidade/len(entidades_filtradas)*100:.1f}%)")
        print(f"   - Latência: {metricas_latencia} ({metricas_latencia/len(entidades_filtradas)*100:.1f}%)")
        print(f"   - Erros: {metricas_erros} ({metricas_erros/len(entidades_filtradas)*100:.1f}%)")
        
        # Testando a limpeza do cache
        print("\n🧹 Testando função de limpeza do cache...")
        entidades_removidas = await limpar_cache_de_entidades_invalidas()
        print(f"   ✅ Limpeza concluída: {entidades_removidas} entidades removidas")
        
        # Carregando cache após limpeza
        cache_limpo = await get_cache()
        entidades_limpas = cache_limpo.get("entidades", [])
        print(f"   ✅ Cache após limpeza: {len(entidades_limpas)} entidades")
        
        # Verificando qualidade das entidades no cache limpo
        print("\n🔍 Analisando qualidade das entidades no cache limpo...")
        entidades_com_dados_reais = 0
        metricas_por_entidade = []
        
        for e in entidades_limpas:
            if not e.get("metricas"):
                continue
                
            metricas_reais = 0
            for period, metrics in e.get("metricas", {}).items():
                for metric_name, metric_data in metrics.items():
                    if metric_data and (isinstance(metric_data, list) and len(metric_data) > 0 or not isinstance(metric_data, list)):
                        metricas_reais += 1
            
            if metricas_reais > 0:
                entidades_com_dados_reais += 1
                metricas_por_entidade.append(metricas_reais)
        
        media_metricas = sum(metricas_por_entidade) / len(metricas_por_entidade) if metricas_por_entidade else 0
        
        print(f"   ✅ Entidades com dados reais: {entidades_com_dados_reais}/{len(entidades_limpas)} ({entidades_com_dados_reais/len(entidades_limpas)*100:.1f}%)")
        print(f"   ✅ Média de métricas por entidade: {media_metricas:.1f}")
        
        # Resultado final do teste
        print("\n" + "="*80)
        taxa_qualidade = entidades_com_dados_reais / len(entidades) * 100 if len(entidades) > 0 else 0
        
        if taxa_qualidade >= 60:
            print(f" ✅ TESTE CONCLUÍDO COM SUCESSO: {taxa_qualidade:.1f}% de qualidade de dados")
        elif taxa_qualidade >= 30:
            print(f" ⚠️ TESTE CONCLUÍDO COM RESSALVAS: {taxa_qualidade:.1f}% de qualidade de dados")
        else:
            print(f" ❌ TESTE FALHOU: {taxa_qualidade:.1f}% de qualidade de dados")
        
        print("="*80)
        
    except Exception as e:
        logger.error(f"Erro ao testar qualidade dos dados: {e}", exc_info=True)
        print(f"\n❌ ERRO NO TESTE: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(testar_qualidade_dados())
