@echo off
echo Iniciando Sistema Analyst-IA...
echo ===================================

:: Verifica se Python está instalado
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado!
    echo Por favor, instale o Python 3.8 ou superior.
    echo Voce pode baixa-lo de: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Verifica se o script de inicialização existe
if not exist iniciar_sistema_completo.py (
    echo ERRO: Arquivo iniciar_sistema_completo.py nao encontrado!
    pause
    exit /b 1
)

:: Executa o script de inicialização
echo Executando script de inicializacao...
python iniciar_sistema_completo.py

echo.
echo Pressione qualquer tecla para sair...
pause > nul
