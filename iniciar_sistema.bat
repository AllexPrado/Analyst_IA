@echo off
REM Script para iniciar todo o sistema Analyst-IA
echo Iniciando sistema completo Analyst-IA...

REM Verificar se Python está instalado
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Erro: Python não encontrado. Por favor instale Python 3.8 ou superior.
    exit /b 1
)

REM Verificar se Node.js está instalado
where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Aviso: Node.js não encontrado. Apenas o backend será iniciado.
    set NODE_INSTALLED=false
) else (
    set NODE_INSTALLED=true
)

REM Iniciar o backend unificado em uma nova janela
echo Iniciando backend unificado...
start "Analyst-IA Backend" cmd /k "python start_unified_backend.py"

REM Aguardar alguns segundos para o backend iniciar
echo Aguardando o backend inicializar...
timeout /t 5 /nobreak >nul

REM Verificar se o backend está funcionando
echo Verificando se o backend está operacional...
curl -s http://localhost:8000/api/status >nul
if %ERRORLEVEL% neq 0 (
    echo Aviso: Backend pode não ter iniciado corretamente. Verificando novamente...
    timeout /t 5 /nobreak >nul
    
    curl -s http://localhost:8000/api/status >nul
    if %ERRORLEVEL% neq 0 (
        echo Erro: Não foi possível conectar ao backend. Verifique os logs para mais detalhes.
        echo Tentando continuar mesmo assim...
    ) else (
        echo Backend está operacional!
    )
) else (
    echo Backend está operacional!
)

REM Iniciar o frontend se Node.js estiver instalado
if %NODE_INSTALLED% == true (
    echo Iniciando frontend...
    cd frontend
    
    REM Verificar se node_modules existe, se não, instalar dependências
    if not exist "node_modules\" (
        echo Instalando dependências do frontend...
        npm install
        if %ERRORLEVEL% neq 0 (
            echo Erro: Falha ao instalar dependências do frontend.
            exit /b 1
        )
    )
    
    REM Iniciar o frontend em uma nova janela
    start "Analyst-IA Frontend" cmd /k "npm run dev"
    
    echo Frontend iniciando em http://localhost:5173
) else (
    echo Pulando inicialização do frontend porque Node.js não foi encontrado.
)

echo.
echo Sistema Analyst-IA está iniciando!
echo - Backend: http://localhost:8000
if %NODE_INSTALLED% == true (
    echo - Frontend: http://localhost:5173
)
echo.
echo IMPORTANTE: Para encerrar o sistema, feche as janelas de terminal criadas.

exit /b 0
