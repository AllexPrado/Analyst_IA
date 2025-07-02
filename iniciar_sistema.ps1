# Script PowerShell para iniciar o Analyst IA
Write-Host "========================================" -ForegroundColor Green
Write-Host "Iniciando Sistema Analyst IA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Muda para o diretório do script
Set-Location $PSScriptRoot

Write-Host "🔧 Ativando ambiente virtual..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"

Write-Host "📦 Verificando dependências..." -ForegroundColor Yellow
& ".\.venv\Scripts\pip.exe" install fastapi uvicorn python-dotenv openai requests aiohttp pydantic

Write-Host "🚀 Iniciando backend..." -ForegroundColor Yellow
Start-Process -FilePath "cmd" -ArgumentList "/k", "cd /d `"$PWD\backend`" && `"$PWD\.venv\Scripts\uvicorn.exe`" main:app --reload --host 0.0.0.0 --port 8000" -WindowStyle Normal

Write-Host "⏳ Aguardando 5 segundos..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "🌐 Iniciando frontend..." -ForegroundColor Yellow
Start-Process -FilePath "cmd" -ArgumentList "/k", "cd /d `"$PWD\frontend`" && npm run dev" -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Sistema iniciado com sucesso!" -ForegroundColor Green
Write-Host ""
Write-Host "📡 Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "🌐 Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "💬 Chat IA: http://localhost:5173/chat" -ForegroundColor Cyan
Write-Host "📊 Dashboard: http://localhost:5173/dashboard" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green

Read-Host "Pressione Enter para sair"
