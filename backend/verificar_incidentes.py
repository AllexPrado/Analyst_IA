import asyncio
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Adicionar o diretório atual ao path para importações
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.cache import get_cache

async def verificar_dados_incidentes():
    try:
        print("Verificando dados de incidentes e alertas no cache...")
        cache = await get_cache()
        
        # Verificar alertas
        alertas = cache.get("alertas", [])
        print(f"\nAlertas no cache: {len(alertas)}")
        if alertas:
            print("Primeiros 3 alertas:")
            for i, alerta in enumerate(alertas[:3]):
                print(f"  {i+1}. {alerta.get('name', 'Sem nome')} - {alerta.get('severity', 'Sem severidade')}")
        
        # Verificar se existe chave "incidentes"
        if "incidentes" in cache:
            incidentes = cache["incidentes"]
            print(f"\nIncidentes no cache: {len(incidentes) if isinstance(incidentes, list) else 'Não é uma lista'}")
            if isinstance(incidentes, list) and incidentes:
                print("Primeiros 3 incidentes:")
                for i, incidente in enumerate(incidentes[:3]):
                    print(f"  {i+1}. {incidente.get('title', 'Sem título')} - {incidente.get('state', 'Sem estado')}")
        else:
            print("\nNão existe a chave 'incidentes' no cache.")
            
        # Verificar se há alguma chave relacionada a incidentes
        related_keys = [key for key in cache.keys() if 'incidente' in key.lower() or 'alert' in key.lower()]
        if related_keys:
            print(f"\nChaves relacionadas encontradas: {related_keys}")
        
        # Verificar informações sobre a última semana
        print("\nVerificando dados da última semana...")
        encontrou_dados_semana = False
        for key, value in cache.items():
            if isinstance(value, dict) and '7d' in value:
                print(f"  Encontrados dados de 7 dias em: {key}")
                encontrou_dados_semana = True
            elif isinstance(value, list) and any(isinstance(item, dict) and '7d' in item for item in value):
                print(f"  Encontrados dados de 7 dias em itens de: {key}")
                encontrou_dados_semana = True
                
        if not encontrou_dados_semana:
            print("  Não foram encontrados dados específicos da última semana.")
            
        # Salvar diagnóstico para análise futura
        relatorio = {
            "timestamp": datetime.now().isoformat(),
            "total_alertas": len(alertas),
            "incidentes_encontrados": "incidentes" in cache,
            "chaves_relacionadas": related_keys,
            "dados_ultima_semana_encontrados": encontrou_dados_semana,
            "chaves_no_cache": list(cache.keys())
        }
        
        Path("historico").mkdir(exist_ok=True)
        relatorio_path = Path("historico") / f"verificacao_incidentes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(relatorio_path, "w", encoding="utf-8") as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False)
            
        print(f"\nRelatório salvo em: {relatorio_path}")
        
    except Exception as e:
        print(f"Erro ao verificar dados: {e}")
        
if __name__ == "__main__":
    asyncio.run(verificar_dados_incidentes())
