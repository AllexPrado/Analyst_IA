@echo off
echo Iniciando Interface de Comunicacao com o Agno...
echo.

:: Configurar PYTHONPATH para incluir o diretorio atual
set PYTHONPATH=%~dp0;%PYTHONPATH%

:: Verificar status dos agentes
echo Verificando status dos agentes...
python -c "import sys; sys.path.append('%~dp0'); import asyncio; from core_inteligente.agno_interface import AgnoInterface; interface = AgnoInterface(); interface.iniciar_sessao(); asyncio.run(interface.verificar_status())" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo AVISO: Nao foi possivel verificar o status dos agentes.
    echo O sistema continuara, mas pode haver problemas de comunicacao.
    echo.
)

echo.
echo Digite suas mensagens para o Agno. Digite 'sair' para terminar.
echo.

:LOOP
set /p MENSAGEM="Voce: "

if "%MENSAGEM%"=="sair" goto :FIM
if "%MENSAGEM%"=="exit" goto :FIM

:: Enviar mensagem para o Agno
python -c "import sys; sys.path.append('%~dp0'); import asyncio; from core_inteligente.agno_interface import falar_com_agno; resultado = asyncio.run(falar_com_agno(r'''%MENSAGEM%''')); print(f'Agno: {resultado.get(\"mensagem\", \"Sem resposta disponivel.\")}')"
if %ERRORLEVEL% NEQ 0 (
    echo Erro ao processar sua mensagem. Verifique se o sistema MPC esta em execucao.
)

goto :LOOP

:FIM
echo Encerrando conversa com o Agno.

:FIM
echo Encerrando conversa com o Agno.
