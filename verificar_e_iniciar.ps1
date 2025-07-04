# Script PowerShell para verificar o status do sistema Analyst_IA e iniciar com dados reais
Write-Host "========================================" -ForegroundColor Green
Write-Host "Verificador de Status - Analyst IA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Muda para o diretório do script
Set-Location $PSScriptRoot

# Verifica se o arquivo .env existe
if (-not (Test-Path ".env")) {
    Write-Host "❌ Arquivo .env não encontrado!" -ForegroundColor Red
    Write-Host "Criando arquivo .env básico..." -ForegroundColor Yellow
    
    @"
# Credenciais do New Relic
NEW_RELIC_API_KEY=your_api_key_here
NEW_RELIC_ACCOUNT_ID=your_account_id_here
NEW_RELIC_QUERY_KEY=your_query_key_here

# Configurações do sistema
USE_SIMULATED_DATA=true
"@ | Out-File -FilePath ".env" -Encoding utf8
    
    Write-Host "✅ Arquivo .env criado. Por favor, edite-o com suas credenciais." -ForegroundColor Green
}

# Verifica se o Python está instalado
try {
    $pythonVersion = python --version
    Write-Host "✅ Python detectado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python não encontrado! Por favor, instale o Python antes de continuar." -ForegroundColor Red
    exit 1
}

# Verifica se o Node.js está instalado
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js detectado: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js não encontrado! Por favor, instale o Node.js antes de continuar." -ForegroundColor Red
    exit 1
}

# Verifica se a pasta node_modules existe no frontend
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "⚠️ Módulos npm não encontrados. Instalando dependências..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
}

# NOVO: Verificar e corrigir problemas nas consultas GraphQL
Write-Host "🔍 Verificando e corrigindo consultas GraphQL/NRQL..." -ForegroundColor Cyan
if (Test-Path "corrigir_consultas_newrelic.py") {
    python corrigir_consultas_newrelic.py
    Write-Host "✅ Consultas verificadas e corrigidas" -ForegroundColor Green
} else {
    Write-Host "⚠️ Script corrigir_consultas_newrelic.py não encontrado" -ForegroundColor Yellow
}

# Verificar conectividade com o New Relic
Write-Host "🔌 Verificando conectividade com New Relic..." -ForegroundColor Cyan
if (Test-Path "verificar_conexao_newrelic.py") {
    python verificar_conexao_newrelic.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "⚠️ Problemas de conectividade com New Relic detectados." -ForegroundColor Yellow
        Write-Host "   Sistema usará dados simulados." -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️ Script verificar_conexao_newrelic.py não encontrado" -ForegroundColor Yellow
}

# Verifica e corrige o cache
Write-Host "🔄 Verificando e corrigindo cache..." -ForegroundColor Yellow
Set-Location backend
python check_and_fix_cache.py
Set-Location ..

# Inicia o backend e frontend em janelas separadas
Write-Host "🚀 Iniciando sistema..." -ForegroundColor Green

# Inicia o backend em uma nova janela de PowerShell
Write-Host "🔹 Iniciando backend..." -ForegroundColor Cyan
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; python main.py" -WindowStyle Normal

# Aguarda alguns segundos para garantir que o backend esteja rodando antes de iniciar o frontend
Write-Host "⏳ Aguardando backend iniciar (3 segundos)..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Inicia o frontend em uma nova janela de PowerShell
Write-Host "🔹 Iniciando frontend..." -ForegroundColor Magenta
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev" -WindowStyle Normal

Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Sistema iniciado com sucesso!" -ForegroundColor Green
Write-Host "📡 Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "🌐 Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "📊 Infraestrutura Avançada: http://localhost:5173/infraestrutura-avancada" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
