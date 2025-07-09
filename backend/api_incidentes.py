
# Arquivo principal do backend: apenas orquestração do app FastAPI
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Handler de lifespan para inicialização/finalização (delegado aos services)
from services.incidentes_service import lifespan

# Criar aplicativo FastAPI com lifespan
app = FastAPI(
    title="API para Dados de Incidentes",
    description="Endpoints para gerenciamento de incidentes e alertas",
    lifespan=lifespan
)

# Registro dos routers modularizados
from routers.incidentes_router import router as incidentes_router
from routers.entidades_router import router as entidades_router
from routers.analise_router import router as analise_router
from routers.causa_raiz_router import router as causa_raiz_router
from routers.status_router import router as status_router
from routers.correlacionar_router import router as correlacionar_router
from routers.chat_router import router as chat_router

app.include_router(incidentes_router, prefix="/api", tags=["Incidentes"])
app.include_router(entidades_router, prefix="/api", tags=["Entidades"])
app.include_router(analise_router, prefix="/api", tags=["Análise"])
app.include_router(causa_raiz_router, prefix="/api", tags=["Causa Raiz"])
app.include_router(status_router, prefix="/api", tags=["Status"])
app.include_router(correlacionar_router, prefix="/api", tags=["Correlação"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
