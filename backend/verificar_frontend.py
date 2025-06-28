import os
import sys
import json
import requests
from pathlib import Path

# Verificar diretório do frontend
FRONTEND_DIR = Path("d:/projetos/Analyst_IA/frontend")
if not FRONTEND_DIR.exists():
    print(f"Diretório do frontend não encontrado: {FRONTEND_DIR}")
    sys.exit(1)

def verificar_apis():
    """Verifica se as APIs estão acessíveis"""
    apis = [
        {"nome": "Backend Principal", "url": "http://localhost:8000/api/status", "esperado": 200},
        {"nome": "API de Incidentes", "url": "http://localhost:8002/status-cache", "esperado": 200}
    ]
    
    print("\n=== Verificando APIs ===")
    todas_ok = True
    
    for api in apis:
        try:
            r = requests.get(api["url"], timeout=5)
            status = "✅ OK" if r.status_code == api["esperado"] else f"❌ FALHA ({r.status_code})"
            print(f"{api['nome']}: {status}")
            if r.status_code != api["esperado"]:
                todas_ok = False
        except Exception as e:
            todas_ok = False
            print(f"{api['nome']}: ❌ ERRO ({str(e)})")
    
    return todas_ok

def verificar_proxy_frontend():
    """Verifica a configuração de proxy no frontend"""
    vite_config = FRONTEND_DIR / "vite.config.js"
    
    if not vite_config.exists():
        print(f"❌ Arquivo de configuração do Vite não encontrado: {vite_config}")
        return False
    
    print("\n=== Configuração de Proxy do Frontend ===")
    
    # Ler o arquivo de configuração
    with open(vite_config, "r", encoding="utf-8") as f:
        config_content = f.read()
    
    # Verificar configurações de proxy
    tem_proxy_8000 = "/api/" in config_content and "localhost:8000" in config_content
    tem_proxy_8002 = "localhost:8002" in config_content
    
    if tem_proxy_8000:
        print("✅ Proxy configurado para backend principal (porta 8000)")
    else:
        print("❌ Proxy não configurado para backend principal (porta 8000)")
    
    if tem_proxy_8002:
        print("✅ Proxy configurado para API de incidentes (porta 8002)")
    else:
        print("❌ Proxy não configurado para API de incidentes (porta 8002)")
    
    return tem_proxy_8000

def sugerir_alteracoes_proxy():
    """Sugere alterações para o proxy do frontend"""
    vite_config = FRONTEND_DIR / "vite.config.js"
    
    if not vite_config.exists():
        print("❌ Não foi possível encontrar o arquivo vite.config.js para sugerir alterações")
        return
        
    print("\n=== Sugestão de Configuração de Proxy ===")
    print("""
Adicione o seguinte ao seu arquivo vite.config.js:

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true
    },
    '/api/incidentes': {
      target: 'http://localhost:8002',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api\/incidentes/, '/incidentes')
    }
  }
}
```

Isso irá:
1. Redirecionar /api/* para o backend principal (porta 8000)
2. Redirecionar /api/incidentes para a nova API de incidentes (porta 8002)
""")

def verificar_frontend():
    """Verifica se o frontend está configurado para acessar as APIs"""
    
    # Verificar se as APIs estão rodando
    apis_ok = verificar_apis()
    
    if not apis_ok:
        print("\n⚠️ Nem todas as APIs estão acessíveis. Certifique-se de que ambos os servidores estejam rodando.")
    
    # Verificar a configuração de proxy
    proxy_ok = verificar_proxy_frontend()
    
    if not proxy_ok:
        print("\n⚠️ A configuração de proxy pode precisar de ajustes.")
        sugerir_alteracoes_proxy()
    
    print("\n=== Próximos Passos ===")
    if not apis_ok:
        print("1. Inicie as APIs que não estão rodando:")
        print("   - Backend principal: python main.py (porta 8000)")
        print("   - API de incidentes: python api_incidentes.py (porta 8002)")
    
    if not proxy_ok:
        print(f"2. Atualize o arquivo de configuração do Vite: {FRONTEND_DIR / 'vite.config.js'}")
    
    print("3. Reinicie o servidor de desenvolvimento frontend: npm run dev")
    
    return apis_ok and proxy_ok

if __name__ == "__main__":
    print("=== Verificador de Integração Frontend-Backend ===")
    verificar_frontend()
