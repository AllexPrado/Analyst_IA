import requests
import json

# Define the chat endpoint URL
url = "http://localhost:8000/api/chat"

# Define the request payload
payload = {
    "pergunta": "Como está o desempenho do sistema?"
}

try:
    # Send the POST request
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    
    # Print the results
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
