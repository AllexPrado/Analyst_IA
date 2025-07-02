@echo off
echo ========================================
echo Iniciando Sistema Completo Analyst IA
echo ========================================

cd /d "%~dp0"

echo Iniciando Backend em nova janela...
start "Backend Analyst IA" cmd /k "call iniciar_backend.bat"

echo Aguardando 5 segundos para o backend inicializar...
timeout /t 5 /nobreak

echo Iniciando Frontend em nova janela...
start "Frontend Analyst IA" cmd /k "call iniciar_frontend.bat"

echo.
echo ========================================
echo Sistema iniciado com sucesso!
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Pressione qualquer tecla para sair
echo ========================================
pause > nul
