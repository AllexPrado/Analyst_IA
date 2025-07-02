# Script PowerShell para iniciar o Analyst IA com dados reais
Write-Host "========================================" -ForegroundColor Green
Write-Host "Iniciando Sistema Analyst IA com Dados Reais" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Muda para o diretório do script
Set-Location $PSScriptRoot

Write-Host "🔍 Verificando configuração de dados reais..." -ForegroundColor Yellow
python verificar_config_dados_reais.py

Write-Host "🔄 Verificando e corrigindo cache..." -ForegroundColor Yellow
python backend\check_and_fix_cache.py

Write-Host "🚀 Iniciando backend..." -ForegroundColor Yellow
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; python main.py" -WindowStyle Normal

Write-Host "⏳ Aguardando 5 segundos..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "🌐 Iniciando frontend..." -ForegroundColor Yellow
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm run dev" -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Sistema iniciado com dados reais!" -ForegroundColor Green
Write-Host ""
Write-Host "📡 Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "🌐 Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "📊 Infraestrutura Avançada: http://localhost:5173/infraestrutura-avancada" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANTE: Para verificar se o frontend está usando dados reais," -ForegroundColor Yellow
Write-Host "acesse a página de Infraestrutura Avançada e verifique se os dados" -ForegroundColor Yellow
Write-Host "correspondem aos dados configurados no New Relic." -ForegroundColor Yellow
