@echo off
echo === INICIANDO ANALYST IA OTIMIZADO ===
echo.
echo 1. Verificando cache e dados...
cd backend
python check_and_fix_cache.py

echo.
echo 2. Iniciando backend...
start cmd /c "cd backend && python main.py"

echo.
echo 3. Iniciando frontend...
cd ../frontend
npm run dev
