# Script para iniciar o servidor MPC e gerenciar portas
param(
    [int]$port = 9876
)

# Verificar se a porta está em uso
$portInUse = $null
try {
    $portInUse = netstat -ano | findstr ":$port" | Out-String
} catch {
    Write-Host "Erro ao verificar porta: $_"
}

if ($portInUse) {
    Write-Host "A porta $port está em uso. Tentando liberar..."
    
    try {
        # Extrair PID
        $portInUse = $portInUse -replace '\s+', ' '
        $parts = ($portInUse -split '\n' | Where-Object { $_ -match ":$port" } | Select-Object -First 1) -split ' '
        $pid = $parts[$parts.Length - 1]
        
        if ($pid -match '^\d+$') {
            # Verificar qual processo é
            $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "Processo usando a porta $port: $($process.Name) (PID: $pid)"
                Write-Host "Finalizando processo..."
                Stop-Process -Id $pid -Force
                Start-Sleep -Seconds 1
            }
        }
    } catch {
        Write-Host "Erro ao tentar finalizar processo: $_"
    }
}

# Verificar se a porta foi liberada
$portCheck = netstat -ano | findstr ":$port" | Out-String
if ($portCheck) {
    Write-Host "AVISO: A porta $port ainda está em uso. Tentando usar a porta alternativa 10876..."
    $port = 10876
}

Write-Host "Iniciando servidor MPC na porta $port..."
# Criar arquivo de log
$logFile = "logs\mpc_server_start_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Executar o servidor MPC
try {
    Start-Process -FilePath "python" -ArgumentList "mpc_server.py --port $port" -RedirectStandardOutput $logFile -RedirectStandardError "$logFile.err" -NoNewWindow
    Write-Host "Servidor MPC iniciado na porta $port. Logs em: $logFile"
    
    # Registra a porta usada em um arquivo para referência
    "porta=$port" | Out-File -FilePath "config\mpc_port.txt" -Force
} catch {
    Write-Host "Erro ao iniciar servidor MPC: $_"
}

Write-Host "Concluído!"
