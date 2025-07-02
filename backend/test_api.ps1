Write-Host "Testando endpoints da API" -ForegroundColor Green

Write-Host "`nVerificando saúde do sistema..." -ForegroundColor Yellow
$health = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -UseBasicParsing
Write-Host "Status: $($health.StatusCode) - $($health.Content)" -ForegroundColor Cyan

Write-Host "`nVerificando KPIs..." -ForegroundColor Yellow
try {
    $kpis = Invoke-WebRequest -Uri "http://localhost:8000/api/kpis" -UseBasicParsing
    Write-Host "Status: $($kpis.StatusCode) - KPIs OK" -ForegroundColor Cyan
} catch {
    Write-Host "Erro ao carregar KPIs: $_" -ForegroundColor Red
}

Write-Host "`nVerificando tendências..." -ForegroundColor Yellow
try {
    $tendencias = Invoke-WebRequest -Uri "http://localhost:8000/api/tendencias" -UseBasicParsing
    Write-Host "Status: $($tendencias.StatusCode) - Tendências OK" -ForegroundColor Cyan
} catch {
    Write-Host "Erro ao carregar tendências: $_" -ForegroundColor Red
}

Write-Host "`nVerificando cobertura..." -ForegroundColor Yellow
try {
    $cobertura = Invoke-WebRequest -Uri "http://localhost:8000/api/cobertura" -UseBasicParsing
    Write-Host "Status: $($cobertura.StatusCode) - Cobertura OK" -ForegroundColor Cyan
} catch {
    Write-Host "Erro ao carregar cobertura: $_" -ForegroundColor Red
}

Write-Host "`nVerificando insights..." -ForegroundColor Yellow
try {
    $insights = Invoke-WebRequest -Uri "http://localhost:8000/api/insights" -UseBasicParsing
    Write-Host "Status: $($insights.StatusCode) - Insights OK" -ForegroundColor Cyan
} catch {
    Write-Host "Erro ao carregar insights: $_" -ForegroundColor Red
}

Write-Host "`nTestando o chat..." -ForegroundColor Yellow
try {
    $body = @{
        pergunta = "Como está o desempenho do sistema?"
    } | ConvertTo-Json

    $chat = Invoke-WebRequest -Uri "http://localhost:8000/api/chat" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
    Write-Host "Status: $($chat.StatusCode) - Chat OK" -ForegroundColor Cyan
    Write-Host "Resposta: $($chat.Content)" -ForegroundColor Gray
} catch {
    Write-Host "Erro ao testar chat: $_" -ForegroundColor Red
}

Write-Host "`nTestes concluídos!" -ForegroundColor Green
