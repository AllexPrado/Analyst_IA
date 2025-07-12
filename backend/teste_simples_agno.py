#!/usr/bin/env python
"""
Teste extremamente simples do endpoint /agno/corrigir
Esse script verifica apenas se o endpoint está acessível
"""
import requests
import json
import sys
import logging
import os

# Configure logging to file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='teste_agno_endpoint.log',
    filemode='w'
)
logger = logging.getLogger(__name__)

def test_agno_corrigir():
    # Open a file for output
    with open('resultado_teste_agno.txt', 'w') as f:
        f.write("Iniciando teste do endpoint /agno/corrigir\n")
    
    # URL do endpoint que estava com problema
    url = "http://localhost:8000/agno/corrigir"
    
    # Dados para enviar
    payload = {
        "entidade": "teste",
        "acao": "verificar"
    }
    
    print("\n============================================================")
    print("TESTE SIMPLES DO ENDPOINT /agno/corrigir")
    print("============================================================\n")
    
    print(f"Fazendo requisição POST para: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("\nResultado:")
    
    try:
        # Fazer a requisição
        logger.debug(f"Iniciando requisição para {url}")
        with open('resultado_teste_agno.txt', 'a') as f:
            f.write(f"Tentando requisição para: {url}\n")
        
        response = requests.post(url, json=payload, timeout=10)
        logger.debug(f"Resposta recebida: Status {response.status_code}")
        
        # Salvar resultado em arquivo
        with open('resultado_teste_agno.txt', 'a') as f:
            f.write(f"Status Code: {response.status_code}\n")
            f.write(f"Resposta: {response.text[:1000]}\n")
        
        # Mostrar resultados
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("SUCESSO! O endpoint está funcionando corretamente.")
            print("\nResposta:")
            try:
                resp_json = response.json()
                print(json.dumps(resp_json, indent=2))
                with open('resultado_teste_agno.txt', 'a') as f:
                    f.write(f"JSON Response: {json.dumps(resp_json)}\n")
            except:
                print(response.text[:500])
            return True
        else:
            print(f"ERRO! Status code: {response.status_code}")
            print(f"Resposta: {response.text}")
            
            # Teste adicional com /api/agno/corrigir para comparação
            api_url = "http://localhost:8000/api/agno/corrigir"
            print(f"\nTentando endpoint alternativo: {api_url}")
            api_response = requests.post(api_url, json=payload, timeout=10)
            print(f"Status do endpoint alternativo: {api_response.status_code}")
            if api_response.status_code == 200:
                print("ENDPOINT ALTERNATIVO FUNCIONOU!")
                print(f"Resposta: {json.dumps(api_response.json(), indent=2)}")
            
            return False
    
    except requests.exceptions.ConnectionError as e:
        print("ERRO DE CONEXÃO! Não foi possível conectar ao servidor.")
        print("Verifique se o servidor está rodando na porta 8000.")
        logger.error(f"Erro de conexão: {e}")
        return False
    
    except Exception as e:
        print(f"ERRO: {str(e)}")
        logger.error(f"Exceção não tratada: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    success = test_agno_corrigir()
    sys.exit(0 if success else 1)
