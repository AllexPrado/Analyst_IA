# Execute este script para iniciar a otimização e execução do sistema completo
# Uso: powershell -ExecutionPolicy Bypass -File .\executar_otimizacao.ps1

Write-Host "=== INICIANDO OTIMIZAÇÃO E EXECUÇÃO DO SISTEMA ===" -ForegroundColor Cyan

# Passo 1: Executar otimização
Write-Host "1. Executando otimização do sistema..." -ForegroundColor Yellow
python otimizar_sistema.py

# Passo 2: Iniciar o backend
Write-Host "2. Iniciando backend..." -ForegroundColor Yellow
$backendPath = Join-Path -Path $PSScriptRoot -ChildPath "backend"
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd $backendPath && python main.py"

# Passo 3: Iniciar o frontend
Write-Host "3. Iniciando frontend..." -ForegroundColor Yellow
$frontendPath = Join-Path -Path $PSScriptRoot -ChildPath "frontend"
Set-Location -Path $frontendPath
npm run dev

Write-Host "Sistema iniciado com sucesso!" -ForegroundColor Green
