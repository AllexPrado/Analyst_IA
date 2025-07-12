#!/usr/bin/env python
"""
Script super básico para testar o endpoint usando curl via subprocess
"""
import subprocess
import sys
import os

def main():
    print("\n=== TESTE BÁSICO DO ENDPOINT /agno/corrigir ===\n")
    
    # Comando para testar o endpoint usando curl
    cmd = 'curl -X POST -H "Content-Type: application/json" -d "{\"entidade\":\"teste\",\"acao\":\"verificar\"}" http://localhost:8000/agno/corrigir'
    
    print(f"Executando comando: {cmd}\n")
    
    try:
        # Executar o comando curl
        resultado = subprocess.run(
            cmd, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        
        # Mostrar resultados
        if resultado.returncode == 0:
            print("Resposta do servidor:")
            print("=" * 50)
            print(resultado.stdout)
            print("=" * 50)
            
            # Verificar se recebemos uma resposta JSON válida e não um erro 404
            if "Not Found" in resultado.stdout or "404" in resultado.stdout:
                print("\n❌ ERRO: Endpoint retornou 404 Not Found!")
                print("O endpoint /agno/corrigir ainda não está funcionando corretamente.")
                return 1
            else:
                print("\n✅ SUCESSO! O endpoint /agno/corrigir está funcionando!")
                return 0
        else:
            print("\n❌ ERRO ao executar o comando:")
            print(resultado.stderr)
            return 1
        
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
