@echo off
echo ===== Iniciando Correção e Limpeza do Sistema Analyst_IA =====
echo.
echo Verificando e configurando variáveis de ambiente...

rem Configurar para uso de dados reais
echo USE_SIMULATED_DATA=false > .env.temp
for /f "tokens=*" %%a in (.env) do (
    echo %%a | find /i "USE_SIMULATED_DATA=" >nul
    if errorlevel 1 (
        echo %%a >> .env.temp
    )
)
move /y .env.temp .env
echo.

echo 1. Executando limpeza do projeto...
python limpar_projeto.py
echo.

echo 2. Corrigindo sistema para usar dados reais completos...
python corrigir_sistema_completo.py
echo.

echo 3. Atualizando dependências se necessário...
cd backend
pip install -r requirements.txt
cd ..
echo.

echo 4. Verificando e corrigindo cache...
cd backend
python check_and_fix_cache.py
cd ..
echo.

echo ===== Iniciando Sistema Completo =====
echo.
echo Iniciando backend...
start cmd /k "cd backend && python main.py"

echo Aguardando backend iniciar (5 segundos)...
timeout /t 5 /nobreak
echo.

echo Iniciando frontend...
cd frontend
npm run dev
