"""
Test script that launches the server and tests the endpoints
"""
import subprocess
import time
import sys
import requests
import json

def test_endpoints():
    """Test the Agno endpoints"""
    print("\n\n===== TESTING ENDPOINTS =====\n")
    endpoints = {
        "/agno/corrigir": {"entidade": "sistema_backend", "acao": "verificar"},
        "/agno/playbook": {"nome": "diagnostico", "contexto": {}},
        "/agno/feedback": {"feedback": {"tipo": "verificacao", "valor": "ok"}},
        "/agno/coletar_newrelic": {"tipo": "entidades"}
    }
    
    base_url = "http://localhost:8000"
    success = 0
    failure = 0
    
    for endpoint, payload in endpoints.items():
        full_url = f"{base_url}{endpoint}"
        print(f"\nTesting: {endpoint}")
        print(f"URL: {full_url}")
        print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
        
        try:
            response = requests.post(full_url, json=payload)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 404:
                print(f"ERROR: Endpoint not found (404)")
                failure += 1
            elif response.status_code >= 400:
                print(f"ERROR: Request failed with status {response.status_code}")
                print(f"Response: {response.text}")
                failure += 1
            else:
                print(f"SUCCESS: Request completed with status {response.status_code}")
                try:
                    print(f"Response: {json.dumps(response.json(), ensure_ascii=False, indent=2)[:300]}...")
                except:
                    print(f"Response: {response.text[:300]}...")
                success += 1
        except Exception as e:
            print(f"EXCEPTION: {str(e)}")
            failure += 1
    
    print(f"\nResults: {success} successful, {failure} failed out of {len(endpoints)} total endpoints")
    return success, failure

def run_command(command):
    """Run a command and return the output"""
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        return result.stdout, result.stderr
    except Exception as e:
        return "", str(e)

if __name__ == "__main__":
    # Step 1: Print system info
    print("===== SYSTEM INFORMATION =====")
    print(f"Python version: {sys.version}")
    stdout, stderr = run_command("pip list | findstr fastapi")
    print(f"FastAPI version: {stdout.strip()}")
    
    # Step 2: Start the server in the background
    print("\n===== STARTING SERVER =====")
    server_process = subprocess.Popen(
        ["python", "d:/projetos/Analyst_IA/backend/main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Step 3: Wait for server to start
    print("Waiting for server to start...")
    time.sleep(5)  # Give the server time to start
    
    # Step 4: Test if server is running
    try:
        response = requests.get("http://localhost:8000/docs")
        if response.status_code == 200:
            print("Server started successfully!")
        else:
            print(f"Server returned status code {response.status_code}")
    except Exception as e:
        print(f"Error connecting to server: {str(e)}")
    
    # Step 5: Test the endpoints
    try:
        test_endpoints()
    except Exception as e:
        print(f"Error testing endpoints: {str(e)}")
    
    # Step 6: Terminate the server
    print("\n===== TERMINATING SERVER =====")
    server_process.terminate()
    
    # Step 7: Wait for server to terminate and print output
    try:
        stdout, stderr = server_process.communicate(timeout=5)
        print("\n===== SERVER OUTPUT =====")
        print("STDOUT:")
        print(stdout[:1000])  # Print first 1000 characters of stdout
        
        if stderr:
            print("\nSTDERR:")
            print(stderr[:1000])  # Print first 1000 characters of stderr
    except Exception as e:
        print(f"Error getting server output: {str(e)}")
        
    print("\n===== TEST COMPLETED =====")
