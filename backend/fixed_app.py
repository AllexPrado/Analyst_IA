"""
Fixed FastAPI application with clear router structure.
This script addresses the router duplication issue in the main application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from pathlib import Path
import uvicorn

# Configure logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/fixed_app.log',
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)

# Create the FastAPI application
app = FastAPI(
    title="Analyst-IA API (Fixed)",
    description="Backend FastAPI com estrutura de routers corrigida",
    version="2.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import core_router (which already includes agno_router properly)
from core_router import api_router

# Include the core router
app.include_router(api_router, prefix="/api")

# Create data directory if it doesn't exist
os.makedirs("dados", exist_ok=True)

# This avoids duplicating agno_router, which is already included in core_router
# The proper access to agno endpoints should be through /api/agno/...

if __name__ == "__main__":
    logger.info("Starting fixed FastAPI application")
    uvicorn.run(app, host="0.0.0.0", port=8000)
