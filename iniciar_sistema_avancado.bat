@echo off
echo ==============================================================
echo Inicializando Sistema Analyst IA com Infraestrutura Avancada
echo ==============================================================

echo.
echo Verificando Cache Avancado...
python regenerar_cache_avancado.py

echo.
echo Verificando e Corrigindo Cache Principal...
cd backend
python check_and_fix_cache.py
cd ..

echo.
echo Iniciando Sistema Completo...
start cmd.exe /k "cd backend && python main.py"

echo Aguardando o backend iniciar...
timeout /t 5 /nobreak > nul

echo Iniciando frontend...
cd frontend
npm run dev

echo.
echo Sistema inicializado com sucesso!
pause
