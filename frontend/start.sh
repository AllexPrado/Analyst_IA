#!/bin/bash

# Script para inicializar o frontend do Analyst_IA
# Este script facilita o desenvolvimento e teste da aplicação

echo "🚀 Iniciando Analyst_IA Frontend..."

# Verificar se Node.js está instalado
if ! command -v node &> /dev/null; then
    echo "❌ Node.js não encontrado. Por favor, instale Node.js primeiro."
    exit 1
fi

# Verificar se npm está instalado  
if ! command -v npm &> /dev/null; then
    echo "❌ npm não encontrado. Por favor, instale npm primeiro."
    exit 1
fi

# Verificar se estamos no diretório correto
if [ ! -f "package.json" ]; then
    echo "❌ package.json não encontrado. Execute este script no diretório frontend."
    exit 1
fi

echo "📦 Instalando dependências..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Erro ao instalar dependências."
    exit 1
fi

echo "🔍 Verificando se o backend está rodando..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend está online na porta 8000"
else
    echo "⚠️  Backend não está respondendo na porta 8000"
    echo "   Por favor, certifique-se de que o backend está rodando:"
    echo "   cd ../backend && python main.py"
fi

echo "🎯 Iniciando servidor de desenvolvimento..."
echo "   Frontend será executado em: http://localhost:5173"
echo "   Pressione Ctrl+C para parar"

npm run dev
