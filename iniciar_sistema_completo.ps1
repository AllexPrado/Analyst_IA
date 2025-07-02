# Script PowerShell para iniciar o sistema completo Analyst IA
Write-Host "========================================" -ForegroundColor Green
Write-Host "Iniciando Sistema Analyst IA Completo" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Muda para o diretório do script
Set-Location $PSScriptRoot

Write-Host "🔄 Verificando e corrigindo cache..." -ForegroundColor Yellow
cd backend
python check_and_fix_cache.py
cd ..

Write-Host "🚀 Iniciando backend..." -ForegroundColor Yellow
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; python main.py" -WindowStyle Normal

Write-Host "⏳ Aguardando 3 segundos para o backend inicializar..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "🌐 Iniciando frontend..." -ForegroundColor Yellow
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev" -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Sistema iniciado com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "📡 Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "🌐 Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "📊 Dashboard: http://localhost:5173/dashboard" -ForegroundColor Cyan
Write-Host "📈 Infraestrutura: http://localhost:5173/infraestrutura-avancada" -ForegroundColor Cyan
