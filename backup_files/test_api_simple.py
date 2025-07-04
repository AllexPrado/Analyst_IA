import requests
import json
import subprocess
import time

# First, make sure the server is running
try:
    # Test health endpoint first
    health_response = requests.get("http://localhost:8000/api/health")
    print(f"Health endpoint status: {health_response.status_code}")
    print(f"Health response: {health_response.text}")

    # Define the chat endpoint URL
    url = "http://localhost:8000/api/chat"

    # Define the request payload
    payload = {
        "pergunta": "Como está o desempenho do sistema?"
    }

    # Send the POST request
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    
    # Print the results
    print(f"\nChat endpoint status: {response.status_code}")
    print(f"Chat response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
