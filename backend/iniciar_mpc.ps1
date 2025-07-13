# Script para iniciar o servidor MPC
Write-Host "Iniciando servidor MPC na porta 8765..."

# Remover arquivo de configuração se existir
$configPath = Join-Path (Get-Location) "config\mpc_agents.json"
if (Test-Path $configPath) {
    Remove-Item $configPath -Force
    Write-Host "Arquivo de configuração removido: $configPath"
}

# Iniciar servidor MPC
try {
    python mpc_server.py --port 8765
} catch {
    Write-Host "Erro ao iniciar servidor MPC: $_"
    exit 1
}
