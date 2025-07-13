"""
Script para testar componentes importantes do backend sem iniciar o servidor completo.
"""
import os
import sys
import json
import importlib
import logging
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

def test_imports():
    """Testa importações de módulos críticos"""
    modules = [
        "fastapi",
        "uvicorn",
        "core_router",
        "check_and_fix_cache"
    ]
    
    results = {}
    
    for module in modules:
        try:
            if module in sys.modules:
                # Recarregar se já importado
                importlib.reload(sys.modules[module])
                mod = sys.modules[module]
            else:
                mod = importlib.import_module(module)
            
            logger.info(f"✅ Módulo {module} importado com sucesso")
            results[module] = {"success": True, "error": None}
            
            # Verificações adicionais para módulos específicos
            if module == "check_and_fix_cache":
                if hasattr(mod, "check_and_fix"):
                    logger.info("✅ Função check_and_fix encontrada em check_and_fix_cache")
                else:
                    logger.warning("⚠️ Função check_and_fix NÃO encontrada em check_and_fix_cache")
                    results[module]["warning"] = "Função check_and_fix não encontrada"
            
        except ImportError as e:
            logger.error(f"❌ Erro ao importar {module}: {e}")
            results[module] = {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao importar {module}: {e}")
            results[module] = {"success": False, "error": str(e)}
    
    return results

def test_agent_tools():
    """Testa a importação e funcionalidade do módulo agent_tools"""
    try:
        from core_inteligente import agent_tools
        logger.info("✅ Módulo agent_tools importado com sucesso")
        
        # Verificar classes específicas
        classes = [
            "NRQLQueryCorrector",
            "CodeValidationTool"
        ]
        
        for class_name in classes:
            if hasattr(agent_tools, class_name):
                logger.info(f"✅ Classe {class_name} encontrada em agent_tools")
                
                # Tentar instanciar
                try:
                    class_obj = getattr(agent_tools, class_name)
                    instance = class_obj()
                    logger.info(f"✅ Classe {class_name} instanciada com sucesso")
                except Exception as e:
                    logger.warning(f"⚠️ Não foi possível instanciar {class_name}: {e}")
            else:
                logger.warning(f"⚠️ Classe {class_name} NÃO encontrada em agent_tools")
        
        return {"success": True, "error": None}
        
    except ImportError as e:
        logger.error(f"❌ Erro ao importar agent_tools: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"❌ Erro inesperado ao testar agent_tools: {e}")
        return {"success": False, "error": str(e)}

def test_cache_functionality():
    """Testa a funcionalidade básica do cache"""
    try:
        import check_and_fix_cache
        
        # Testar a função check_and_fix
        if hasattr(check_and_fix_cache, "check_and_fix"):
            logger.info("Testando função check_and_fix...")
            
            # Criar um arquivo de cache de teste
            base_dir = Path(__file__).parent
            test_dir = base_dir / "tests"
            test_dir.mkdir(exist_ok=True)
            
            test_cache_file = test_dir / "test_cache.json"
            
            # Criar um cache de teste
            test_data = {
                "timestamp": "2023-07-12T12:00:00Z",
                "entidades": [
                    {"name": "Entidade Teste", "type": "APPLICATION"}
                ]
            }
            
            with open(test_cache_file, "w", encoding="utf-8") as f:
                json.dump(test_data, f)
            
            # Executar check_and_fix no arquivo de teste
            result = check_and_fix_cache.check_and_fix(test_cache_file)
            
            # Verificar resultado
            if result:
                logger.info("✅ Função check_and_fix executada com sucesso")
                return {"success": True, "error": None}
            else:
                logger.warning("⚠️ Função check_and_fix retornou False")
                return {"success": False, "error": "check_and_fix retornou False"}
        else:
            logger.warning("⚠️ Função check_and_fix NÃO encontrada no módulo")
            return {"success": False, "error": "Função check_and_fix não encontrada"}
            
    except Exception as e:
        logger.error(f"❌ Erro ao testar funcionalidade do cache: {e}")
        return {"success": False, "error": str(e)}

def main():
    """Função principal"""
    logger.info("=" * 80)
    logger.info("TESTANDO COMPONENTES DO BACKEND ANALYST IA")
    logger.info("=" * 80)
    
    # Testar importações
    logger.info("\n--- Teste de importações de módulos ---")
    import_results = test_imports()
    
    # Testar agent_tools
    logger.info("\n--- Teste do módulo agent_tools ---")
    agent_tools_result = test_agent_tools()
    
    # Testar funcionalidade do cache
    logger.info("\n--- Teste de funcionalidade do cache ---")
    cache_result = test_cache_functionality()
    
    # Resumo dos resultados
    logger.info("\n--- RESUMO DOS TESTES ---")
    logger.info(f"Importações de módulos: {'✅ OK' if all(r['success'] for r in import_results.values()) else '❌ FALHA'}")
    logger.info(f"Módulo agent_tools: {'✅ OK' if agent_tools_result['success'] else '❌ FALHA'}")
    logger.info(f"Funcionalidade do cache: {'✅ OK' if cache_result['success'] else '❌ FALHA'}")
    
    overall_success = all(r['success'] for r in import_results.values()) and agent_tools_result['success'] and cache_result['success']
    
    logger.info("=" * 80)
    logger.info(f"RESULTADO FINAL: {'✅ TODOS OS TESTES PASSARAM' if overall_success else '❌ ALGUNS TESTES FALHARAM'}")
    logger.info("=" * 80)
    
    return overall_success

if __name__ == "__main__":
    try:
        success = main()
        if success:
            logger.info("O backend está pronto para iniciar!")
            sys.exit(0)
        else:
            logger.warning("Ainda existem problemas a serem resolvidos antes de iniciar o backend.")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operação interrompida pelo usuário")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Erro não tratado: {e}")
        sys.exit(1)
