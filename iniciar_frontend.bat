@echo off
echo ===================================
echo Iniciando Frontend do Analyst IA
echo ===================================

cd /d "%~dp0"

echo Mudando para pasta frontend...
cd frontend

echo Verificando se node_modules existe...
if not exist "node_modules" (
    echo Instalando dependencias do npm...
    npm install
)

echo Iniciando servidor de desenvolvimento...
npm run dev

pause
