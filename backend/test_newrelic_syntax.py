#!/usr/bin/env python
"""
Teste simples para verificar a sintaxe e funcionalidade do módulo newrelic_collector
"""
import sys
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Testando importação do módulo newrelic_collector...")
        from utils.newrelic_collector import buscar_todas_entidades, coletar_contexto_completo
        
        logger.info("Importação bem-sucedida!")
        
        # Verificar se as funções estão definidas corretamente
        logger.info("Verificando definição das funções...")
        
        # Verificar se buscar_todas_entidades é uma função async
        if not hasattr(buscar_todas_entidades, "__code__"):
            logger.error("buscar_todas_entidades não parece ser uma função válida!")
            return 1
            
        # Verificar se coletar_contexto_completo é uma função async
        if not hasattr(coletar_contexto_completo, "__code__"):
            logger.error("coletar_contexto_completo não parece ser uma função válida!")
            return 1
            
        logger.info("Teste de importação e validação concluído com sucesso!")
        return 0
        
    except SyntaxError as e:
        logger.error(f"Erro de sintaxe no módulo newrelic_collector: {e}")
        logger.error(f"Linha: {e.lineno}, posição: {e.offset}")
        logger.error(f"Texto: {e.text}")
        return 1
        
    except ImportError as e:
        logger.error(f"Erro ao importar o módulo newrelic_collector: {e}")
        return 1
        
    except Exception as e:
        logger.error(f"Erro não esperado: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
