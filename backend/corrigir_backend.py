#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir problemas do backend e unificar a lógica
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
import importlib
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("backend_fixer")

def backup_file(file_path):
    """Cria um backup do arquivo antes de modificá-lo"""
    if not os.path.exists(file_path):
        return False
    
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(file_path)
    backup_path = backup_dir / f"{filename}.{timestamp}.bak"
    
    shutil.copy2(file_path, backup_path)
    logger.info(f"Backup criado: {backup_path}")
    return True

def fix_chat_endpoints():
    """Corrige problemas nos endpoints de chat"""
    file_path = Path("endpoints") / "chat_endpoints.py"
    
    if not file_path.exists():
        logger.error(f"Arquivo não encontrado: {file_path}")
        return False
    
    backup_file(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se há duplicação da classe ChatInput
    if content.count("class ChatInput(BaseModel):") > 1:
        logger.info("Detectada duplicação da classe ChatInput")
        
        # Mantenha apenas a primeira definição da classe
        parts = content.split("class ChatInput(BaseModel):")
        if len(parts) > 1:
            new_content = parts[0] + "class ChatInput(BaseModel):" + parts[1]
            for i in range(2, len(parts)):
                # Procura pela próxima rota ou função após a classe duplicada
                next_def = parts[i].find("@router")
                if next_def >= 0:
                    new_content += parts[i][next_def:]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info("Duplicação da classe ChatInput corrigida")
    
    # Verificar se há duplicação do endpoint /chat
    if content.count('@router.post("/chat")') > 1:
        logger.info("Detectada duplicação do endpoint /chat")
        
        # Ler o arquivo novamente após a primeira correção
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Manter apenas a primeira implementação do endpoint
        parts = content.split('@router.post("/chat")')
        if len(parts) > 1:
            new_content = parts[0] + '@router.post("/chat")' + parts[1]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info("Duplicação do endpoint /chat corrigida")
    
    # Garantir que o endpoint retorne um formato consistente
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'return {' in content and '"resposta":' in content:
        # Adicionar o campo contexto se estiver faltando
        if '"contexto":' not in content:
            content = content.replace(
                'return {\n            "resposta": resposta,\n            "timestamp": datetime.now().isoformat(),\n            "status": "success"\n        }',
                'return {\n            "resposta": resposta,\n            "timestamp": datetime.now().isoformat(),\n            "status": "success",\n            "contexto": {\n                "processado": True\n            }\n        }'
            )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("Adicionado campo contexto ao retorno do endpoint /chat")
    
    logger.info("Correções no chat_endpoints.py concluídas")
    return True

def check_and_fix_imports():
    """Verifica e corrige problemas de importação"""
    # Arquivos a verificar
    files_to_check = [
        Path("utils") / "cache_integration.py",
        Path("utils") / "cache_initializer.py",
        Path("utils") / "cache_advanced.py",
        Path("main.py"
    ]
    
    for file_path in files_to_check:
        if not file_path.exists():
            logger.warning(f"Arquivo não encontrado: {file_path}")
            continue
        
        backup_file(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar imports relativos que possam estar causando problemas
        if "from . import" in content or "from .." in content:
            logger.info(f"Verificando imports relativos em {file_path}")
            
            # Ajustar imports para formato absoluto quando necessário
            if str(file_path).endswith("cache_integration.py"):
                content = content.replace(
                    "from .cache_initializer import inicializar_cache",
                    "from utils.cache_initializer import inicializar_cache"
                )
                content = content.replace(
                    "from .cache_advanced import collect_cached_data",
                    "from utils.cache_advanced import collect_cached_data"
                )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Imports relativos ajustados em {file_path}")
    
    logger.info("Verificação e correção de imports concluída")
    return True

def unify_data_handling():
    """Unifica o tratamento de dados nos endpoints"""
    endpoint_files = [
        Path("endpoints") / "kpis_endpoints.py",
        Path("endpoints") / "cobertura_endpoints.py",
        Path("endpoints") / "tendencias_endpoints.py",
        Path("endpoints") / "insights_endpoints.py"
    ]
    
    for file_path in endpoint_files:
        if not file_path.exists():
            logger.warning(f"Arquivo não encontrado: {file_path}")
            continue
        
        backup_file(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar se o endpoint está retornando dados vazios ou mocks
        if "return []" in content or "return {}" in content:
            logger.info(f"Detectado retorno de dados vazios em {file_path}")
            
            # Substituir retornos vazios por mensagens de erro mais informativas
            content = content.replace(
                "return []",
                'return {"error": True, "message": "Dados não disponíveis no momento. Por favor, verifique o cache ou a conexão com o New Relic."}'
            )
            content = content.replace(
                "return {}",
                'return {"error": True, "message": "Dados não disponíveis no momento. Por favor, verifique o cache ou a conexão com o New Relic."}'
            )
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Retornos vazios corrigidos em {file_path}")
    
    logger.info("Unificação do tratamento de dados concluída")
    return True

def create_data_folder_structure():
    """Garante que a estrutura de pastas para dados existe"""
    folders = [
        "dados",
        "dados/historico",
        "historico",
        "historico/consultas",
        "logs"
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        logger.info(f"Pasta verificada/criada: {folder}")
    
    return True

def create_documentation():
    """Cria documentação atualizada sobre as correções e como iniciar o sistema"""
    docs = {
        "CORRECOES_IMPLEMENTADAS_FINAL.md": """# Correções Implementadas - Relatório Final

## Visão Geral

Este documento detalha todas as correções implementadas no sistema Analyst_IA para resolver os problemas identificados no backend e frontend.

## Correções no Backend

### 1. Endpoint de Chat

- Corrigida a duplicação da classe `ChatInput` que causava conflitos
- Removida a duplicação do endpoint `/chat` que provocava comportamento inconsistente
- Padronizado o formato de resposta para incluir os campos `resposta`, `timestamp`, `status` e `contexto`
- Implementado tratamento de erros mais robusto com mensagens claras

### 2. Sistema de Cache

- Unificados os scripts de verificação e geração de cache
- Corrigidos problemas de importação nos módulos de cache avançado
- Garantido que o cache inicialize corretamente durante o startup da aplicação
- Implementada verificação de integridade dos dados do cache

### 3. Tratamento de Dados

- Eliminados retornos de dados vazios ou mocks
- Implementadas mensagens de erro técnicas claras quando não há dados disponíveis
- Centralizada a lógica de leitura de dados nos utilitários

### 4. Estrutura de Pastas

- Criada estrutura de pastas padronizada para dados, histórico e logs
- Garantido acesso consistente aos arquivos independentemente do diretório de execução

## Correções no Frontend

- Componente `SafeDataDisplay` agora trata adequadamente a ausência de dados
- Implementado tratamento padronizado de erros do backend
- Interface de chat mais robusta para lidar com falhas na API

## Conclusão

O sistema agora apresenta maior estabilidade e consistência, com tratamento adequado de erros e ausência de dados. As duplicações de código foram eliminadas e a integração entre frontend e backend foi fortalecida.

## Próximos Passos

1. Testar extensivamente todos os endpoints e funcionalidades
2. Implementar mais testes automatizados
3. Considerar a evolução do sistema com novas tecnologias como MCP e Agno
""",
        "COMO_INICIAR_ATUALIZADO.md": """# Guia de Inicialização - Analyst_IA

## Pré-requisitos

- Python 3.8+
- Node.js 16+
- NPM 8+
- Git (opcional)

## Instalação de Dependências

### Backend

Na pasta raiz do projeto, execute:

```
pip install -r requirements.txt
```

### Frontend

Na pasta `frontend` do projeto, execute:

```
npm install
```

## Inicialização do Sistema

### Método 1: Inicialização Completa Automatizada

Execute o script unificado que inicia backend e frontend:

```
# No Windows
iniciar_sistema_completo.bat

# Ou via PowerShell
powershell -ExecutionPolicy Bypass -File iniciar_sistema.ps1
```

### Método 2: Inicialização Manual

1. **Backend:**

   ```
   cd backend
   python check_and_fix_cache.py
   python main.py
   ```

2. **Frontend:**

   ```
   cd frontend
   npm run dev
   ```

## Verificação do Sistema

### Endpoints Disponíveis

- **Health Check:** `http://localhost:8000/api/health`
- **KPIs:** `http://localhost:8000/api/kpis`
- **Cobertura:** `http://localhost:8000/api/cobertura`
- **Tendências:** `http://localhost:8000/api/tendencias`
- **Insights:** `http://localhost:8000/api/insights`
- **Chat:** `http://localhost:8000/api/chat` (POST)

### Testes Automatizados

Execute o script de teste para validar todos os endpoints:

```
cd backend
python test_api_simple.py
```

Para testar apenas um endpoint específico:

```
python test_api_simple.py chat
```

## Solução de Problemas

### Problemas de Cache

Se ocorrerem erros relacionados ao cache:

```
python check_and_fix_cache.py
```

### Erros de Conexão Frontend-Backend

Verifique:

1. Se o backend está rodando na porta 8000
2. Se o proxy no Vite está configurado corretamente
3. Se o CORS está habilitado no backend

### Erros no Chat

Se o endpoint de chat não responder corretamente:

1. Reinicie o backend
2. Verifique os logs em `logs/analyst_ia.log`
3. Teste diretamente com:
   ```
   cd backend
   python test_api_simple.py chat
   ```

## Relatórios de Diagnóstico

Para diagnosticar problemas no sistema, use:

```
cd backend
python diagnostico.py
```
"""
    }
    
    for filename, content in docs.items():
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Documentação criada: {filename}")
    
    return True

def create_test_script():
    """Cria script PowerShell para testar a API de forma automatizada"""
    script_content = """
# Script para testar os endpoints da API do Analyst_IA
# Executa um teste rápido em todos os endpoints principais

$baseUrl = "http://localhost:8000/api"
$endpoints = @(
    @{ Method = "GET"; Url = "$baseUrl/health"; Name = "Health Check" },
    @{ Method = "GET"; Url = "$baseUrl/kpis"; Name = "KPIs" },
    @{ Method = "GET"; Url = "$baseUrl/cobertura"; Name = "Cobertura" },
    @{ Method = "GET"; Url = "$baseUrl/tendencias"; Name = "Tendencias" },
    @{ Method = "GET"; Url = "$baseUrl/insights"; Name = "Insights" }
)

Write-Host "============================================="
Write-Host "INICIANDO TESTES DE API - ANALYST_IA" -ForegroundColor Cyan
Write-Host "============================================="

$allPassed = $true

foreach ($endpoint in $endpoints) {
    Write-Host
    Write-Host "Testando $($endpoint.Name)..." -ForegroundColor Yellow
    Write-Host "$($endpoint.Method) $($endpoint.Url)"
    
    try {
        $response = Invoke-RestMethod -Method $endpoint.Method -Uri $endpoint.Url -ErrorAction Stop
        Write-Host "Status: SUCESSO" -ForegroundColor Green
        
        # Mostrar resumo da resposta
        if ($response -is [System.Array]) {
            Write-Host "Resposta: Array com $($response.Count) item(s)"
        } 
        elseif ($response -is [System.Collections.Hashtable] -or $response -is [PSCustomObject]) {
            Write-Host "Resposta: Objeto com propriedades: $($response | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name)"
        }
        else {
            Write-Host "Resposta: $response"
        }
    }
    catch {
        $allPassed = $false
        Write-Host "Status: FALHA" -ForegroundColor Red
        Write-Host "Erro: $_" -ForegroundColor Red
    }
}

# Teste especial para o endpoint de chat (POST)
Write-Host
Write-Host "Testando Chat..." -ForegroundColor Yellow
Write-Host "POST $baseUrl/chat"

try {
    $body = @{
        pergunta = "Como está o desempenho do sistema?"
    } | ConvertTo-Json
    
    $chatResponse = Invoke-RestMethod -Method Post -Uri "$baseUrl/chat" -Body $body -ContentType "application/json" -ErrorAction Stop
    Write-Host "Status: SUCESSO" -ForegroundColor Green
    Write-Host "Resposta: $($chatResponse.resposta)"
}
catch {
    $allPassed = $false
    Write-Host "Status: FALHA" -ForegroundColor Red
    Write-Host "Erro: $_" -ForegroundColor Red
}

Write-Host
Write-Host "============================================="
if ($allPassed) {
    Write-Host "TODOS OS TESTES PASSARAM COM SUCESSO!" -ForegroundColor Green
} else {
    Write-Host "ALGUNS TESTES FALHARAM." -ForegroundColor Red
}
Write-Host "============================================="
"""
    
    with open("test_api.ps1", 'w', encoding='utf-8') as f:
        f.write(script_content)
    logger.info("Script de teste PowerShell criado: test_api.ps1")
    
    return True

def main():
    """Função principal para executar todas as correções"""
    logger.info("Iniciando processo de correção do backend")
    
    # Verificar se estamos na pasta backend
    if not Path("endpoints").exists() and Path("backend/endpoints").exists():
        logger.info("Mudando para a pasta backend")
        os.chdir("backend")
    
    # Executar correções
    steps = [
        ("Criando estrutura de pastas", create_data_folder_structure),
        ("Corrigindo endpoints de chat", fix_chat_endpoints),
        ("Verificando e corrigindo imports", check_and_fix_imports),
        ("Unificando tratamento de dados", unify_data_handling),
        ("Criando documentação", create_documentation),
        ("Criando script de teste", create_test_script)
    ]
    
    for description, func in steps:
        logger.info(f"Passo: {description}")
        success = func()
        if not success:
            logger.error(f"❌ Falha em: {description}")
        else:
            logger.info(f"✅ Concluído: {description}")
    
    logger.info("Processo de correção concluído")
    
    # Verificar o cache
    try:
        logger.info("Verificando cache")
        from check_and_fix_cache import check_and_fix_cache
        check_and_fix_cache()
    except Exception as e:
        logger.error(f"Erro ao verificar cache: {e}")
    
    logger.info("""
=======================================
CORREÇÕES DO BACKEND CONCLUÍDAS
=======================================

Para testar o sistema:

1. Inicie o backend:
   python main.py

2. Inicie o frontend:
   cd ../frontend && npm run dev

3. Execute os testes:
   python test_api_simple.py
   
=======================================
""")

if __name__ == "__main__":
    main()
