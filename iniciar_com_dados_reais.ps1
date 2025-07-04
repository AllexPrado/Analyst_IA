# Script PowerShell para iniciar o sistema Analyst_IA com dados reais
# Este script executa todos os passos necessários para garantir o uso de dados reais

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "         INICIALIZAÇÃO OTIMIZADA DO ANALYST_IA (DADOS REAIS)" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan

# Função para executar uma etapa com tratamento de erros
function Executar-Etapa {
    param (
        [string]$Descricao,
        [scriptblock]$Comando
    )
    
    Write-Host "`n[$Descricao]" -ForegroundColor Yellow
    try {
        & $Comando
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠️ Aviso: A etapa '$Descricao' completou com código $LASTEXITCODE" -ForegroundColor Yellow
        } else {
            Write-Host "✅ $Descricao concluído com sucesso" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ Erro na etapa '$Descricao': $_" -ForegroundColor Red
    }
}

# Etapa 1: Limpeza do projeto e verificação de integridade
Executar-Etapa -Descricao "Limpeza do projeto" -Comando {
    python limpar_projeto.py
}

# Etapa 2: Verificação e correção do cache
Executar-Etapa -Descricao "Verificação e correção do cache" -Comando {
    python backend\check_and_fix_cache.py
}

# Etapa 3: Forçar uso de dados reais
Executar-Etapa -Descricao "Configuração para dados reais" -Comando {
    python forcar_dados_reais_frontend.py
}

# Etapa 4: Verificação de dados reais
Executar-Etapa -Descricao "Verificação de dados reais" -Comando {
    python verificar_dados_reais.py
}

# Etapa 5: Iniciar o sistema completo
Write-Host "`n[Iniciando o sistema completo]" -ForegroundColor Yellow

Write-Host "`nIniciando backend em segundo plano..." -ForegroundColor Cyan
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd $PWD\backend && python main.py" -WindowStyle Normal

# Aguardar um momento para o backend inicializar
Write-Host "Aguardando backend inicializar (10 segundos)..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# Verificar se o backend está respondendo
$backendOk = $false
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 5
    if ($response.status -eq "ok") {
        $backendOk = $true
        Write-Host "✅ Backend iniciado com sucesso!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Backend respondendo, mas com status inesperado." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Backend não está respondendo. Continuando mesmo assim..." -ForegroundColor Yellow
}

# Iniciar o frontend
Write-Host "`nIniciando frontend..." -ForegroundColor Cyan
try {
    Set-Location -Path "frontend"
    npm run dev
} catch {
    Write-Host "❌ Erro ao iniciar o frontend: $_" -ForegroundColor Red
    Exit 1
}

Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host "         Sistema Analyst_IA em execução com dados reais!" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan
