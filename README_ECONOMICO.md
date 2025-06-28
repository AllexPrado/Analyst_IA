# Analyst-IA - Versão Econômica

## Instruções de Uso Rápido

Para economizar no consumo de tokens e garantir o funcionamento do sistema:

1. **Inicie o sistema com um clique duplo em:**

   ```bat
   INICIAR.bat
   ```

2. **Aguarde o backend iniciar** (uma nova janela de console se abrirá)

3. **Para iniciar o frontend**, abra outro terminal e execute:

   ```bash
   cd frontend
   npm run dev
   ```

4. **Acesse o sistema em:** [http://localhost:5173](http://localhost:5173)

## Economia de Tokens

Esta versão foi otimizada para reduzir o consumo de tokens:

- Usa GPT-3.5 para perguntas simples (mais econômico)
- Só usa GPT-4 para análises complexas
- Implementa limite diário de tokens
- Registra uso para evitar gastos excessivos

## Troubleshooting

Se encontrar problemas:

1. Verifique se o Node.js está instalado corretamente
2. Execute `python corrigir_e_iniciar.py` diretamente da pasta do projeto
3. Certifique-se que o arquivo `.env` contém sua chave da API OpenAI

## Nota Importante

Esta versão foi configurada para minimizar os custos de uso da API OpenAI, mantendo a funcionalidade essencial do sistema.
