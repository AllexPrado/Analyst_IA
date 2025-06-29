"""
Script para verificar se as métricas estão sendo integradas corretamente
e se todos os componentes do sistema funcionam apropriadamente
"""

import os
import sys
import asyncio
import json
import logging
from pathlib import Path

# Configura logging
logging.basicConfig(level=logging.INFO,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adiciona diretório pai ao path para poder importar módulos corretamente
script_dir = Path(__file__).parent
sys.path.append(str(script_dir))

# Importa os módulos necessários
try:
    from main import get_cache, get_kpis, get_insights
except ImportError as e:
    logger.error(f"Erro ao importar módulos necessários: {e}")
    sys.exit(1)

async def testar_backend_api():
    """Testa as principais APIs do backend que apresentaram problemas"""
    try:
        print("\n🔍 Verificando cache do sistema...")
        cache = await get_cache()
        entidades = cache.get("entidades", [])
        print(f"✅ Cache carregado com {len(entidades)} entidades")
        
        # Verificando se há métricas
        entidades_com_metricas = [e for e in entidades if e.get("metricas")]
        print(f"✅ {len(entidades_com_metricas)} entidades possuem métricas")
        
        # Teste do endpoint de KPIs
        print("\n🔍 Testando endpoint /api/kpis...")
        try:
            kpis_result = await get_kpis()
            print(f"✅ Endpoint /api/kpis funcionando!")
            print(f"  - KPIs obtidos: {json.dumps(kpis_result['kpis'], indent=2)}")
        except Exception as e:
            print(f"❌ Erro no endpoint /api/kpis: {e}")
        
        # Teste do endpoint de insights
        print("\n🔍 Testando endpoint /api/insights...")
        try:
            insights_result = await get_insights()
            print(f"✅ Endpoint /api/insights funcionando!")
            print(f"  - Insights obtidos: {len(insights_result.get('insights', []))} itens")
        except Exception as e:
            print(f"❌ Erro no endpoint /api/insights: {e}")
        
        print("\n✅ Testes de backend concluídos!")
    except Exception as e:
        logger.error(f"Erro nos testes de backend: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    print("🔍 Iniciando testes do backend API...")
    asyncio.run(testar_backend_api())
