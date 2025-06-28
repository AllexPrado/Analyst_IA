@echo off
echo Iniciando correcoes do Analyst-IA...
echo =====================================

:: Verifica se Python esta instalado
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado!
    echo Por favor, instale o Python 3.8 ou superior.
    echo Voce pode baixa-lo de: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Executa o script de correcao
echo Executando script de correcao...
python corrigir_e_iniciar.py

pause
