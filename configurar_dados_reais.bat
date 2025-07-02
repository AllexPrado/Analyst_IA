@echo off
echo ===============================================================
echo       ANALISTA_IA - CONFIGURACAO DE DADOS REAIS
echo ===============================================================
echo.
echo Este script ajuda a configurar o sistema para usar dados reais
echo do New Relic em vez de dados simulados.
echo.
echo Passo 1: Verificando configuracao atual...
python verificar_config_dados_reais.py
echo.
echo Passo 2: Se voce ja configurou suas credenciais no arquivo .env,
echo          podemos integrar os dados reais agora.
echo.

set /p CONTINUE=Deseja continuar com a integracao de dados reais? (S/N): 
if /i "%CONTINUE%"=="S" (
    echo.
    echo Iniciando integracao de dados reais...
    echo.
    python integrar_dados_reais_newrelic.py
    echo.
    echo Integracao concluida. Agora voce pode iniciar o sistema completo 
    echo com dados reais usando o comando:
    echo.
    echo iniciar_sistema_com_dados_reais.bat
    echo.
) else (
    echo.
    echo Operacao cancelada pelo usuario.
    echo.
    echo Para integrar dados reais mais tarde, configure o arquivo .env
    echo e execute: python integrar_dados_reais_newrelic.py
    echo.
)

pause
