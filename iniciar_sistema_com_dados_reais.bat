@echo off
setlocal enabledelayedexpansion

echo ===== Iniciando Sistema Analyst_IA com Dados Reais =====
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

REM Verificar credenciais do New Relic
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
) else (
    echo Sistema configurado para usar dados REAIS do New Relic.
)

echo.
echo === Etapa 1: Integrando dados do New Relic ===
if "!MODO!"=="simulado" (
    python integrar_dados_reais_newrelic.py --simulated
) else (
    python integrar_dados_reais_newrelic.py
)

if %ERRORLEVEL% NEQ 0 (
    echo Aviso: Falha na integração de dados. Continuando com dados existentes.
) else (
    echo Integração de dados concluída com sucesso!
)

echo.
echo === Etapa 2: Iniciando sincronização periódica ===
start "Sincronização Periódica New Relic" cmd /c "python sincronizar_periodico_newrelic.py --intervalo 30"
if %ERRORLEVEL% NEQ 0 (
    echo Aviso: Falha ao iniciar sincronização periódica.
) else (
    echo Sincronização periódica iniciada em segundo plano.
)

echo.
echo === Etapa 3: Verificando e corrigindo cache ===
python backend\check_and_fix_cache.py
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: Falha ao verificar e corrigir cache. Abortando.
    goto :fim
) else (
    echo Cache verificado e corrigido com sucesso!
)

echo.
echo === Etapa 4: Iniciando backend ===
start "Backend Analyst_IA" cmd /c "python backend\main.py"
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: Falha ao iniciar backend. Abortando.
    goto :fim
) else (
    echo Backend iniciado com sucesso!
)

echo Aguardando inicialização do backend...
timeout /t 5 /nobreak >nul

echo.
echo === Etapa 5: Iniciando frontend ===
cd frontend
start "Frontend Analyst_IA" cmd /c "npm run dev"
if %ERRORLEVEL% NEQ 0 (
    echo ERRO: Falha ao iniciar frontend.
    goto :fim
) else (
    echo Frontend iniciado com sucesso!
)
cd ..

echo.
echo ===== SISTEMA INICIADO COM SUCESSO! =====
echo.
echo Frontend disponível em: http://localhost:3000
echo Backend disponível em: http://localhost:8000
echo Dados sendo sincronizados periodicamente
echo.

if "!MODO!"=="simulado" (
    echo ATENÇÃO: Sistema usando dados SIMULADOS.
    echo Para usar dados reais, defina as variáveis de ambiente:
    echo   - NEW_RELIC_ACCOUNT_ID
    echo   - NEW_RELIC_API_KEY
) else (
    echo Sistema usando dados REAIS do New Relic.
)

echo.
echo Pressione qualquer tecla para encerrar este prompt (serviços continuarão rodando)
pause >nul

:fim
endlocal
