#!/usr/bin/env python
"""
Script para corrigir o roteamento do Agno
"""
import os
import sys
import re

# Caminho do arquivo principal
MAIN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py')

def corrigir_agno_router():
    """
    Corrige o router do Agno no arquivo main.py
    """
    print(f"Verificando arquivo {MAIN_FILE}...")
    
    try:
        # Ler o conteúdo do arquivo
        with open(MAIN_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Procurar pelo padrão de inclusão do router
        if "app.include_router(agno_router, prefix=\"/agno\"" in content:
            print("✅ O router Agno já está incluído diretamente no app.")
        else:
            print("❌ Router Agno não está incluído diretamente. Corrigindo...")
            
            # Substituir a seção de importação do agno_router
            novo_conteudo = re.sub(
                r"# Incluir os endpoints inteligentes do Agno.*?from routers\.agno_router import router as agno_router",
                "# Incluir os endpoints inteligentes do Agno\nfrom routers.agno_router import router as agno_router",
                content,
                flags=re.DOTALL
            )
            
            # Substituir a seção de inclusão do router
            novo_conteudo = re.sub(
                r"# Incluir os endpoints inteligentes do Agno diretamente.*?logger\.error\(f\"\[ERRO\] Falha ao registrar endpoints do Agno: {str\(e\)}\"\)",
                """# Incluir os endpoints inteligentes do Agno diretamente no app
# Nota: Incluímos o router diretamente sem try/except para mostrar qualquer erro
app.include_router(agno_router, prefix="/agno", tags=["Agno IA"])
logger.info("[AGNO] Endpoints inteligentes do Agno IA disponíveis em /agno")

# Registrar também no api_router para manter compatibilidade com /api/agno
api_router.include_router(agno_router, prefix="/agno", tags=["Agno IA via API"])
logger.info("[AGNO] Endpoints inteligentes do Agno IA também disponíveis em /api/agno")""",
                novo_conteudo,
                flags=re.DOTALL
            )
            
            # Salvar o arquivo modificado
            with open(MAIN_FILE, 'w', encoding='utf-8') as f:
                f.write(novo_conteudo)
            
            print("✅ Arquivo corrigido com sucesso!")
            return True
            
        return False
    
    except Exception as e:
        print(f"❌ Erro ao tentar corrigir o arquivo: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== CORREÇÃO DE ROTEAMENTO DO AGNO ===")
    
    if corrigir_agno_router():
        print("\n✅ Configuração do router corrigida!")
        print("\nPara aplicar as alterações:")
        print("1. Reinicie o servidor FastAPI:")
        print("   python -m uvicorn main:app --reload")
        print("\n2. Teste o endpoint com:")
        print("   python teste_simples_agno.py")
    else:
        print("\n⚠️ Nenhuma alteração foi necessária ou não foi possível corrigir.")
        print("Por favor, verifique manualmente o arquivo main.py")
