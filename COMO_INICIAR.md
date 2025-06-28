# Como iniciar o Analyst-IA (Sistema Unificado)

Este guia explica como iniciar corretamente o sistema Analyst-IA após as correções de unificação.

## Pré-requisitos

- Python 3.8 ou superior
- Node.js e npm (para o frontend)
- Chave de API do New Relic configurada
- Chave de API da OpenAI configurada

## Opção 1: Inicialização Automática (Recomendado)

Para iniciar todo o sistema (backend e frontend) com um único comando, execute:

```bat
iniciar_sistema.bat
```

Este script vai:

1. Iniciar o backend unificado em uma janela
2. Verificar se está funcionando
3. Iniciar o frontend em outra janela
4. Exibir as URLs para acesso

## Opção 2: Inicialização Manual

### Passo 1: Instalar dependências

```bash
python instalar_dependencias.py
```

### Passo 2: Iniciar o backend unificado

```bash
python start_unified_backend.py
```

### Passo 3: Iniciar o frontend (em outro terminal)

```bash
cd frontend
npm install  # apenas na primeira vez ou após alterações no package.json
npm run dev
```

## Verificação

Para verificar se o sistema está funcionando corretamente:

```bash
python validar_frontend_backend.py
```

## Acessando o sistema

- Frontend: [http://localhost:5173](http://localhost:5173)
- Backend API: [http://localhost:8000](http://localhost:8000)

## Solução de problemas

Se encontrar problemas:

1. Verifique se as APIs estão configuradas corretamente (.env)
2. Verifique os logs do backend (`logs/analyst_ia.log`)
3. Certifique-se de que não há outros serviços rodando nas mesmas portas (8000, 5173)

Para reiniciar o sistema completamente, encerre todos os processos e execute `iniciar_sistema.bat` novamente.
