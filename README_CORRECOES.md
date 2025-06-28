# Analyst-IA - Sistema Unificado

## Correções Implementadas

Este projeto passou por uma série de correções para garantir seu funcionamento adequado. As principais melhorias incluem:

1. **Correção do Backend**
   - Remoção da importação problemática `truncate_text_tokens`
   - Implementação do endpoint `/api/health` para monitoramento
   - Correção dos parâmetros na chamada da função `gerar_resposta_ia`

2. **Correções do Frontend**
   - Verificação de dependências e instalação do Node.js
   - Tratamento adequado de dados nulos nos gráficos
   - Compatibilidade com o backend unificado

3. **Scripts de Manutenção**
   - `reiniciar_sistema.py`: Reinicia completamente o sistema
   - `corrigir_backend.py`: Corrige problemas específicos no backend
   - `verificar_node.py`: Verifica a instalação do Node.js e npm
   - `iniciar_sistema_completo.py`: Aplica todas as correções e inicia o sistema

## Como Iniciar o Sistema

### Método Simples (Recomendado)

1. Execute o arquivo batch:

   ```bat
   INICIAR_SISTEMA_COMPLETO.bat
   ```

2. Siga as instruções na tela para completar a instalação.

### Método Manual

1. **Preparação do Ambiente**:
   - Instale Python 3.8+
   - Instale Node.js e npm

2. **Instale as Dependências**:

   ```bash
   python instalar_dependencias.py
   ```

3. **Corrija Problemas Específicos**:

   ```bash
   python corrigir_backend.py
   ```

4. **Reinicie o Sistema**:

   ```bash
   python reiniciar_sistema.py
   ```

5. **Acesse o Sistema**:
   - Frontend: [http://localhost:5173](http://localhost:5173)
   - Backend: [http://localhost:8000](http://localhost:8000)

## Resolução de Problemas

### Problema: Erro de importação no backend

```text
ImportError: cannot import name 'truncate_text_tokens' from 'utils.openai_connector'
```

**Solução**: Execute `python corrigir_backend.py` para corrigir automaticamente o problema ou edite manualmente o arquivo `backend/unified_backend.py` para remover a importação de `truncate_text_tokens`.

### Problema: Node.js/npm não encontrado

```text
'npm' não é reconhecido como um comando interno ou externo
```

**Solução**: Execute `python verificar_node.py` para instruções sobre como instalar o Node.js, ou baixe-o diretamente de [nodejs.org](https://nodejs.org/).

### Problema: Endpoint de chat falha

**Solução**: Verifique se o parâmetro 'temperatura' não está sendo passado para a função `gerar_resposta_ia()` no backend.

### Problema: Aplicação frontend não inicia

**Solução**: Execute:

```bash
cd frontend
npm install
npm run dev
```

para instalar dependências e iniciar o servidor de desenvolvimento.

## Contato

Se você tiver problemas adicionais, consulte a documentação ou entre em contato com o administrador do sistema.
