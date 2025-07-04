# Script para iniciar o sistema Analyst_IA de forma otimizada
# Executar como: powershell -ExecutionPolicy Bypass -File .\iniciar_sistema_otimizado.ps1

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "          INICIAR ANALYST IA OTIMIZADO" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se Python está instalado
$pythonInstalled = $null
try {
    $pythonInstalled = Get-Command python -ErrorAction Stop
    Write-Host "[OK] Python encontrado: $($pythonInstalled.Version)" -ForegroundColor Green
}
catch {
    Write-Host "[ERRO] Python não encontrado! Instale o Python 3.8+ e tente novamente." -ForegroundColor Red
    Read-Host "Pressione ENTER para sair"
    exit 1
}

# Verificar se Node.js está instalado
$nodeInstalled = $null
try {
    $nodeInstalled = Get-Command node -ErrorAction Stop
    Write-Host "[OK] Node.js encontrado: $((node -v))" -ForegroundColor Green
}
catch {
    Write-Host "[ERRO] Node.js não encontrado! Instale o Node.js e tente novamente." -ForegroundColor Red
    Read-Host "Pressione ENTER para sair"
    exit 1
}

Write-Host ""
Write-Host "[1/4] Verificando dependências Python..." -ForegroundColor Yellow
Set-Location -Path "backend"
pip install -r requirements.txt

Write-Host ""
Write-Host "[2/4] Verificando cache e dados..." -ForegroundColor Yellow
python check_and_fix_cache.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[AVISO] Problemas detectados com o cache. Tentando corrigir..." -ForegroundColor Yellow
    python .\otimizar_sistema.py
}

Write-Host ""
Write-Host "[3/4] Iniciando backend..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd $PWD && python main.py"

Write-Host ""
Write-Host "[4/4] Iniciando frontend..." -ForegroundColor Yellow
Set-Location -Path "../frontend"
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Falha ao instalar dependências do frontend!" -ForegroundColor Red
    Read-Host "Pressione ENTER para sair"
    exit 1
}

Write-Host ""
Write-Host "Iniciando servidor de desenvolvimento do frontend..." -ForegroundColor Cyan
npm run dev

Write-Host ""
Write-Host "Sistema iniciado com sucesso!" -ForegroundColor Green
