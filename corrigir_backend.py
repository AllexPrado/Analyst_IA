#!/usr/bin/env python3
"""
Script para corrigir erros específicos no backend do Analyst-IA
"""

import os
import sys
import re
import shutil
from pathlib import Path

def print_header(message):
    """Imprime uma mensagem de cabeçalho formatada"""
    print("\n" + "=" * 80)
    print(f" {message} ".center(80, "="))
    print("=" * 80)

def find_and_fix_truncate_text_tokens():
    """Procura e corrige o erro de importação truncate_text_tokens"""
    print_header("Corrigindo erro de importação truncate_text_tokens")
    
    # Caminhos de arquivos relevantes
    unified_backend_path = Path("backend/unified_backend.py")
    
    if not unified_backend_path.exists():
        print(f"✗ Arquivo {unified_backend_path} não encontrado")
        return False
    
    # Faz backup do arquivo
    backup_path = unified_backend_path.with_suffix(".py.bak")
    shutil.copy2(unified_backend_path, backup_path)
    print(f"✓ Backup criado: {backup_path}")
    
    # Lê o conteúdo do arquivo
    with open(unified_backend_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verifica se o erro está presente
    if "truncate_text_tokens" in content:
        # Corrige o erro
        fixed_content = re.sub(
            r"from utils\.openai_connector import gerar_resposta_ia,\s*truncate_text_tokens",
            "from utils.openai_connector import gerar_resposta_ia",
            content
        )
        
        # Se houve alteração, salva o arquivo
        if fixed_content != content:
            with open(unified_backend_path, "w", encoding="utf-8") as f:
                f.write(fixed_content)
            print(f"✓ Correção aplicada: removida importação de truncate_text_tokens em {unified_backend_path}")
            return True
        else:
            print(f"✗ Padrão encontrado, mas substituição não foi efetiva em {unified_backend_path}")
            return False
    else:
        print(f"✓ Nenhum problema de importação truncate_text_tokens encontrado em {unified_backend_path}")
        return True

def find_and_fix_api_health():
    """Verifica e implementa o endpoint /api/health se necessário"""
    print_header("Verificando endpoint /api/health")
    
    unified_backend_path = Path("backend/unified_backend.py")
    
    if not unified_backend_path.exists():
        print(f"✗ Arquivo {unified_backend_path} não encontrado")
        return False
    
    # Lê o conteúdo do arquivo
    with open(unified_backend_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verifica se o endpoint já existe
    if "@app.get(\"/api/health\")" in content or "@router.get(\"/health\")" in content:
        print("✓ Endpoint /api/health já implementado")
        return True
    
    # Busca por linha onde implementar o endpoint
    # Geralmente após outros endpoints ou antes do bloco if __name__ == "__main__"
    match = re.search(r"@app.get\(\"/api/[^\"]+\"\)[^\n]+\ndef [^:]+:", content)
    
    if match:
        # Faz backup do arquivo
        backup_path = unified_backend_path.with_suffix(".py.bak2")
        shutil.copy2(unified_backend_path, backup_path)
        print(f"✓ Backup criado: {backup_path}")
        
        # Posição para inserir o novo endpoint (antes do trecho encontrado)
        insert_pos = match.start()
        
        # Implementação do endpoint /api/health
        health_endpoint = """
@app.get("/api/health", status_code=status.HTTP_200_OK)
async def health_check():
    # Endpoint de verificação de saúde para monitoramento
    return {"status": "online", "timestamp": datetime.now().isoformat()}

"""
        
        # Insere o novo endpoint
        new_content = content[:insert_pos] + health_endpoint + content[insert_pos:]
        
        # Salva o arquivo
        with open(unified_backend_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        print(f"✓ Endpoint /api/health implementado em {unified_backend_path}")
        return True
    else:
        print(f"✗ Não foi possível encontrar um local adequado para implementar o endpoint /api/health em {unified_backend_path}")
        return False

def main():
    """Função principal"""
    print_header("Corrigindo Erros Específicos do Backend")
    
    # Lista de correções a serem aplicadas
    fixes = [
        ("Erro de importação truncate_text_tokens", find_and_fix_truncate_text_tokens),
        ("Implementação do endpoint /api/health", find_and_fix_api_health),
    ]
    
    # Aplica cada correção
    results = []
    for name, fix_func in fixes:
        print(f"\nTentando correção: {name}")
        try:
            result = fix_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ Erro ao aplicar correção {name}: {e}")
            results.append((name, False))
    
    # Exibe resumo
    print_header("Resumo das Correções")
    
    successful_fixes = 0
    for name, result in results:
        status = "✓ Sucesso" if result else "✗ Falha"
        print(f"{status}: {name}")
        if result:
            successful_fixes += 1
    
    if successful_fixes == len(fixes):
        print("\n✓ Todas as correções foram aplicadas com sucesso!")
        print("Execute 'python reiniciar_sistema.py' para reiniciar o sistema com as correções.")
        return 0
    else:
        print(f"\n✗ {len(fixes) - successful_fixes} de {len(fixes)} correções falharam.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
