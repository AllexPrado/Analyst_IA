import requests
import json
import webbrowser
import time
import os
from datetime import datetime

# This script validates that:
# 1. The backend is running and returning real New Relic data
# 2. The data is properly formatted and contains expected fields
# 3. The frontend can access this data

# Define the base URL
base_url = 'http://localhost:8000'
frontend_url = 'http://localhost:5174'  # Adjust port if different

# Print header
print("\n" + "="*50)
print(f"Analyst_IA Validation Test - {datetime.now()}")
print("="*50)

# Test connection to backend
try:
    health = requests.get(f'{base_url}/api/health')
    print(f"Backend Connection: {'✓ OK' if health.status_code == 200 else '✗ ERROR'}")
    print(f"Status Code: {health.status_code}")
except Exception as e:
    print(f"Backend Connection: ✗ ERROR ({e})")

# Validate status endpoint (core system status)
try:
    status = requests.get(f'{base_url}/api/status')
    status_data = status.json()
    
    # Validation checks for expected fields
    validation_checks = [
        ('statusGeral' in status_data, "Status field present"),
        ('incidentesAtivos' in status_data, "Incidents field present"),
        ('disponibilidade' in status_data, "Availability field present"),
        ('totalEntidades' in status_data, "Entity count field present"),
        ('entidadesComMetricas' in status_data, "Metrics entity field present"),
        (status_data.get('totalEntidades', 0) > 0, "Has entity data"),
        (len(status_data.get('dominios', {})) > 0, "Has domain data")
    ]
    
    print("\nStatus Endpoint Validation:")
    for check, description in validation_checks:
        print(f"  {description}: {'✓ OK' if check else '✗ ERROR'}")
    
    print(f"\nEntities found: {status_data.get('totalEntidades', 0)}")
    print(f"Entities with metrics: {status_data.get('entidadesComMetricas', 0)}")
    
    domains = status_data.get('dominios', {})
    print(f"Domains found: {', '.join([f'{k}({v})' for k, v in domains.items() if k != 'entidades'])}")
    
except Exception as e:
    print(f"Status Endpoint Error: {e}")

# Validate KPIs endpoint
try:
    kpis = requests.get(f'{base_url}/api/kpis')
    kpis_data = kpis.json()
    
    print("\nKPIs Endpoint Validation:")
    print(f"  KPIs present: {'✓ OK' if 'kpis' in kpis_data else '✗ ERROR'}")
    print(f"  KPIs count: {len(kpis_data.get('kpis', []))}")
    
    for kpi in kpis_data.get('kpis', []):
        print(f"  - {kpi.get('nome')}: {kpi.get('valor')} {kpi.get('unidade')}")
    
except Exception as e:
    print(f"KPIs Endpoint Error: {e}")

# Test chat functionality with a simple question
try:
    chat = requests.post(
        f'{base_url}/chat',
        json={'pergunta': 'Quais são as aplicações com mais erros?'}
    )
    chat_data = chat.json()
    
    print("\nChat Endpoint Validation:")
    print(f"  Response present: {'✓ OK' if 'resposta' in chat_data else '✗ ERROR'}")
    print(f"  Context returned: {'✓ OK' if 'contexto' in chat_data else '✗ ERROR'}")
    print(f"  Response length: {len(chat_data.get('resposta', ''))}")
    
    # Check if response is too generic (no data)
    response_text = chat_data.get('resposta', '').lower()
    generic_phrases = ['não tenho dados', 'não foi possível', 'não há informações', 'sem dados']
    is_generic = any(phrase in response_text for phrase in generic_phrases)
    
    print(f"  Response has real data: {'✗ ERROR - Generic response' if is_generic else '✓ OK'}")
    
    # Print first 100 chars of response
    print(f"\nResponse preview: \"{chat_data.get('resposta', '')[:100]}...\"")
    
except Exception as e:
    print(f"Chat Endpoint Error: {e}")

print("\n" + "="*50)
print("Validation Complete")
print("="*50)

# Open frontend in browser if it's running
try:
    frontend_check = requests.get(frontend_url, timeout=2)
    print(f"\nFrontend appears to be running at {frontend_url}")
    print("Opening browser to validate frontend...")
    webbrowser.open(frontend_url)
except Exception:
    print(f"\nFrontend doesn't appear to be running at {frontend_url}")
    print("Please start the frontend and verify it's displaying real data.")

print("\nDone.")
