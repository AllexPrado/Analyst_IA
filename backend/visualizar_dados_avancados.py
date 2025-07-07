import requests
import json

guid = "Mzg4MjgyMHxBUE18QVBQTElDQVRJT058NTkwNzU1NjAy"
url = f"http://localhost:8000/api/entidade/{guid}/dados_avancados"

resp = requests.get(url)
resp.raise_for_status()
print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
