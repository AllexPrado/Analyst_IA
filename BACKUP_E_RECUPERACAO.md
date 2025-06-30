# Procedimento de Backup e Recuperação Diária do Analyst IA

Este documento descreve os procedimentos para backup diário e recuperação do sistema Analyst IA, incluindo dados do coletor avançado do New Relic e sistema de economia de tokens.

## Visão Geral

O sistema Analyst IA possui os seguintes componentes críticos que necessitam backup:

1. **Cache de dados do New Relic**: Contém dados coletados através do coletor avançado
2. **Histórico de economia de tokens**: Relatórios e métricas de economia do sistema
3. **Configurações de integração**: Arquivos de configuração do New Relic e OpenAI
4. **Registros de interação com usuários**: Histórico de chats e análises geradas

## Procedimento de Backup Diário

### 1. Backup Automatizado

Um script automatizado realiza o backup dos seguintes diretórios:

```powershell
# Script de backup diário - executar às 23:00 diariamente
$date = Get-Date -Format "yyyy-MM-dd"
$backupDir = "D:\backups\analyst_ia\$date"

# Criar diretório de backup
New-Item -ItemType Directory -Force -Path $backupDir

# Backup de dados críticos
Copy-Item "D:\projetos\Analyst_IA\backend\historico\*" -Destination "$backupDir\cache" -Recurse
Copy-Item "D:\projetos\Analyst_IA\backend\logs\*" -Destination "$backupDir\logs" -Recurse
Copy-Item "D:\projetos\Analyst_IA\relatorios\*" -Destination "$backupDir\relatorios" -Recurse
Copy-Item "D:\projetos\Analyst_IA\backend\.env" -Destination "$backupDir\"

# Backup do código-fonte com configurações atuais
Copy-Item "D:\projetos\Analyst_IA\backend\utils\newrelic_advanced_collector.py" -Destination "$backupDir\"
Copy-Item "D:\projetos\Analyst_IA\backend\utils\entity_processor.py" -Destination "$backupDir\"
Copy-Item "D:\projetos\Analyst_IA\backend\main.py" -Destination "$backupDir\"

# Compressão do backup
Compress-Archive -Path "$backupDir\*" -DestinationPath "$backupDir.zip"
Remove-Item -Path $backupDir -Recurse

# Manter apenas os últimos 7 backups
Get-ChildItem -Path "D:\backups\analyst_ia\*.zip" | Sort-Object CreationTime -Descending | Select-Object -Skip 7 | Remove-Item
```

### 2. Backup Manual (Quando necessário)

Para realizar um backup manual completo do sistema:

1. Acesse o servidor via terminal
2. Execute o script de backup:

```bash
python D:\projetos\Analyst_IA\backend\utils\backup_system.py --full
```

Este script fará:

- Backup completo de todo o cache
- Backup de todos os relatórios gerados
- Backup das configurações e credenciais
- Backup do código-fonte atual

## Procedimento de Recuperação

### 1. Recuperação Total

Em caso de falha completa do sistema:

1. Reinstale o sistema a partir do repositório Git
2. Restaure os dados de backup:

```powershell
# Escolher backup mais recente ou específico
$backupFile = "D:\backups\analyst_ia\2025-06-28.zip"

# Extrair backup
Expand-Archive -Path $backupFile -DestinationPath "D:\temp\restore"

# Restaurar dados
Copy-Item "D:\temp\restore\cache\*" -Destination "D:\projetos\Analyst_IA\backend\historico\" -Recurse -Force
Copy-Item "D:\temp\restore\logs\*" -Destination "D:\projetos\Analyst_IA\backend\logs\" -Recurse -Force 
Copy-Item "D:\temp\restore\relatorios\*" -Destination "D:\projetos\Analyst_IA\relatorios\" -Recurse -Force
Copy-Item "D:\temp\restore\.env" -Destination "D:\projetos\Analyst_IA\backend\.env" -Force

# Limpar diretório temporário
Remove-Item -Path "D:\temp\restore" -Recurse
```

### 2. Recuperação Parcial do Cache

Para recuperar apenas os dados do cache:

```bash
python D:\projetos\Analyst_IA\backend\utils\restore_cache.py --date 2025-06-28
```

## Verificação de Integridade Após Restauração

Após a restauração, execute o script de verificação de integridade:

```bash
python D:\projetos\Analyst_IA\backend\test_system_integrity.py
```

Este script verificará:

- Integridade do cache restaurado
- Conexões com New Relic e OpenAI
- Funcionamento do coletor avançado
- Processamento de entidades
- Economia de tokens

## Cronograma de Backup

| Tipo de Backup | Frequência | Retenção |
|----------------|------------|----------|
| Completo | Diário (23h) | 7 dias |
| Cache | A cada 6 horas | 3 dias |
| Logs | Diário | 30 dias |
| Relatórios | Semanal | 90 dias |

## Contatos para Emergências

Em caso de falhas no processo de backup ou recuperação:

- Suporte Técnico: [suporte@exemplo.com](mailto:suporte@exemplo.com)

- Administrador do Sistema: [admin@exemplo.com](mailto:admin@exemplo.com)
- Telefone de Emergência: (XX) XXXXX-XXXX
