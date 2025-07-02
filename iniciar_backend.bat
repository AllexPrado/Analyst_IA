@echo off
echo ===================================
echo Iniciando Backend do Analyst IA
echo ===================================

cd /d "%~dp0"

echo Ativando ambiente virtual...
call .venv\Scripts\activate.bat

echo Verificando dependencias...
pip install fastapi uvicorn python-dotenv openai requests aiohttp

echo Mudando para pasta backend...
cd backend

echo Iniciando servidor FastAPI...
uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
