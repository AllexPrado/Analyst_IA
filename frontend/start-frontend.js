#!/usr/bin/env node

/**
 * Script para inicializar o frontend do Analyst IA
 * Este script verifica dependências, instala se necessário e inicia o servidor de desenvolvimento
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const readline = require('readline');

// Configuração do console para cores
const colors = {
  reset: "\x1b[0m",
  bright: "\x1b[1m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  red: "\x1b[31m"
};

// Imprime cabeçalho
console.log(`
${colors.bright}${colors.blue}======================================================
            ANALYST IA - FRONTEND STARTER
======================================================${colors.reset}
`);

// Verifica se estamos no diretório correto
try {
  const packagePath = path.join(process.cwd(), 'package.json');
  if (!fs.existsSync(packagePath)) {
    console.error(`${colors.red}Erro: Arquivo package.json não encontrado!
Execute este script na pasta raiz do frontend.${colors.reset}`);
    process.exit(1);
  }

  const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
  if (!packageJson.name || !packageJson.name.toLowerCase().includes('analyst')) {
    console.log(`${colors.yellow}Aviso: Este não parece ser o projeto Analyst IA. Continuando mesmo assim...${colors.reset}`);
  }
} catch (error) {
  console.error(`${colors.red}Erro ao verificar o projeto: ${error.message}${colors.reset}`);
  process.exit(1);
}

console.log(`${colors.bright}1. Verificando dependências...${colors.reset}`);

// Verifica se node_modules existe
const hasNodeModules = fs.existsSync(path.join(process.cwd(), 'node_modules'));

if (!hasNodeModules) {
  console.log(`${colors.yellow}node_modules não encontrado. Instalando dependências...${colors.reset}`);
  try {
    execSync('npm install', { stdio: 'inherit' });
    console.log(`${colors.green}Dependências instaladas com sucesso!${colors.reset}`);
  } catch (error) {
    console.error(`${colors.red}Erro ao instalar dependências: ${error.message}${colors.reset}`);
    process.exit(1);
  }
} else {
  console.log(`${colors.green}node_modules já existe. Pulando instalação.${colors.reset}`);
}

console.log(`${colors.bright}2. Verificando o backend...${colors.reset}`);
console.log(`${colors.yellow}Nota: O frontend pode funcionar sem o backend, mas usará dados de demonstração.${colors.reset}`);

// Inicia o servidor de desenvolvimento
console.log(`${colors.bright}3. Iniciando servidor de desenvolvimento...${colors.reset}`);
try {
  console.log(`${colors.green}Servidor iniciado! Acesse: http://localhost:5173${colors.reset}`);
  execSync('npm run dev', { stdio: 'inherit' });
} catch (error) {
  console.error(`${colors.red}Erro ao iniciar o servidor: ${error.message}${colors.reset}`);
  process.exit(1);
}
