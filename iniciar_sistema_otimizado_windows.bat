@echo off
echo ===================================================
echo          INICIAR ANALYST IA OTIMIZADO
echo ===================================================
echo.

REM Verificar se Python está instalado
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Python nao encontrado! Instale o Python 3.8+ e tente novamente.
    pause
    exit /b 1
)

REM Verificar se Node.js está instalado
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Node.js nao encontrado! Instale o Node.js e tente novamente.
    pause
    exit /b 1
)

echo [1/4] Executando otimizacao do sistema...
python otimizar_sistema.py
if %ERRORLEVEL% NEQ 0 (
    echo [AVISO] A otimizacao encontrou alguns problemas.
    pause
)

echo.
echo [2/4] Verificando cache e dados...
cd backend
python check_and_fix_cache.py
if %ERRORLEVEL% NEQ 0 (
    echo [AVISO] Problemas detectados com o cache. Tentando corrigir...
    echo.
    python corrigir_cache_dados_reais.py
)

echo.
echo [3/4] Iniciando backend...
start cmd /c "cd %CD% && python main.py"

echo.
echo [4/4] Iniciando frontend...
cd ..\frontend
npm install
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Falha ao instalar dependencias do frontend!
    pause
    exit /b 1
)

echo.
echo Iniciando servidor de desenvolvimento do frontend...
npm run dev

echo.
echo Sistema iniciado com sucesso!
