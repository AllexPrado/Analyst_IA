
import requests
import json

# Define the base URL
base_url = 'http://localhost:8000'

# Test the status endpoint
try:
    response = requests.get(f'{base_url}/api/status')
    print(f'Status endpoint: {response.status_code}')
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f'Error with status endpoint: {e}')

# Test the KPIs endpoint
try:
    response = requests.get(f'{base_url}/api/kpis')
    print(f'KPIs endpoint: {response.status_code}')
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f'Error with KPIs endpoint: {e}')

# Test the chat endpoint
try:
    response = requests.post(
        f'{base_url}/chat',
        json={'pergunta': 'Olá'}
    )
    print(f'Chat endpoint: {response.status_code}')
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f'Error with chat endpoint: {e}')

