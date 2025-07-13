# Script para diagnosticar o servidor MPC
Write-Host "Diagnosticando servidor MPC..."

$logFile = "logs\diagnostico_mpc.log"

# Verificar se o Python está disponível
try {
    $pythonVersion = python --version
    Write-Host "Python disponível: $pythonVersion"
    Add-Content -Path $logFile -Value "Python disponível: $pythonVersion"
} catch {
    Write-Host "Erro: Python não encontrado: $_"
    Add-Content -Path $logFile -Value "Erro: Python não encontrado: $_"
    exit 1
}

# Verificar se os módulos necessários estão instalados
try {
    Write-Host "Verificando módulos necessários..."
    Add-Content -Path $logFile -Value "Verificando módulos necessários..."
    
    $modules = @("fastapi", "uvicorn")
    foreach ($module in $modules) {
        $checkModule = python -c "import $module; print('$module disponível')"
        Write-Host $checkModule
        Add-Content -Path $logFile -Value $checkModule
    }
} catch {
    Write-Host "Erro ao verificar módulos: $_"
    Add-Content -Path $logFile -Value "Erro ao verificar módulos: $_"
}

# Tentar iniciar o servidor com redirecionamento de saída para arquivo
try {
    Write-Host "Tentando iniciar servidor MPC..."
    Add-Content -Path $logFile -Value "Tentando iniciar servidor MPC..."
    
    python mpc_server.py --port 8765 > logs\mpc_output.log 2>&1
} catch {
    Write-Host "Erro ao iniciar servidor: $_"
    Add-Content -Path $logFile -Value "Erro ao iniciar servidor: $_"
}
