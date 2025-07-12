import requests
import sys

def check_endpoint(url):
    try:
        print(f"Checking {url}...")
        response = requests.get(url, timeout=5)
        print(f"Status code: {response.status_code}")
        return response.status_code
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    print(f"Python version: {sys.version}")
    print("Testing FastAPI endpoints...")
    
    # Test basic connectivity
    check_endpoint("http://localhost:8000/docs")
    
    # Test Agno endpoints
    check_endpoint("http://localhost:8000/agno/corrigir")
    
    print("Test complete.")
