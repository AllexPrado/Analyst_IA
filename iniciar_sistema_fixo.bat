@echo off
echo ===== Iniciando Sistema Analyst_IA =====
echo.
echo Verificando e corrigindo o cache...
cd /d %~dp0\backend
python check_and_fix_cache.py
echo.
echo Iniciando Backend...
start cmd /k "cd /d %~dp0\backend && python main.py"
echo.
echo Aguardando backend iniciar (5 segundos)...
timeout /t 5 /nobreak
echo.
echo Iniciando Frontend...
cd /d %~dp0\frontend
npm run dev
