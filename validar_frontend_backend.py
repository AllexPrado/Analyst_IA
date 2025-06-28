#!/usr/bin/env python3
"""
Valida a conexão entre o frontend e o backend,
verificando todos os endpoints cruciais.
"""

import requests
import json
import time
import sys
import logging
from rich.console import Console
from rich.table import Table
from rich import print as rprint

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
console = Console()

# Backend URL
BACKEND_URL = "http://localhost:8000"

# Endpoints to check
ENDPOINTS = [
    {"path": "/api/health", "method": "GET", "name": "Health Check"},
    {"path": "/api/status", "method": "GET", "name": "Status"},
    {"path": "/api/kpis", "method": "GET", "name": "KPIs"},
    {"path": "/api/entidades", "method": "GET", "name": "Entidades"},
    {"path": "/api/cobertura", "method": "GET", "name": "Cobertura"},
    {"path": "/api/tendencias", "method": "GET", "name": "Tendencias"},
    {"path": "/api/insights", "method": "GET", "name": "Insights"},
    {"path": "/api/chat", "method": "POST", "name": "Chat", "json": {"message": "Teste de endpoint"}}
]

def test_endpoint(endpoint):
    """Test a specific endpoint and return the result"""
    url = f"{BACKEND_URL}{endpoint['path']}"
    method = endpoint["method"]
    name = endpoint["name"]
    
    try:
        if method == "GET":
            start_time = time.time()
            response = requests.get(url, timeout=10)
            elapsed = time.time() - start_time
        elif method == "POST":
            json_data = endpoint.get("json", {})
            start_time = time.time()
            response = requests.post(url, json=json_data, timeout=10)
            elapsed = time.time() - start_time
        
        status_code = response.status_code
        
        # Check if the response is valid JSON
        try:
            response_json = response.json()
            json_valid = True
            if method == "GET":
                data_size = len(json.dumps(response_json))
            else:
                data_size = len(response.text)
        except:
            json_valid = False
            data_size = len(response.text)
            response_json = {}
        
        return {
            "name": name,
            "status_code": status_code,
            "success": 200 <= status_code < 300,
            "elapsed": elapsed,
            "json_valid": json_valid,
            "data_size": data_size,
            "data": response_json
        }
    except Exception as e:
        return {
            "name": name,
            "status_code": 0,
            "success": False,
            "error": str(e),
            "json_valid": False,
            "data_size": 0,
            "data": {}
        }

def main():
    """Test all endpoints and display results"""
    console.print("[bold blue]Testando conexão entre frontend e backend[/]")
    console.print(f"Backend URL: [cyan]{BACKEND_URL}[/]")
    console.print("Testando endpoints...")
    
    # Create results table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Endpoint", style="dim")
    table.add_column("Status", justify="center")
    table.add_column("Tempo (s)", justify="right")
    table.add_column("Tamanho", justify="right")
    table.add_column("Detalhes", justify="left")
    
    all_success = True
    results = []
    
    # Test each endpoint
    for endpoint in ENDPOINTS:
        console.print(f"Testando [cyan]{endpoint['name']}[/] ({endpoint['path']})...", end="")
        result = test_endpoint(endpoint)
        results.append(result)
        
        status_style = "green" if result["success"] else "red bold"
        status_text = f"[{status_style}]{result['status_code']} {'✓' if result['success'] else '✗'}[/]"
        
        # Format time
        if 'elapsed' in result:
            time_text = f"{result['elapsed']:.2f}s"
            if result['elapsed'] > 1.0:
                time_style = "yellow"
            elif result['elapsed'] > 2.0:
                time_style = "red"
            else:
                time_style = "green"
            time_text = f"[{time_style}]{time_text}[/]"
        else:
            time_text = "[red]N/A[/]"
        
        # Format data size
        if result['data_size'] > 0:
            if result['data_size'] < 1024:
                size_text = f"{result['data_size']} B"
            else:
                size_text = f"{result['data_size'] / 1024:.1f} KB"
        else:
            size_text = "N/A"
        
        # Details
        details = ""
        if not result["success"]:
            details = result.get("error", "Erro desconhecido")
            all_success = False
        elif "data" in result and isinstance(result["data"], dict):
            # Extract useful information based on endpoint
            if endpoint["path"] == "/api/health":
                if "status" in result["data"]:
                    details = f"Status: {result['data']['status']}"
            elif endpoint["path"] == "/api/entidades":
                if isinstance(result["data"], list):
                    details = f"{len(result['data'])} entidades"
                elif "entidades" in result["data"] and isinstance(result["data"]["entidades"], list):
                    details = f"{len(result['data']['entidades'])} entidades"
            elif endpoint["path"] == "/api/chat":
                if "message" in result["data"]:
                    message = result["data"]["message"]
                    details = f"Resposta: {message[:30]}..." if len(message) > 30 else message
        
        table.add_row(endpoint["name"], status_text, time_text, size_text, details)
        
        if result["success"]:
            console.print(" [green]OK[/]")
        else:
            console.print(f" [red bold]FALHA[/] - {result.get('error', 'Erro desconhecido')}")
    
    console.print("\n[bold]Resultados detalhados:[/]")
    console.print(table)
    
    # Overall status
    if all_success:
        console.print("\n[green bold]✓ Todos os endpoints estão funcionando corretamente![/]")
        console.print("[blue]Frontend pode se conectar ao backend sem problemas.[/]")
    else:
        console.print("\n[red bold]✗ Alguns endpoints apresentaram falhas![/]")
        console.print("[yellow]Problemas de conexão entre frontend e backend foram detectados.[/]")
        
        # Specific advice for common issues
        failing_endpoints = [r for r in results if not r["success"]]
        if any(r["name"] == "Chat" for r in failing_endpoints):
            console.print("\n[yellow bold]Problema no endpoint de chat detectado:[/]")
            console.print("- Verifique se o parametro 'temperatura' não está sendo passado para gerar_resposta_ia()")
            console.print("- Confirme que o OpenAI API Key está configurado corretamente")
        
        if any(r["name"] == "Health Check" for r in failing_endpoints):
            console.print("\n[yellow bold]Endpoint de saúde não encontrado:[/]")
            console.print("- Verifique se o endpoint /api/health está implementado no backend")
        
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
