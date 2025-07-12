@echo off
echo =====================================================
echo REINICIANDO SERVIDOR FASTAPI
echo =====================================================

echo.
echo 1. Matando processos existentes na porta 8000...
FOR /F "tokens=5" %%P IN ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') DO (
    echo Encontrado processo com PID %%P usando a porta 8000
    taskkill /F /PID %%P
)

echo.
echo 2. Iniciando o servidor FastAPI...
start cmd /k "python -m uvicorn main:app --reload"

echo.
echo 3. Aguardando inicialização do servidor (10 segundos)...
timeout /t 10 /nobreak > nul

echo.
echo 4. Testando os endpoints...
python teste_endpoint_agno.py

echo.
echo =====================================================
echo SERVIDOR REINICIADO E ENDPOINTS TESTADOS
echo =====================================================
echo.
echo O servidor está rodando em http://localhost:8000
echo.
