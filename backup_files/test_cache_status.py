import asyncio
from utils.cache import get_cache, diagnosticar_cache

async def verificar_cache():
    # Obtém o cache atual
    cache = await get_cache()
    
    # Verifica as entidades consolidadas
    entidades = cache.get("entidades", [])
    
    print(f"== Status do Cache ==")
    print(f"Total de entidades consolidadas: {len(entidades)}")
    print(f"Chaves no cache: {list(cache.keys())}")
    
    # Verifica diagnóstico
    diagnostico = diagnosticar_cache()
    print("\n== Diagnóstico ==")
    print(f"Status: {diagnostico.get('status')}")
    print(f"Última atualização: {diagnostico.get('ultima_atualizacao')}")
    
    # Se houver entidades por domínio, listar
    if "contagem_por_dominio" in diagnostico:
        print("\n== Entidades por domínio ==")
        for dominio, contagem in diagnostico["contagem_por_dominio"].items():
            print(f"{dominio}: {contagem}")
    
    # Verifica GUIDs das entidades consolidadas
    if entidades:
        guids = set()
        for entidade in entidades:
            guid = entidade.get("guid")
            if guid:
                guids.add(guid)
        
        print(f"\nTotal de GUIDs únicos: {len(guids)}")

if __name__ == "__main__":
    asyncio.run(verificar_cache())
