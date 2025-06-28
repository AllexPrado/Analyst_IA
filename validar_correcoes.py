"""
Script para validar todas as correções de backend e qualidade de dados
"""

import asyncio
import logging
import sys
from pathlib import Path
import time
import importlib

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Adiciona pasta atual ao path para importar módulos locais
sys.path.append(str(Path(__file__).parent))

async def executar_testes():
    """
    Executa todos os testes do backend para validar correções
    """
    try:
        print("\n" + "="*80)
        print(" 🧪 VALIDAÇÃO DE CORREÇÕES DO BACKEND E QUALIDADE DE DADOS")
        print("="*80)
        
        testes = [
            "test_data_quality",
            "test_chat",
            "test_backend_simple",
            "test_frontend_data"
        ]
        
        resultados = {}
        
        for teste in testes:
            print(f"\n\n{'='*50}")
            print(f" 🧪 Executando {teste}...")
            print(f"{'='*50}\n")
            
            try:
                # Importa dinamicamente o módulo de teste
                modulo = importlib.import_module(teste)
                
                # Identifica a função principal do teste
                if hasattr(modulo, "testar_qualidade_dados"):
                    resultado = await modulo.testar_qualidade_dados()
                elif hasattr(modulo, "testar_chat"):
                    resultado = await modulo.testar_chat()
                elif hasattr(modulo, "main"):
                    resultado = await modulo.main()
                else:
                    print(f"❌ Erro: Função principal não encontrada no módulo {teste}")
                    resultado = False
                
                resultados[teste] = resultado
                
            except Exception as e:
                logger.error(f"Erro ao executar teste {teste}: {e}", exc_info=True)
                print(f"❌ Erro ao executar {teste}: {str(e)}")
                resultados[teste] = False
            
            # Pequena pausa entre testes
            time.sleep(1)
        
        # Resumo dos resultados
        print("\n\n" + "="*80)
        print(" 📊 RESUMO DOS RESULTADOS")
        print("="*80)
        
        total = len(resultados)
        sucesso = sum(1 for resultado in resultados.values() if resultado)
        
        for teste, resultado in resultados.items():
            status = "✅ SUCESSO" if resultado else "❌ FALHA"
            print(f"- {teste}: {status}")
        
        print("\n" + "="*80)
        
        if sucesso == total:
            print(f" ✅ TODOS OS {total} TESTES PASSARAM COM SUCESSO")
        else:
            print(f" ⚠️ {sucesso}/{total} TESTES PASSARAM")
            
        print("="*80)
        
    except Exception as e:
        logger.error(f"Erro ao executar bateria de testes: {e}", exc_info=True)
        print(f"\n❌ ERRO GERAL DE EXECUÇÃO: {str(e)}")
        return False
    
    return sucesso == total

if __name__ == "__main__":
    asyncio.run(executar_testes())
