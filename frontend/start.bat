@echo off
REM Script para inicializar o frontend do Analyst_IA no Windows
REM Este script facilita o desenvolvimento e teste da aplicação

echo 🚀 Iniciando Analyst_IA Frontend...

REM Verificar se Node.js está instalado
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js não encontrado. Por favor, instale Node.js primeiro.
    pause
    exit /b 1
)

REM Verificar se npm está instalado
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm não encontrado. Por favor, instale npm primeiro.
    pause
    exit /b 1
)

REM Verificar se estamos no diretório correto
if not exist "package.json" (
    echo ❌ package.json não encontrado. Execute este script no diretório frontend.
    pause
    exit /b 1
)

echo 📦 Instalando dependências...
npm install

if %errorlevel% neq 0 (
    echo ❌ Erro ao instalar dependências.
    pause
    exit /b 1
)

echo 🔍 Verificando se o backend está rodando...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend está online na porta 8000
) else (
    echo ⚠️  Backend não está respondendo na porta 8000
    echo    Por favor, certifique-se de que o backend está rodando:
    echo    cd ..\backend ^&^& python main.py
)

echo 🎯 Iniciando servidor de desenvolvimento...
echo    Frontend será executado em: http://localhost:5173
echo    Pressione Ctrl+C para parar

npm run dev

pause
