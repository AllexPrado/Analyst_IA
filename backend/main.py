from fastapi import FastAPI
from middleware.agno_proxy import add_agno_middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import re
import logging
import subprocess
from datetime import datetime
# ...existing code...








# Incluir os endpoints inteligentes do Agno (sem try/except para exibir qualquer erro de importação)
from routers.agno_router import router as agno_router

# ...existing code...

app = FastAPI(
    title="Analyst-IA API",
    description="Backend FastAPI para análise de métricas e IA contextual",
    version="2.0.0"
)

# Adicionar middleware para redirecionar /agno para /api/agno
app = add_agno_middleware(app)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração do logger
logger = logging.getLogger("main")

# Removido o middleware de redirecionamento em favor de uma abordagem
# mais direta que registra os endpoints em ambos os caminhos

# Importa o router principal
from core_router import api_router
app.include_router(api_router, prefix="/api")

# Incluir os endpoints inteligentes do Agno diretamente no app
# Nota: Incluímos o router diretamente sem try/except para mostrar qualquer erro
app.include_router(agno_router, prefix="/agno", tags=["Agno IA"])
logger.info("[AGNO] Endpoints inteligentes do Agno IA disponíveis em /agno")

# Registrar também no api_router para manter compatibilidade com /api/agno
api_router.include_router(agno_router, prefix="/agno", tags=["Agno IA via API"])
logger.info("[AGNO] Endpoints inteligentes do Agno IA também disponíveis em /api/agno")


# Criar diretório de dados se não existir
os.makedirs("dados", exist_ok=True)


# Importa o BaseModel do pydantic e tipos do typing
from pydantic import BaseModel
from typing import Optional, Dict, Any

class ChatInput(BaseModel):
    pergunta: str = ""

class MetricsResponse(BaseModel):
    entidades: list

class ChatResponse(BaseModel):
    resposta: str
    contexto: Optional[Dict[str, Any]] = None

from utils.newrelic_collector import coletar_contexto_completo, safe_first, NewRelicCollector


# Importa o coletor avançado se disponível
logger = logging.getLogger("main")
try:
    from utils.newrelic_advanced_collector import collect_full_data as coletar_contexto_avancado
    COLETOR_AVANCADO_DISPONIVEL = True
    logger.info("✅ Coletor avançado do New Relic disponível e será utilizado por padrão")
except ImportError:
    COLETOR_AVANCADO_DISPONIVEL = False
    logger.warning("⚠️ Coletor avançado do New Relic não disponível, usando coletor padrão")

from utils.persona_detector import detectar_persona, montar_prompt_por_persona
from utils.openai_connector import gerar_resposta_ia
from utils.cache import (
    get_cache, cache_updater_loop, diagnosticar_cache, 
    buscar_no_cache_por_pergunta, forcar_atualizacao_cache,
    atualizar_cache_completo
)
import asyncio
from utils.entity_processor import filter_entities_with_data, process_entity_details
from utils.intent_extractor import extract_metrics_for_query
from utils.context_enricher import context_enricher
from utils.learning_integration import learning_integration

# Instancia o coletor New Relic para health checks
newrelic_collector = NewRelicCollector(
    api_key=os.getenv('NEW_RELIC_API_KEY', ''),
    account_id=os.getenv('NEW_RELIC_ACCOUNT_ID', '')
)

app = FastAPI(
    title="Analyst-IA API",
    description="Backend FastAPI para análise de métricas e IA contextual",
    version="2.0.0"
)

# Adicionar middleware para redirecionar /agno para /api/agno
app = add_agno_middleware(app)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir os endpoints do router principal
app.include_router(api_router, prefix="/api")

# Endpoint para consultar resultados dos agentes inteligentes
@app.get("/api/auto_agents/results")
async def get_auto_agents_results():
    """Retorna os resultados da última execução dos agentes de auto-correção e otimização."""
    results = {}
    try:
        if auto_fix_agent:
            fix_result = auto_fix_agent.run()
            results['auto_fix_agent'] = {
                'last_run': fix_result.get('last_run'),
                'errors': fix_result.get('errors'),
                'suggestions': fix_result.get('suggestions'),
                'test_output': fix_result.get('test_output')
            }
        if auto_optimize_agent:
            optimizations = auto_optimize_agent.scan_code()
            results['auto_optimize_agent'] = {
                'suggestions': optimizations
            }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return results

# Mover o endpoint para depois da definição do app

# ...existing code...
import os
# Inicializa o agente New Relic manualmente no Windows
try:
    import newrelic.agent
    newrelic.agent.initialize('newrelic.ini')
    print("[NEWRELIC] Agente New Relic inicializado via código.")
except ImportError:
    print("[NEWRELIC] Pacote newrelic não encontrado. Monitoramento New Relic não será ativado.")
from dotenv import load_dotenv
load_dotenv()
import os
print("[DEBUG] NEW_RELIC_API_KEY:", os.getenv("NEW_RELIC_API_KEY"))
print("[DEBUG] NEW_RELIC_QUERY_KEY:", os.getenv("NEW_RELIC_QUERY_KEY"))
print("[DEBUG] NEW_RELIC_ACCOUNT_ID:", os.getenv("NEW_RELIC_ACCOUNT_ID"))
print("[DEBUG] OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

import sys
import json
import logging
import aiofiles
import traceback
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import re
import asyncio



# Inicializa o sistema de cache durante o startup
try:
    import utils.cache_integration
    print("Sistema de cache avançado inicializado")
except ImportError as e:
    print(f"Aviso: não foi possível inicializar o sistema de cache avançado: {e}")
    print("O sistema continuará funcionando com o cache padrão")

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken não disponível. Usando fallback para contagem de tokens.")

# Importar o router principal
try:
    from core_router import api_router
except ImportError:
    # Fallback para quando executado de outra pasta
    from backend.core_router import api_router

import uvicorn
from core_inteligente.agno_agent import auto_fix_agent, auto_optimize_agent

import uvicorn
from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Request, APIRouter
from middleware.agno_proxy import add_agno_middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader

# Configuração de logging
# Garante que o diretório de logs existe
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/analyst_ia.log',
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

# Configuração da aplicação
app = FastAPI(
    title="Analyst-IA API",
    description="Backend FastAPI para análise de métricas e IA contextual",
    version="2.0.0"
)

# Adicionar middleware para redirecionar /agno para /api/agno
app = add_agno_middleware(app)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluir os endpoints do router principal
app.include_router(api_router, prefix="/api")


# Incluir os endpoints inteligentes do Agno (sem try/except para exibir qualquer erro de importação)
from routers.agno_router import router as agno_router
app.include_router(agno_router, prefix="/agno", tags=["Agno IA"])
print("[AGNO] Endpoints inteligentes do Agno IA disponíveis em /agno")

# Criar diretório de dados se não existir
os.makedirs("dados", exist_ok=True)

class ChatInput(BaseModel):
    pergunta: str = ""

class MetricsResponse(BaseModel):
    entidades: list

class ChatResponse(BaseModel):
    resposta: str
    contexto: Optional[Dict[str, Any]] = None

from utils.newrelic_collector import coletar_contexto_completo, safe_first, NewRelicCollector

# Importa o coletor avançado se disponível
try:
    from utils.newrelic_advanced_collector import collect_full_data as coletar_contexto_avancado
    COLETOR_AVANCADO_DISPONIVEL = True
    logger.info("✅ Coletor avançado do New Relic disponível e será utilizado por padrão")
except ImportError:
    COLETOR_AVANCADO_DISPONIVEL = False
    logger.warning("⚠️ Coletor avançado do New Relic não disponível, usando coletor padrão")

from utils.persona_detector import detectar_persona, montar_prompt_por_persona
from utils.openai_connector import gerar_resposta_ia
from utils.cache import (
    get_cache, cache_updater_loop, diagnosticar_cache, 
    buscar_no_cache_por_pergunta, forcar_atualizacao_cache,
    atualizar_cache_completo
)
import asyncio
from utils.entity_processor import filter_entities_with_data, process_entity_details
from utils.intent_extractor import extract_metrics_for_query
from utils.context_enricher import context_enricher
from utils.learning_integration import learning_integration

# Instancia o coletor New Relic para health checks
newrelic_collector = NewRelicCollector(
    api_key=os.getenv('NEW_RELIC_API_KEY', ''),
    account_id=os.getenv('NEW_RELIC_ACCOUNT_ID', '')
)

# Endpoint para consultar resultados dos agentes inteligentes
@app.get("/api/auto_agents/results")
async def get_auto_agents_results():
    """Retorna os resultados da última execução dos agentes de auto-correção e otimização."""
    results = {}
    try:
        if auto_fix_agent:
            fix_result = auto_fix_agent.run()
            results['auto_fix_agent'] = {
                'last_run': fix_result.get('last_run'),
                'errors': fix_result.get('errors'),
                'suggestions': fix_result.get('suggestions'),
                'test_output': fix_result.get('test_output')
            }
        if auto_optimize_agent:
            optimizations = auto_optimize_agent.scan_code()
            results['auto_optimize_agent'] = {
                'suggestions': optimizations
            }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return results

# ...existing code...
import os
# Inicializa o agente New Relic manualmente no Windows
try:
    import newrelic.agent
    newrelic.agent.initialize('newrelic.ini')
    print("[NEWRELIC] Agente New Relic inicializado via código.")
except ImportError:
    print("[NEWRELIC] Pacote newrelic não encontrado. Monitoramento New Relic não será ativado.")
from dotenv import load_dotenv
load_dotenv()
import os
print("[DEBUG] NEW_RELIC_API_KEY:", os.getenv("NEW_RELIC_API_KEY"))
print("[DEBUG] NEW_RELIC_QUERY_KEY:", os.getenv("NEW_RELIC_QUERY_KEY"))
print("[DEBUG] NEW_RELIC_ACCOUNT_ID:", os.getenv("NEW_RELIC_ACCOUNT_ID"))
print("[DEBUG] OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

import sys
import json
import logging
import aiofiles
import traceback
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import re
import asyncio



# Inicializa o sistema de cache durante o startup
try:
    import utils.cache_integration
    print("Sistema de cache avançado inicializado")
except ImportError as e:
    print(f"Aviso: não foi possível inicializar o sistema de cache avançado: {e}")
    print("O sistema continuará funcionando com o cache padrão")

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken não disponível. Usando fallback para contagem de tokens.")

# Importar o router principal
try:
    from core_router import api_router
except ImportError:
    # Fallback para quando executado de outra pasta
    from backend.core_router import api_router

import uvicorn
from core_inteligente.agno_agent import auto_fix_agent, auto_optimize_agent

import uvicorn
from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Request, APIRouter
from middleware.agno_proxy import add_agno_middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader

# Configuração de logging
# Garante que o diretório de logs existe
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/analyst_ia.log',
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

# Configuração da aplicação
app = FastAPI(
    title="Analyst-IA API",
    description="Backend FastAPI para análise de métricas e IA contextual",
    version="2.0.0"
)

# Adicionar middleware para redirecionar /agno para /api/agno
app = add_agno_middleware(app)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluir os endpoints do router principal
app.include_router(api_router, prefix="/api")


# Incluir os endpoints inteligentes do Agno (sem try/except para exibir qualquer erro de importação)
from routers.agno_router import router as agno_router
app.include_router(agno_router, prefix="/agno", tags=["Agno IA"])
print("[AGNO] Endpoints inteligentes do Agno IA disponíveis em /agno")

# Criar diretório de dados se não existir
os.makedirs("dados", exist_ok=True)

class ChatInput(BaseModel):
    pergunta: str = ""

class MetricsResponse(BaseModel):
    entidades: list

class ChatResponse(BaseModel):
    resposta: str
    contexto: Optional[Dict[str, Any]] = None

from utils.newrelic_collector import coletar_contexto_completo, safe_first, NewRelicCollector

# Importa o coletor avançado se disponível
try:
    from utils.newrelic_advanced_collector import collect_full_data as coletar_contexto_avancado
    COLETOR_AVANCADO_DISPONIVEL = True
    logger.info("✅ Coletor avançado do New Relic disponível e será utilizado por padrão")
except ImportError:
    COLETOR_AVANCADO_DISPONIVEL = False
    logger.warning("⚠️ Coletor avançado do New Relic não disponível, usando coletor padrão")

from utils.persona_detector import detectar_persona, montar_prompt_por_persona
from utils.openai_connector import gerar_resposta_ia
from utils.cache import (
    get_cache, cache_updater_loop, diagnosticar_cache, 
    buscar_no_cache_por_pergunta, forcar_atualizacao_cache,
    atualizar_cache_completo
)
import asyncio
from utils.entity_processor import filter_entities_with_data, process_entity_details
from utils.intent_extractor import extract_metrics_for_query
from utils.context_enricher import context_enricher
from utils.learning_integration import learning_integration

# Instancia o coletor New Relic para health checks
newrelic_collector = NewRelicCollector(
    api_key=os.getenv('NEW_RELIC_API_KEY', ''),
    account_id=os.getenv('NEW_RELIC_ACCOUNT_ID', '')
)

# Endpoint para consultar resultados dos agentes inteligentes
@app.get("/api/auto_agents/results")
async def get_auto_agents_results():
    """Retorna os resultados da última execução dos agentes de auto-correção e otimização."""
    results = {}
    try:
        if auto_fix_agent:
            fix_result = auto_fix_agent.run()
            results['auto_fix_agent'] = {
                'last_run': fix_result.get('last_run'),
                'errors': fix_result.get('errors'),
                'suggestions': fix_result.get('suggestions'),
                'test_output': fix_result.get('test_output')
            }
        if auto_optimize_agent:
            optimizations = auto_optimize_agent.scan_code()
            results['auto_optimize_agent'] = {
                'suggestions': optimizations
            }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return results

# Mover o endpoint para depois da definição do app

# ...existing code...
import os
# Inicializa o agente New Relic manualmente no Windows
try:
    import newrelic.agent
    newrelic.agent.initialize('newrelic.ini')
    print("[NEWRELIC] Agente New Relic inicializado via código.")
except ImportError:
    print("[NEWRELIC] Pacote newrelic não encontrado. Monitoramento New Relic não será ativado.")
from dotenv import load_dotenv
load_dotenv()
import os
print("[DEBUG] NEW_RELIC_API_KEY:", os.getenv("NEW_RELIC_API_KEY"))
print("[DEBUG] NEW_RELIC_QUERY_KEY:", os.getenv("NEW_RELIC_QUERY_KEY"))
print("[DEBUG] NEW_RELIC_ACCOUNT_ID:", os.getenv("NEW_RELIC_ACCOUNT_ID"))
print("[DEBUG] OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

import sys
import json
import logging
import aiofiles
import traceback
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import re
import asyncio



# Inicializa o sistema de cache durante o startup
try:
    import utils.cache_integration
    print("Sistema de cache avançado inicializado")
except ImportError as e:
    print(f"Aviso: não foi possível inicializar o sistema de cache avançado: {e}")
    print("O sistema continuará funcionando com o cache padrão")

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken não disponível. Usando fallback para contagem de tokens.")

# Importar o router principal
try:
    from core_router import api_router
except ImportError:
    # Fallback para quando executado de outra pasta
    from backend.core_router import api_router

import uvicorn
from core_inteligente.agno_agent import auto_fix_agent, auto_optimize_agent

import uvicorn
from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Request, APIRouter
from middleware.agno_proxy import add_agno_middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader

# Configuração de logging
# Garante que o diretório de logs existe
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/analyst_ia.log',
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

# Configuração da aplicação
app = FastAPI(
    title="Analyst-IA API",
    description="Backend FastAPI para análise de métricas e IA contextual",
    version="2.0.0"
)

# Adicionar middleware para redirecionar /agno para /api/agno
app = add_agno_middleware(app)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluir os endpoints do router principal
app.include_router(api_router, prefix="/api")


# Incluir os endpoints inteligentes do Agno (sem try/except para exibir qualquer erro de importação)
from routers.agno_router import router as agno_router
app.include_router(agno_router, prefix="/agno", tags=["Agno IA"])
print("[AGNO] Endpoints inteligentes do Agno IA disponíveis em /agno")

# Criar diretório de dados se não existir
os.makedirs("dados", exist_ok=True)

class ChatInput(BaseModel):
    pergunta: str = ""

class MetricsResponse(BaseModel):
    entidades: list

class ChatResponse(BaseModel):
    resposta: str
    contexto: Optional[Dict[str, Any]] = None

from utils.newrelic_collector import coletar_contexto_completo, safe_first, NewRelicCollector

# Importa o coletor avançado se disponível
try:
    from utils.newrelic_advanced_collector import collect_full_data as coletar_contexto_avancado
    COLETOR_AVANCADO_DISPONIVEL = True
    logger.info("✅ Coletor avançado do New Relic disponível e será utilizado por padrão")
except ImportError:
    COLETOR_AVANCADO_DISPONIVEL = False
    logger.warning("⚠️ Coletor avançado do New Relic não disponível, usando coletor padrão")

from utils.persona_detector import detectar_persona, montar_prompt_por_persona
from utils.openai_connector import gerar_resposta_ia
from utils.cache import (
    get_cache, cache_updater_loop, diagnosticar_cache, 
    buscar_no_cache_por_pergunta, forcar_atualizacao_cache,
    atualizar_cache_completo
)
import asyncio
from utils.entity_processor import filter_entities_with_data, process_entity_details
from utils.intent_extractor import extract_metrics_for_query
from utils.context_enricher import context_enricher
from utils.learning_integration import learning_integration

# Instancia o coletor New Relic para health checks
newrelic_collector = NewRelicCollector(
    api_key=os.getenv('NEW_RELIC_API_KEY', ''),
    account_id=os.getenv('NEW_RELIC_ACCOUNT_ID', '')
)

# Endpoint para consultar resultados dos agentes inteligentes
@app.get("/api/auto_agents/results")
async def get_auto_agents_results():
    """Retorna os resultados da última execução dos agentes de auto-correção e otimização."""
    results = {}
    try:
        if auto_fix_agent:
            fix_result = auto_fix_agent.run()
            results['auto_fix_agent'] = {
                'last_run': fix_result.get('last_run'),
                'errors': fix_result.get('errors'),
                'suggestions': fix_result.get('suggestions'),
                'test_output': fix_result.get('test_output')
            }
        if auto_optimize_agent:
            optimizations = auto_optimize_agent.scan_code()
            results['auto_optimize_agent'] = {
                'suggestions': optimizations
            }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return results

# ...existing code...
import os
# Inicializa o agente New Relic manualmente no Windows
try:
    import newrelic.agent
    newrelic.agent.initialize('newrelic.ini')
    print("[NEWRELIC] Agente New Relic inicializado via código.")
except ImportError:
    print("[NEWRELIC] Pacote newrelic não encontrado. Monitoramento New Relic não será ativado.")
from dotenv import load_dotenv
load_dotenv()
import os
print("[DEBUG] NEW_RELIC_API_KEY:", os.getenv("NEW_RELIC_API_KEY"))
print("[DEBUG] NEW_RELIC_QUERY_KEY:", os.getenv("NEW_RELIC_QUERY_KEY"))
print("[DEBUG] NEW_RELIC_ACCOUNT_ID:", os.getenv("NEW_RELIC_ACCOUNT_ID"))
print("[DEBUG] OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

import sys
import json
import logging
import aiofiles
import traceback
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import re
import asyncio



# Inicializa o sistema de cache durante o startup
try:
    import utils.cache_integration
    print("Sistema de cache avançado inicializado")
except ImportError as e:
    print(f"Aviso: não foi possível inicializar o sistema de cache avançado: {e}")
    print("O sistema continuará funcionando com o cache padrão")

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken não disponível. Usando fallback para contagem de tokens.")

# Importar o router principal
try:
    from core_router import api_router
except ImportError:
    # Fallback para quando executado de outra pasta
    from backend.core_router import api_router

import uvicorn
from core_inteligente.agno_agent import auto_fix_agent, auto_optimize_agent

import uvicorn
from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Request, APIRouter
from middleware.agno_proxy import add_agno_middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader

# Configuração de logging
# Garante que o diretório de logs existe
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/analyst_ia.log',
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

# Configuração da aplicação
app = FastAPI(
    title="Analyst-IA API",
    description="Backend FastAPI para análise de métricas e IA contextual",
    version="2.0.0"
)

# Adicionar middleware para redirecionar /agno para /api/agno
app = add_agno_middleware(app)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluir os endpoints do router principal
app.include_router(api_router, prefix="/api")


# Incluir os endpoints inteligentes do Agno (sem try/except para exibir qualquer erro de importação)
from routers.agno_router import router as agno_router
app.include_router(agno_router, prefix="/agno", tags=["Agno IA"])
print("[AGNO] Endpoints inteligentes do Agno IA disponíveis em /agno")

# Criar diretório de dados se não existir
os.makedirs("dados", exist_ok=True)

class ChatInput(BaseModel):
    pergunta: str = ""

class MetricsResponse(BaseModel):
    entidades: list

class ChatResponse(BaseModel):
    resposta: str
    contexto: Optional[Dict[str, Any]] = None

from utils.newrelic_collector import coletar_contexto_completo, safe_first, NewRelicCollector

# Importa o coletor avançado se disponível
try:
    from utils.newrelic_advanced_collector import collect_full_data as coletar_contexto_avancado
    COLETOR_AVANCADO_DISPONIVEL = True
    logger.info("✅ Coletor avançado do New Relic disponível e será utilizado por padrão")
except ImportError:
    COLETOR_AVANCADO_DISPONIVEL = False
    logger.warning("⚠️ Coletor avançado do New Relic não disponível, usando coletor padrão")

from utils.persona_detector import detectar_persona, montar_prompt_por_persona
from utils.openai_connector import gerar_resposta_ia
from utils.cache import (
    get_cache, cache_updater_loop, diagnosticar_cache, 
    buscar_no_cache_por_pergunta, forcar_atualizacao_cache,
    atualizar_cache_completo
)
import asyncio
from utils.entity_processor import filter_entities_with_data, process_entity_details
from utils.intent_extractor import extract_metrics_for_query
from utils.context_enricher import context_enricher
from utils.learning_integration import learning_integration

# Instancia o coletor New Relic para health checks
newrelic_collector = NewRelicCollector(
    api_key=os.getenv('NEW_RELIC_API_KEY', ''),
    account_id=os.getenv('NEW_RELIC_ACCOUNT_ID', '')
)

# Endpoint para consultar resultados dos agentes inteligentes
@app.get("/api/auto_agents/results")
async def get_auto_agents_results():
    """Retorna os resultados da última execução dos agentes de auto-correção e otimização."""
    results = {}
    try:
        if auto_fix_agent:
            fix_result = auto_fix_agent.run()
            results['auto_fix_agent'] = {
                'last_run': fix_result.get('last_run'),
                'errors': fix_result.get('errors'),
                'suggestions': fix_result.get('suggestions'),
                'test_output': fix_result.get('test_output')
            }
        if auto_optimize_agent:
            optimizations = auto_optimize_agent.scan_code()
            results['auto_optimize_agent'] = {
                'suggestions': optimizations
            }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return results

# Mover o endpoint para depois da definição do app

# ...existing code...
import os
# Inicializa o agente New Relic manualmente no Windows
try:
    import newrelic.agent
    newrelic.agent.initialize('newrelic.ini')
    print("[NEWRELIC] Agente New Relic inicializado via código.")
except ImportError:
    print("[NEWRELIC] Pacote newrelic não encontrado. Monitoramento New Relic não será ativado.")
from dotenv import load_dotenv
load_dotenv()
import os
print("[DEBUG] NEW_RELIC_API_KEY:", os.getenv("NEW_RELIC_API_KEY"))
print("[DEBUG] NEW_RELIC_QUERY_KEY:", os.getenv("NEW_RELIC_QUERY_KEY"))
print("[DEBUG] NEW_RELIC_ACCOUNT_ID:", os.getenv("NEW_RELIC_ACCOUNT_ID"))
print("[DEBUG] OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

import sys
import json
import logging
import aiofiles
import traceback
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import re
import asyncio



# Inicializa o sistema de cache durante o startup
try:
    import utils.cache_integration
    print("Sistema de cache avançado inicializado")
except ImportError as e:
    print(f"Aviso: não foi possível inicializar o sistema de cache avançado: {e}")
    print("O sistema continuará funcionando com o cache padrão")

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken não disponível. Usando fallback para contagem de tokens.")

# Importar o router principal
try:
    from core_router import api_router
except ImportError:
    # Fallback para quando executado de outra pasta
    from backend.core_router import api_router

import uvicorn
from core_inteligente.agno_agent import auto_fix_agent, auto_optimize_agent

import uvicorn
from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Request, APIRouter
from middleware.agno_proxy import add_agno_middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader

# Configuração de logging
# Garante que o diretório de logs existe
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/analyst_ia.log',
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

# Configuração da aplicação
app = FastAPI(
    title="Analyst-IA API",
    description="Backend FastAPI para análise de métricas e IA contextual",
    version="2.0.0"
)

# Adicionar middleware para redirecionar /agno para /api/agno
app = add_agno_middleware(app)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluir os endpoints do router principal
app.include_router(api_router, prefix="/api")


# Incluir os endpoints inteligentes do Agno (sem try/except para exibir qualquer erro de importação)
from routers.agno_router import router as agno_router
app.include_router(agno_router, prefix="/agno", tags=["Agno IA"])
print("[AGNO] Endpoints inteligentes do Agno IA disponíveis em /agno")

# Criar diretório de dados se não existir
os.makedirs("dados", exist_ok=True)

class ChatInput(BaseModel):
    pergunta: str = ""

class MetricsResponse(BaseModel):
    entidades: list

class ChatResponse(BaseModel):
    resposta: str
    contexto: Optional[Dict[str, Any]] = None

from utils.newrelic_collector import coletar_contexto_completo, safe_first, NewRelicCollector

# Importa o coletor avançado se disponível
try:
    from utils.newrelic_advanced_collector import collect_full_data as coletar_contexto_avancado
    COLETOR_AVANCADO_DISPONIVEL = True
    logger.info("✅ Coletor avançado do New Relic disponível e será utilizado por padrão")
except ImportError:
    COLETOR_AVANCADO_DISPONIVEL = False
    logger.warning("⚠️ Coletor avançado do New Relic não disponível, usando coletor padrão")

from utils.persona_detector import detectar_persona, montar_prompt_por_persona
from utils.openai_connector import gerar_resposta_ia
from utils.cache import (
    get_cache, cache_updater_loop, diagnosticar_cache, 
    buscar_no_cache_por_pergunta, forcar_atualizacao_cache,
    atualizar_cache_completo
)
import asyncio
from utils.entity_processor import filter_entities_with_data, process_entity_details
from utils.intent_extractor import extract_metrics_for_query
from utils.context_enricher import context_enricher
from utils.learning_integration import learning_integration

# Instancia o coletor New Relic para health checks
newrelic_collector = NewRelicCollector(
    api_key=os.getenv('NEW_RELIC_API_KEY', ''),
    account_id=os.getenv('NEW_RELIC_ACCOUNT_ID', '')
)

# Endpoint para consultar resultados dos agentes inteligentes
@app.get("/api/auto_agents/results")
async def get_auto_agents_results():
    """Retorna os resultados da última execução dos agentes de auto-correção e otimização."""
    results = {}
    try:
        if auto_fix_agent:
            fix_result = auto_fix_agent.run()
            results['auto_fix_agent'] = {
                'last_run': fix_result.get('last_run'),
                'errors': fix_result.get('errors'),
                'suggestions': fix_result.get('suggestions'),
                'test_output': fix_result.get('test_output')
            }
        if auto_optimize_agent:
            optimizations = auto_optimize_agent.scan_code()
            results['auto_optimize_agent'] = {
                'suggestions': optimizations
            }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return results

# Mover o endpoint para depois da definição do app

# ...existing code...
import os
# Inicializa o agente New Relic manualmente no Windows
try:
    import newrelic.agent
    newrelic.agent.initialize('newrelic.ini')
    print("[NEWRELIC] Agente New Relic inicializado via código.")
except ImportError:
    print("[NEWRELIC] Pacote newrelic não encontrado. Monitoramento New Relic não será ativado.")
from dotenv import load_dotenv
load_dotenv()
import os
print("[DEBUG] NEW_RELIC_API_KEY:", os.getenv("NEW_RELIC_API_KEY"))
print("[DEBUG] NEW_RELIC_QUERY_KEY:", os.getenv("NEW_RELIC_QUERY_KEY"))
print("[DEBUG] NEW_RELIC_ACCOUNT_ID:", os.getenv("NEW_RELIC_ACCOUNT_ID"))
print("[DEBUG] OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

import sys
import json
import logging
import aiofiles
import traceback
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import re
import asyncio



# Inicializa o sistema de cache durante o startup
try:
    import utils.cache_integration
    print("Sistema de cache avançado inicializado")
except ImportError as e:
    print(f"Aviso: não foi possível inicializar o sistema de cache avançado: {e}")
    print("O sistema continuará funcionando com o cache padrão")

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken não disponível. Usando fallback para contagem de tokens.")

# Importar o router principal
try:
    from core_router import api_router
except ImportError:
    # Fallback para quando executado de outra pasta
    from backend.core_router import api_router

import uvicorn
from core_inteligente.agno_agent import auto_fix_agent, auto_optimize_agent

import uvicorn
from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Request, APIRouter
from middleware.agno_proxy import add_agno_middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader

# Configuração de logging
# Garante que o diretório de logs existe
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/analyst_ia.log',
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

# Configuração da aplicação
app = FastAPI(
    title="Analyst-IA API",
    description="Backend FastAPI para análise de métricas e IA contextual",
    version="2.0.0"
)

# Adicionar middleware para redirecionar /agno para /api/agno
app = add_agno_middleware(app)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluir os endpoints do router principal
app.include_router(api_router, prefix="/api")


# Incluir os endpoints inteligentes do Agno (sem try/except para exibir qualquer erro de importação)
from routers.agno_router import router as agno_router
app.include_router(agno_router, prefix="/agno", tags=["Agno IA"])
print("[AGNO] Endpoints inteligentes do Agno IA disponíveis em /agno")

# Criar diretório de dados se não existir
os.makedirs("dados", exist_ok=True)

class ChatInput(BaseModel):
    pergunta: str = ""

class MetricsResponse(BaseModel):
    entidades: list

class ChatResponse(BaseModel):
    resposta: str
    contexto: Optional[Dict[str, Any]] = None

from utils.newrelic_collector import coletar_contexto_completo, safe_first, NewRelicCollector

# Importa o coletor avançado se disponível
try:
    from utils.newrelic_advanced_collector import collect_full_data as coletar_contexto_avancado
    COLETOR_AVANCADO_DISPONIVEL = True
    logger.info("✅ Coletor avançado do New Relic disponível e será utilizado por padrão")
except ImportError:
    COLETOR_AVANCADO_DISPONIVEL = False
    logger.warning("⚠️ Coletor avançado do New Relic não disponível, usando coletor padrão")

from utils.persona_detector import detectar_persona, montar_prompt_por_persona
from utils.openai_connector import gerar_resposta_ia
from utils.cache import (
    get_cache, cache_updater_loop, diagnosticar_cache, 
    buscar_no_cache_por_pergunta, forcar_atualizacao_cache,
    atualizar_cache_completo
)
import asyncio
from utils.entity_processor import filter_entities_with_data, process_entity_details
from utils.intent_extractor import extract_metrics_for_query
from utils.context_enricher import context_enricher
from utils.learning_integration import learning_integration

# Instancia o coletor New Relic para health checks
newrelic_collector = NewRelicCollector(
    api_key=os.getenv('NEW_RELIC_API_KEY', ''),
    account_id=os.getenv('NEW_RELIC_ACCOUNT_ID', '')
)

# Endpoint para consultar resultados dos agentes inteligentes
@app.get("/api/auto_agents/results")
async def get_auto_agents_results():
    """Retorna os resultados da última execução dos agentes de auto-correção e otimização."""
    results = {}
    try:
        if auto_fix_agent:
            fix_result = auto_fix_agent.run()
            results['auto_fix_agent'] = {
                'last_run': fix_result.get('last_run'),
                'errors': fix_result.get('errors'),
                'suggestions': fix_result.get('suggestions'),
                'test_output': fix_result.get('test_output')
            }
        if auto_optimize_agent:
            optimizations = auto_optimize_agent.scan_code()
            results['auto_optimize_agent'] = {
                'suggestions': optimizations
            }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return results

# ...existing code...
import os
# Inicializa o agente New Relic manualmente no Windows
try:
    import newrelic.agent
    newrelic.agent.initialize('newrelic.ini')
    print("[NEWRELIC] Agente New Relic inicializado via código.")
except ImportError:
    print("[NEWRELIC] Pacote newrelic não encontrado. Monitoramento New Relic não será ativado.")
from dotenv import load_dotenv
load_dotenv()
import os
print("[DEBUG] NEW_RELIC_API_KEY:", os.getenv("NEW_RELIC_API_KEY"))
print("[DEBUG] NEW_RELIC_QUERY_KEY:", os.getenv("NEW_RELIC_QUERY_KEY"))
print("[DEBUG] NEW_RELIC_ACCOUNT_ID:", os.getenv("NEW_RELIC_ACCOUNT_ID"))
print("[DEBUG] OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

import sys
import json
import logging
import aiofiles
import traceback
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import re
import asyncio



# Inicializa o sistema de cache durante o startup
try:
    import utils.cache_integration
    print("Sistema de cache avançado inicializado")
except ImportError as e:
    print(f"Aviso: não foi possível inicializar o sistema de cache avançado: {e}")
    print("O sistema continuará funcionando com o cache padrão")

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken não disponível. Usando fallback para contagem de tokens.")

# Importar o router principal
try:
    from core_router import api_router
except ImportError:
    # Fallback para quando executado de outra pasta
    from backend.core_router import api_router

import uvicorn
from core_inteligente.agno_agent import auto_fix_agent, auto_optimize_agent

import uvicorn
from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Request, APIRouter
from middleware.agno_proxy import add_agno_middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader

# Configuração de logging
# Garante que o diretório de logs existe
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/analyst_ia.log',
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

# Configuração da aplicação
app = FastAPI(
    title="Analyst-IA API",
    description="Backend FastAPI para análise de métricas e IA contextual",
    version="2.0.0"
)

# Adicionar middleware para redirecionar /agno para /api/agno
app = add_agno_middleware(app)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluir os endpoints do router principal
app.include_router(api_router, prefix="/api")


# Incluir os endpoints inteligentes do Agno (sem try/except para exibir qualquer erro de importação)
from routers.agno_router import router as agno_router
app.include_router(agno_router, prefix="/agno", tags=["Agno IA"])
print("[AGNO] Endpoints inteligentes do Agno IA disponíveis em /agno")

# Criar diretório de dados se não existir
os.makedirs("dados", exist_ok=True)

class ChatInput(BaseModel):
    pergunta: str = ""

class MetricsResponse(BaseModel):
    entidades: list

class ChatResponse(BaseModel):
    resposta: str
    contexto: Optional[Dict[str, Any]] = None

from utils.newrelic_collector import coletar_contexto_completo, safe_first, NewRelicCollector

# Importa o coletor avançado se disponível
try:
    from utils.newrelic_advanced_collector import collect_full_data as coletar_contexto_avancado
    COLETOR_AVANCADO_DISPONIVEL = True
    logger.info("✅ Coletor avançado do New Relic disponível e será utilizado por padrão")
except ImportError:
    COLETOR_AVANCADO_DISPONIVEL = False
    logger.warning("⚠️ Coletor avançado do New Relic não disponível, usando coletor padrão")

from utils.persona_detector import detectar_persona, montar_prompt_por_persona
from utils.openai_connector import gerar_resposta_ia
from utils.cache import (
    get_cache, cache_updater_loop, diagnosticar_cache, 
    buscar_no_cache_por_pergunta, forcar_atualizacao_cache,
    atualizar_cache_completo
)
import asyncio
from utils.entity_processor import filter_entities_with_data, process_entity_details
from utils.intent_extractor import extract_metrics_for_query
from utils.context_enricher import context_enricher
from utils.learning_integration import learning_integration

# Instancia o coletor New Relic para health checks
newrelic_collector = NewRelicCollector(
    api_key=os.getenv('NEW_RELIC_API_KEY', ''),
    account_id=os.getenv('NEW_RELIC_ACCOUNT_ID', '')
)

# Endpoint para consultar resultados dos agentes inteligentes
@app.get("/api/auto_agents/results")
async def get_auto_agents_results():
    """Retorna os resultados da última execução dos agentes de auto-correção e otimização."""
    results = {}
    try:
        if auto_fix_agent:
            fix_result = auto_fix_agent.run()
            results['auto_fix_agent'] = {
                'last_run': fix_result.get('last_run'),
                'errors': fix_result.get('errors'),
                'suggestions': fix_result.get('suggestions'),
                'test_output': fix_result.get('test_output')
            }
        if auto_optimize_agent:
            optimizations = auto_optimize_agent.scan_code()
            results['auto_optimize_agent'] = {
                'suggestions': optimizations
            }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return results

# Mover o endpoint para depois da definição do app

# ...existing code...
import os
# Inicializa o agente New Relic manualmente no Windows
try:
    import newrelic.agent
    newrelic.agent.initialize('newrelic.ini')
    print("[NEWRELIC] Agente New Relic inicializado via código.")
except ImportError:
    print("[NEWRELIC] Pacote newrelic não encontrado. Monitoramento New Relic não será ativado.")
from dotenv import load_dotenv
load_dotenv()
import os
print("[DEBUG] NEW_RELIC_API_KEY:", os.getenv("NEW_RELIC_API_KEY"))
print("[DEBUG] NEW_RELIC_QUERY_KEY:", os.getenv("NEW_RELIC_QUERY_KEY"))
print("[DEBUG] NEW_RELIC_ACCOUNT_ID:", os.getenv("NEW_RELIC_ACCOUNT_ID"))
print("[DEBUG] OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

import sys
import json
import logging
import aiofiles
import traceback
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import re
import asyncio



# Inicializa o sistema de cache durante o startup
try:
    import utils.cache_integration
    print("Sistema de cache avançado inicializado")
except ImportError as e:
    print(f"Aviso: não foi possível inicializar o sistema de cache avançado: {e}")
    print("O sistema continuará funcionando com o cache padrão")

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken não disponível. Usando fallback para contagem de tokens.")

# Importar o router principal
try:
    from core_router import api_router
except ImportError:
    # Fallback para quando executado de outra pasta
    from backend.core_router import api_router

import uvicorn
from core_inteligente.agno_agent import auto_fix_agent, auto_optimize_agent

import uvicorn
from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Request, APIRouter
from middleware.agno_proxy import add_agno_middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader

# Configuração de logging
# Garante que o diretório de logs existe
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/analyst_ia.log',
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

# Configuração da aplicação
app = FastAPI(
    title="Analyst-IA API",
    description="Backend FastAPI para análise de métricas e IA contextual",
    version="2.0.0"
)

# Adicionar middleware para redirecionar /agno para /api/agno
app = add_agno_middleware(app)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluir os endpoints do router principal
app.include_router(api_router, prefix="/api")


# Incluir os endpoints inteligentes do Agno (sem try/except para exibir qualquer erro de importação)
from routers.agno_router import router as agno_router
app.include_router(agno_router, prefix="/agno", tags=["Agno IA"])
print("[AGNO] Endpoints inteligentes do Agno IA disponíveis em /agno")

# Criar diretório de dados se não existir
os.makedirs("dados", exist_ok=True)

class ChatInput(BaseModel):
    pergunta: str = ""

class MetricsResponse(BaseModel):
    entidades: list

class ChatResponse(BaseModel):
    resposta: str
    contexto: Optional[Dict[str, Any]] = None

from utils.newrelic_collector import coletar_contexto_completo, safe_first, NewRelicCollector

# Importa o coletor avançado se disponível
try:
    from utils.newrelic_advanced_collector import collect_full_data as coletar_contexto_avancado
    COLETOR_AVANCADO_DISPONIVEL = True
    logger.info("✅ Coletor avançado do New Relic disponível e será utilizado por padrão")
except ImportError:
    COLETOR_AVANCADO_DISPONIVEL = False
    logger.warning("⚠️ Coletor avançado do New Relic não disponível, usando coletor padrão")

from utils.persona_detector import detectar_persona, montar_prompt_por_persona
from utils.openai_connector import gerar_resposta_ia
from utils.cache import (
    get_cache, cache_updater_loop, diagnosticar_cache, 
    buscar_no_cache_por_pergunta, forcar_atualizacao_cache,
    atualizar_cache_completo
)
import asyncio
from utils.entity_processor import filter_entities_with_data, process_entity_details
from utils.intent_extractor import extract_metrics_for_query
from utils.context_enricher import context_enricher
from utils.learning_integration import learning_integration

# Instancia o coletor New Relic para health checks
newrelic_collector = NewRelicCollector(
    api_key=os.getenv('NEW_RELIC_API_KEY', ''),
    account_id=os.getenv('NEW_RELIC_ACCOUNT_ID', '')
)

# Endpoint para consultar resultados dos agentes inteligentes
@app.get("/api/auto_agents/results")
async def get_auto_agents_results():
    """Retorna os resultados da última execução dos agentes de auto-correção e otimização."""
    results = {}
    try:
        if auto_fix_agent:
            fix_result = auto_fix_agent.run()
            results['auto_fix_agent'] = {
                'last_run': fix_result.get('last_run'),
                'errors': fix_result.get('errors'),
                'suggestions': optimizations
            }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return results

# ...existing code...
import os
# Inicializa o agente New Relic manualmente no Windows
try:
    import newrelic.agent
    newrelic.agent.initialize('newrelic.ini')
    print("[NEWRELIC] Agente New Relic inicializado via código.")
except ImportError:
    print("[NEWRELIC] Pacote newrelic não encontrado. Monitoramento New Relic não será ativado.")
from dotenv import load_dotenv
load_dotenv()
import os
print("[DEBUG] NEW_RELIC_API_KEY:", os.getenv("NEW_RELIC_API_KEY"))
print("[DEBUG] NEW_RELIC_QUERY_KEY:", os.getenv("NEW_RELIC_QUERY_KEY"))
print("[DEBUG] NEW_RELIC_ACCOUNT_ID:", os.getenv("NEW_RELIC_ACCOUNT_ID"))
print("[DEBUG] OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

import sys
import json
import logging
import aiofiles
import traceback
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import re
import asyncio



# Inicializa o sistema de cache durante o startup
try:
    import utils.cache_integration
    print("Sistema de cache avançado inicializado")
except ImportError as e:
    print(f"Aviso: não foi possível inicializar o sistema de cache avançado: {e}")
    print("O sistema continuará funcionando com o cache padrão")

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken não disponível. Usando fallback para contagem de tokens.")

# Importar o router principal
try:
    from core_router import api_router
except ImportError:
    # Fallback para quando executado de outra pasta
    from backend.core_router import api_router

import uvicorn
from core_inteligente.agno_agent import auto_fix_agent, auto_optimize_agent

import uvicorn
from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Request, APIRouter
from middleware.agno_proxy import add_agno_middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader

# Configuração de logging
# Garante que o diretório de logs existe
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/analyst_ia.log',
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

# Configuração da aplicação
app = FastAPI(
    title="Analyst-IA API",
    description="Backend FastAPI para análise de métricas e IA contextual",
    version="2.0.0"
)

# Adicionar middleware para redirecionar /agno para /api/agno
app = add_agno_middleware(app)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluir os endpoints do router principal
app.include_router(api_router, prefix="/api")


# Incluir os endpoints inteligentes do Agno (sem try/except para exibir qualquer erro de importação)
from routers.agno_router import router as agno_router
app.include_router(agno_router, prefix="/agno", tags=["Agno IA"])
print("[AGNO] Endpoints inteligentes do Agno IA disponíveis em /agno")

# Criar diretório de dados se não existir
os.makedirs("dados", exist_ok=True)

class ChatInput(BaseModel):
    pergunta: str = ""

class MetricsResponse(BaseModel):
    entidades: list

class ChatResponse(BaseModel):
    resposta: str
    contexto: Optional[Dict[str, Any]] = None

from utils.newrelic_collector import coletar_contexto_completo, safe_first, NewRelicCollector

# Importa o coletor avançado se disponível
try:
    from utils.newrelic_advanced_collector import collect_full_data as coletar_contexto_avancado
    COLETOR_AVANCADO_DISPONIVEL = True
    logger.info("✅ Coletor avançado do New Relic disponível e será utilizado por padrão")
except ImportError:
    COLETOR_AVANCADO_DISPONIVEL = False
    logger.warning("⚠️ Coletor avançado do New Relic não disponível, usando coletor padrão")

from utils.persona_detector import detectar_persona, montar_prompt_por_persona
from utils.openai_connector import gerar_resposta_ia
from utils.cache import (
    get_cache, cache_updater_loop, diagnosticar_cache, 
    buscar_no_cache_por_pergunta, forcar_atualizacao_cache,
    atualizar_cache_completo
)
import asyncio
from utils.entity_processor import filter_entities_with_data, process_entity_details
from utils.intent_extractor import extract_metrics_for_query
from utils.context_enricher import context_enricher
from utils.learning_integration import learning_integration

# Instancia o coletor New Relic para health checks
newrelic_collector = NewRelicCollector(
    api_key=os.getenv('NEW_RELIC_API_KEY', ''),
    account_id=os.getenv('NEW_RELIC_ACCOUNT_ID', '')
)

# Endpoint para consultar resultados dos agentes inteligentes
@app.get("/api/auto_agents/results")
async def get_auto_agents_results():
    """Retorna os resultados da última execução dos agentes de auto-correção e otimização."""
    results = {}
    try:
        if auto_fix_agent:
            fix_result = auto_fix_agent.run()
            results['auto_fix_agent'] = {
                'last_run': fix_result.get('last_run'),
                'errors': fix_result.get('errors'),
                'suggestions': fix_result.get('suggestions'),
                'test_output': fix_result.get('test_output')
            }
        if auto_optimize_agent:
            optimizations = auto_optimize_agent.scan_code()
            results['auto_optimize_agent'] = {
                'suggestions': optimizations
            }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return results

# ...existing code...
import os
# Inicializa o agente New Relic manualmente no Windows
try:
    import newrelic.agent
    newrelic.agent.initialize('newrelic.ini')
    print("[NEWRELIC] Agente New Relic inicializado via código.")
except ImportError:
    print("[NEWRELIC] Pacote newrelic não encontrado. Monitoramento New Relic não será ativado.")
from dotenv import load_dotenv
load_dotenv()
import os
print("[DEBUG] NEW_RELIC_API_KEY:", os.getenv("NEW_RELIC_API_KEY"))
print("[DEBUG] NEW_RELIC_QUERY_KEY:", os.getenv("NEW_RELIC_QUERY_KEY"))
print("[DEBUG] NEW_RELIC_ACCOUNT_ID:", os.getenv("NEW_RELIC_ACCOUNT_ID"))
print("[DEBUG] OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

import sys
import json
import logging
import aiofiles
import traceback
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import re
import asyncio



# Inicializa o sistema de cache durante o startup
try:
    import utils.cache_integration
    print("Sistema de cache avançado inicializado")
except ImportError as e:
    print(f"Aviso: não foi possível inicializar o sistema de cache avançado: {e}")
    print("O sistema continuará funcionando com o cache padrão")

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken não disponível. Usando fallback para contagem de tokens.")

# Importar o router principal
try:
    from core_router import api_router
except ImportError:
    # Fallback para quando executado de outra pasta
    from backend.core_router import api_router

import uvicorn
from core_inteligente.agno_agent import auto_fix_agent, auto_optimize_agent

import uvicorn
from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Request, APIRouter
from middleware.agno_proxy import add_agno_middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader

# Configuração de logging
# Garante que o diretório de logs existe
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/analyst_ia.log',
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

# Configuração da aplicação
app = FastAPI(
    title="Analyst-IA API",
    description="Backend FastAPI para análise de métricas e IA contextual",
    version="2.0.0"
)

# Adicionar middleware para redirecionar /agno para /api/agno
app = add_agno_middleware(app)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluir os endpoints do router principal
app.include_router(api_router, prefix="/api")


# Incluir os endpoints inteligentes do Agno (sem try/except para exibir qualquer erro de importação)
from routers.agno_router import router as agno_router
app.include_router(agno_router, prefix="/agno", tags=["Agno IA"])
print("[AGNO] Endpoints inteligentes do Agno IA disponíveis em /agno")

# Criar diretório de dados se não existir
os.makedirs("dados", exist_ok=True)

class ChatInput(BaseModel):
    pergunta: str = ""

class MetricsResponse(BaseModel):
    entidades: list

class ChatResponse(BaseModel):
    resposta: str
    contexto: Optional[Dict[str, Any]] = None

from utils.newrelic_collector import coletar_contexto_completo, safe_first, NewRelicCollector

# Importa o coletor avançado se disponível
try:
    from utils.newrelic_advanced_collector import collect_full_data as coletar_contexto_avancado
    COLETOR_AVANCADO_DISPONIVEL = True
    logger.info("✅ Coletor avançado do New Relic disponível e será utilizado por padrão")
except ImportError:
    COLETOR_AVANCADO_DISPONIVEL = False
    logger.warning("⚠️ Coletor avançado do New Relic não disponível, usando coletor padrão")

from utils.persona_detector import detectar_persona, montar_prompt_por_persona
from utils.openai_connector import gerar_resposta_ia
from utils.cache import (
    get_cache, cache_updater_loop, diagnosticar_cache, 
    buscar_no_cache_por_pergunta, forcar_atualizacao_cache,
    atualizar_cache_completo
)
import asyncio
from utils.entity_processor import filter_entities_with_data, process_entity_details
from utils.intent_extractor import extract_metrics_for_query
from utils.context_enricher import context_enricher
from utils.learning_integration import learning_integration

# Instancia o coletor New Relic para health checks
newrelic_collector = NewRelicCollector(
    api_key=os.getenv('NEW_RELIC_API_KEY', ''),
    account_id=os.getenv('NEW_RELIC_ACCOUNT_ID', '')
)

# Endpoint para consultar resultados dos agentes inteligentes
@app.get("/api/auto_agents/results")
async def get_auto_agents_results():
    """Retorna os resultados da última execução dos agentes de auto-correção e otimização."""
    results = {}
    try:
        if auto_fix_agent:
            fix_result = auto_fix_agent.run()
            results['auto_fix_agent'] = {
                'last_run': fix_result.get('last_run'),
                'errors': fix_result.get('errors'),
                'suggestions': fix_result.get('suggestions'),
                'test_output': fix_result.get('test_output')
            }
        if auto_optimize_agent:
            optimizations = auto_optimize_agent.scan_code()
            results['auto_optimize_agent'] = {
                'suggestions': optimizations
            }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return results

# ...existing code...
import os
# Inicializa o agente New Relic manualmente no Windows
try:
    import newrelic.agent
    newrelic.agent.initialize('newrelic.ini')
    print("[NEWRELIC] Agente New Relic inicializado via código.")
except ImportError:
    print("[NEWRELIC] Pacote newrelic não encontrado. Monitoramento New Relic não será ativado.")
from dotenv import load_dotenv
load_dotenv()
import os
print("[DEBUG] NEW_RELIC_API_KEY:", os.getenv("NEW_RELIC_API_KEY"))
print("[DEBUG] NEW_RELIC_QUERY_KEY:", os.getenv("NEW_RELIC_QUERY_KEY"))
print("[DEBUG] NEW_RELIC_ACCOUNT_ID:", os.getenv("NEW_RELIC_ACCOUNT_ID"))
print("[DEBUG] OPENAI_API_KEY:", os.getenv("OPENAI_API_KEY"))

import sys
import json
import logging
import aiofiles
import traceback
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import re
import asyncio



# Inicializa o sistema de cache durante o startup
try:
    import utils.cache_integration
    print("Sistema de cache avançado inicializado")
except ImportError as e:
    print(f"Aviso: não foi possível inicializar o sistema de cache avançado: {e}")
    print("O sistema continuará funcionando com o cache padrão")

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken não disponível. Usando fallback para contagem de tokens.")

# Importar o router principal
try:
    from core_router import api_router
except ImportError:
    # Fallback para quando executado de outra pasta
    from backend.core_router import api_router

import uvicorn
from core_inteligente.agno_agent import auto_fix_agent, auto_optimize_agent

import uvicorn
from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Request, APIRouter
from middleware.agno_proxy import add_agno_middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader

# Configuração de logging
# Garante que o diretório de logs existe
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/analyst_ia.log',
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

# Configuração da aplicação
app = FastAPI(
    title="Analyst-IA API",
    description="Backend FastAPI para análise de métricas e IA contextual",
    version="2.0.0"
)

# Adicionar middleware para redirecionar /agno para /api/agno
app = add_agno_middleware(app)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluir os endpoints do router principal
app.include_router(api_router, prefix="/api")
