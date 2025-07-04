Write-Host "=== INICIANDO ANALYST IA OTIMIZADO ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Verificando cache e dados..." -ForegroundColor Yellow
Set-Location -Path "backend"
python check_and_fix_cache.py

Write-Host ""
Write-Host "2. Iniciando backend..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd backend && python main.py"

Write-Host ""
Write-Host "3. Iniciando frontend..." -ForegroundColor Yellow
Set-Location -Path "../frontend"
npm run dev
