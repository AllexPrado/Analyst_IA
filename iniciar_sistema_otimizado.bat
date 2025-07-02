@echo off
setlocal enabledelayedexpansion

echo ===== Sistema Analyst_IA: Diagnóstico e Inicialização =====
echo.

REM Verificar se Python está instalado
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: Python não encontrado. Por favor, instale o Python e tente novamente.
    goto :fim
)

REM Verificar se estamos no diretório correto
if not exist frontend\ (
    echo ERRO: Este script deve ser executado no diretório raiz do projeto Analyst_IA.
    goto :fim
)

echo === Etapa 1: Diagnóstico e correção do frontend ===
python diagnostico_frontend.py
if %ERRORLEVEL% NEQ 0 (
    echo AVISO: Diagnóstico do frontend encontrou problemas que não puderam ser corrigidos automaticamente.
    echo        Revise o relatório diagnostico_frontend.json para mais detalhes.
    echo.
    
    choice /C SN /M "Deseja continuar mesmo assim? (S/N)"
    if !ERRORLEVEL! EQU 2 (
        echo Operação cancelada pelo usuário.
        goto :fim
    )
) else (
    echo Frontend diagnosticado e corrigido com sucesso!
)

echo.
echo === Etapa 2: Verificando credenciais do New Relic ===
if "!NEW_RELIC_ACCOUNT_ID!"=="" (
    echo Aviso: Variável NEW_RELIC_ACCOUNT_ID não encontrada.
    set MODO=simulado
) else if "!NEW_RELIC_API_KEY!"=="" (
    echo Aviso: Variável NEW_RELIC_API_KEY não encontrada.
    set MODO=simulado
) else (
    echo Credenciais do New Relic encontradas!
    set MODO=real
)

if "!MODO!"=="simulado" (
    echo AVISO: Usando dados SIMULADOS.
    echo Para usar dados reais, defina as variáveis de ambiente:
    echo   - NEW_RELIC_ACCOUNT_ID
    echo   - NEW_RELIC_API_KEY
    
    choice /C RSD /M "Escolha o modo de inicialização: (R)eal com entrada manual, (S)imulado ou (D)ados reais simulados?"
    
    if !ERRORLEVEL! EQU 1 (
        echo.
        echo === Configuração manual de credenciais ===
        set /p NEW_RELIC_ACCOUNT_ID="Digite o Account ID do New Relic: "
        set /p NEW_RELIC_API_KEY="Digite a API Key do New Relic: "
        set MODO=real
        echo Credenciais configuradas manualmente.
    ) else if !ERRORLEVEL! EQU 2 (
        echo Continuando com modo simulado básico...
    ) else if !ERRORLEVEL! EQU 3 (
        echo Usando dados reais simulados (modo avançado)...
        set MODO=simulado_avancado
    )
) else (
    echo Sistema configurado para usar dados REAIS do New Relic.
)

echo.
echo === Etapa 3: Verificando cache e integridade do sistema ===
python diagnostico_infra_avancada.py
if %ERRORLEVEL% NEQ 0 (
    echo AVISO: Diagnóstico encontrou problemas no cache ou endpoints.
    
    choice /C SR /M "Deseja (S)air ou (R)egenerar o cache e continuar? (S/R)"
    if !ERRORLEVEL! EQU 1 (
        echo Operação cancelada pelo usuário.
        goto :fim
    ) else (
        echo.
        echo === Regenerando cache do sistema ===
        python regenerar_cache_avancado.py
        if %ERRORLEVEL% NEQ 0 (
            echo ERRO: Falha ao regenerar cache. Abortando.
            goto :fim
        ) else (
            echo Cache regenerado com sucesso!
        )
    )
) else (
    echo Cache e endpoints OK!
)

echo.
echo === Etapa 4: Integrando dados ===
if "!MODO!"=="real" (
    echo Integrando dados REAIS do New Relic...
    python integrar_dados_reais_newrelic.py
) else if "!MODO!"=="simulado_avancado" (
    echo Integrando dados simulados avançados...
    python integrar_dados_reais_newrelic.py --simulated
) else (
    echo Usando dados simulados básicos...
)

echo.
echo === Etapa 5: Iniciando sistema completo ===
echo.
echo O sistema será iniciado com os seguintes componentes:
echo  - Backend (Python FastAPI)
echo  - Frontend (Vue.js)
if "!MODO!"=="real" (
    echo  - Sincronização periódica de dados reais
)
echo.
choice /C SN /M "Deseja iniciar o sistema agora? (S/N)"

if !ERRORLEVEL! EQU 2 (
    echo Operação cancelada pelo usuário.
    goto :fim
)

echo.
echo Iniciando backend...
start "Backend Analyst_IA" cmd /c "python backend\main.py"

echo Aguardando inicialização do backend...
timeout /t 5 /nobreak >nul

echo.
echo Iniciando frontend...
cd frontend
start "Frontend Analyst_IA" cmd /c "npm run dev"
cd ..

if "!MODO!"=="real" (
    echo.
    echo Iniciando sincronização periódica de dados...
    start "Sincronização Periódica" cmd /c "python sincronizar_periodico_newrelic.py --intervalo 30"
)

echo.
echo ===== SISTEMA INICIADO COM SUCESSO! =====
echo.
echo Frontend disponível em: http://localhost:3000
echo Backend disponível em: http://localhost:8000

if "!MODO!"=="real" (
    echo Sistema usando dados REAIS do New Relic.
) else if "!MODO!"=="simulado_avancado" (
    echo Sistema usando dados SIMULADOS AVANÇADOS.
) else (
    echo Sistema usando dados SIMULADOS básicos.
)

echo.
echo Pressione qualquer tecla para fechar este prompt (serviços continuarão rodando)
pause >nul

:fim
endlocal
