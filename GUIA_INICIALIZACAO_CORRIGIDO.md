# Guia de Inicialização do Sistema - Versão Corrigida

Este guia explica como iniciar corretamente o sistema após as correções de problemas com diretórios e arquivos.

## Problema Anterior

O sistema estava enfrentando problemas com:

- Arquivos de dados gerados em `backend/dados/` mas o backend procurava em `dados/`
- Diretório de endpoints não sendo encontrado
- Caminhos relativos incorretos entre os scripts

## Solução Implementada

As correções permitem que o sistema:

1. Procure arquivos de dados em múltiplos diretórios possíveis
2. Sincronize dados entre o diretório raiz e o diretório backend
3. Identifique corretamente os endpoints independentemente do diretório atual

## Como Iniciar o Sistema

### Opção 1: Iniciar com o Script Corrigido

``

python iniciar_sistema_corrigido.py

``

Este script:

- Verifica e corrige a estrutura de diretórios
- Copia arquivos de dados entre diretórios se necessário
- Cria o arquivo de endpoint de insights se não existir
- Inicia o backend e o frontend

### Opção 2: Verificar a Estrutura Primeiro

Se preferir verificar se tudo está configurado corretamente antes de iniciar:

``
python verificar_paths.py
``

Este script verificará se todos os arquivos e diretórios necessários existem e mostrará um relatório detalhado.

### Opção 3: Usar o Script Original

Se preferir continuar usando o script original:

``
python iniciar_sistema.py
``

Obs: As correções aplicadas também melhoram o comportamento do script original.

## Estrutura de Diretórios

Para o funcionamento correto do sistema, é necessário que exista:

``
Analyst_IA/
  ├── dados/                    # Arquivos JSON de dados (no nível raiz)
  ├── backend/
  │   ├── dados/                # Cópia dos arquivos JSON (no backend)
  │   ├── endpoints/            # Módulos de endpoints da API
  │   │   ├── __init__.py
  │   │   └── insights_endpoints.py
  │   ├── main.py               # Script principal do backend
  │   └── core_router.py        # Router principal da API
  └── frontend/                 # Código do frontend
``

## Solução de Problemas

Se encontrar problemas:

1. **Erro "Diretório de endpoints não encontrado"**:
   - Execute `verificar_paths.py` para diagnóstico
   - Verifique se existe o diretório `backend/endpoints`

2. **Erro "Arquivo não encontrado" ao acessar dados**:
   - Verifique se os arquivos JSON existem tanto em `dados/` quanto em `backend/dados/`
   - Execute `iniciar_sistema_corrigido.py` para sincronizar os diretórios

3. **Tela branca no frontend**:
   - Verifique se o backend está retornando os dados corretamente: `http://localhost:8000/api/insights`
   - Verifique no console do navegador se há erros de JavaScript

## Comandos Úteis

- **Gerar dados de demonstração**: `python backend/gerar_dados_demo.py`
- **Iniciar apenas o backend**: `python backend/main.py`
- **Iniciar apenas o frontend**: (Na pasta frontend) `npm run dev`

## Notas Adicionais

- Os endpoints agora procuram os arquivos de dados em múltiplos locais (tanto `/dados` quanto `/backend/dados`)
- O sistema foi modificado para ser mais resiliente a diferentes diretórios de trabalho
- Os arquivos de dados são sincronizados entre os diretórios durante a inicialização
