"""
Script para verificar a funcionalidade do coletor_new_relic.py
"""

import asyncio
import logging
from datetime import datetime
from tabulate import tabulate

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def teste_coletor_new_relic():
    """Testa a coleta de entidades usando o coletor_new_relic"""
    try:
        # Importar o módulo após a configuração de logging
        import os
        from dotenv import load_dotenv
        from coletor_new_relic import coletar_entidades
        
        # Carregar variáveis de ambiente
        load_dotenv()
        
        # Obter credenciais do New Relic
        api_key = os.getenv("NEW_RELIC_API_KEY")
        account_id = os.getenv("NEW_RELIC_ACCOUNT_ID")
        
        if not api_key or not account_id:
            logger.error("NEW_RELIC_API_KEY ou NEW_RELIC_ACCOUNT_ID não estão configurados nas variáveis de ambiente")
            return False
        
        # Cronometrar a operação
        inicio = datetime.now()
        logger.info(f"Iniciando teste de coleta de entidades ({inicio})")
        
        # Coletar entidades
        entidades = await coletar_entidades(api_key, account_id)
        
        # Registrar tempo de conclusão
        fim = datetime.now()
        duracao = (fim - inicio).total_seconds()
        logger.info(f"Coleta concluída em {duracao:.2f} segundos")
        
        # Validar resultados
        if not entidades:
            logger.error("Nenhuma entidade foi coletada")
            return False
        
        # Exibir resultados em formato tabular
        print("\n=== Teste de Coleta de Entidades ===")
        
        headers = ["Métrica", "Valor"]
        data = [
            ["Total de entidades", len(entidades)],
            ["Duração da coleta", f"{duracao:.2f} segundos"]
        ]
        
        print(tabulate(data, headers=headers, tablefmt="simple"))
        
        # Contagem por domínio
        dominios = {}
        for entidade in entidades:
            dominio = entidade.get("domain", "desconhecido")
            if dominio not in dominios:
                dominios[dominio] = 0
            dominios[dominio] += 1
        
        print("\n=== Entidades por Domínio ===")
        headers = ["Domínio", "Quantidade"]
        data = [[dominio, quantidade] for dominio, quantidade in dominios.items()]
        data.sort(key=lambda x: x[1], reverse=True)  # Ordenar por quantidade descendente
        
        print(tabulate(data, headers=headers, tablefmt="simple"))
        
        # Mostrar alguns exemplos de entidades
        print("\n=== Exemplos de Entidades ===")
        headers = ["Nome", "GUID", "Domínio", "Tipo"]
        data = [
            [
                entidade.get("name", "N/A"),
                entidade.get("guid", "N/A")[:8] + "...",
                entidade.get("domain", "N/A"),
                entidade.get("type", "N/A")
            ] for entidade in entidades[:5]
        ]
        
        print(tabulate(data, headers=headers, tablefmt="simple"))
        
        return len(entidades) > 0
    
    except Exception as e:
        logger.error(f"Erro ao testar coletor_new_relic: {str(e)}")
        return False

async def main():
    """Função principal"""
    sucesso = await teste_coletor_new_relic()
    
    if sucesso:
        logger.info("✓ Teste do coletor_new_relic concluído com sucesso")
    else:
        logger.error("✗ Teste do coletor_new_relic falhou")

if __name__ == "__main__":
    asyncio.run(main())
