# Script para matar o processo que está usando a porta 9876
$port = 9876

Write-Host "Verificando processos que estão usando a porta $port..."

# Encontrar o PID do processo usando a porta
$processInfo = netstat -ano | findstr ":$port"
if ($processInfo) {
    $processInfo = $processInfo -replace '\s+', ' '
    $parts = $processInfo.Split(' ')
    
    # O PID geralmente é o último item
    $pid = $parts[$parts.Length - 1]
    
    Write-Host "Processo com PID $pid encontrado usando a porta $port"
    
    # Verificar detalhes do processo
    $processDetails = Get-Process -Id $pid
    Write-Host "Nome do processo: $($processDetails.Name)"
    
    # Matar o processo
    Write-Host "Tentando matar o processo..."
    Stop-Process -Id $pid -Force
    Write-Host "Processo finalizado com sucesso!"
    
    # Verificar novamente se a porta foi liberada
    $checkAgain = netstat -ano | findstr ":$port"
    if ($checkAgain) {
        Write-Host "AVISO: A porta $port ainda parece estar em uso!"
    } else {
        Write-Host "✓ Porta $port liberada com sucesso!"
    }
} else {
    Write-Host "Nenhum processo encontrado usando a porta $port"
}
