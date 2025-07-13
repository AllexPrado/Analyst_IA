@echo off
:: Script para iniciar o monitoramento local automaticamente
:: Salve este arquivo como "iniciar_monitoramento.bat" e crie um atalho na pasta de inicialização do Windows

echo Iniciando monitoramento local do Analyst_IA...
cd /d "d:\projetos\Analyst_IA\backend"

:: Verifica se Python está instalado
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python não encontrado! Verifique a instalação.
    pause
    exit /b 1
)

:: Inicia o monitoramento local em segundo plano
start "Monitoramento Local Analyst_IA" /min python monitoramento_local.py

echo Monitoramento iniciado em segundo plano.
echo Para verificar o status, execute: python monitoramento_local.py --once
timeout /t 5
exit
