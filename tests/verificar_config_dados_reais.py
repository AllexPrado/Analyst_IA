#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para verificar a configuração de dados reais do New Relic e orientar o usuário.

Este script:
1. Verifica se as credenciais do New Relic estão configuradas
2. Testa a conexão com a API do New Relic
3. Mostra o status atual da configuração (dados reais ou simulados)
4. Orienta o usuário sobre como configurar dados reais
"""

import os
import sys
import json
import logging
import requests
import traceback
from pathlib import Path
from datetime import datetime
import colorama
from colorama import Fore, Style

# Inicializar colorama para cores no terminal
colorama.init()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/configuracao_new_relic.log", mode='a')
    ]
)

logger = logging.getLogger(__name__)
os.makedirs("logs", exist_ok=True)

class ConfiguracaoNewRelic:
    def __init__(self):
        """Inicializa o verificador de configuração"""
        # Obter credenciais do ambiente
        self.account_id = os.environ.get("NEW_RELIC_ACCOUNT_ID")
        self.api_key = os.environ.get("NEW_RELIC_API_KEY")
        
        # Verificar arquivo .env na raiz do projeto
        self._carregar_env()
        
        # Status da configuração
        self.status = {
            "credenciais_configuradas": bool(self.account_id and self.api_key),
            "conexao_api_ok": False,
            "modo_atual": "simulado"
        }
    
    def _carregar_env(self):
        """Carrega as variáveis de ambiente do arquivo .env se existir"""
        env_path = Path(".env")
        if env_path.exists():
            logger.info("Arquivo .env encontrado. Carregando variáveis...")
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        try:
                            key, value = line.split("=", 1)
                            if not os.environ.get(key) and value:  # Não sobrescreve se já definido
                                os.environ[key] = value
                                if key in ["NEW_RELIC_ACCOUNT_ID", "NEW_RELIC_API_KEY"]:
                                    setattr(self, key.lower(), value)
                        except Exception as e:
                            logger.warning(f"Erro ao processar linha no .env: {line}, erro: {e}")
        else:
            logger.warning("Arquivo .env não encontrado.")
    
    def testar_conexao_api(self):
        """Testa a conexão com a API do New Relic"""
        if not self.account_id or not self.api_key:
            logger.warning("Credenciais não configuradas. Não é possível testar conexão.")
            return False
        
        try:
            # Teste simples da API do New Relic - obter lista de aplicações
            url = f"https://api.newrelic.com/v2/applications.json"
            headers = {
                "X-Api-Key": self.api_key,
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.status["conexao_api_ok"] = True
                logger.info("Conexão com a API do New Relic bem-sucedida!")
                return True
            else:
                logger.error(f"Falha na conexão com a API do New Relic. Status: {response.status_code}")
                logger.error(f"Resposta: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao testar conexão com a API do New Relic: {e}")
            traceback.print_exc()
            return False
    
    def verificar_modo_atual(self):
        """Verifica se o sistema está usando dados reais ou simulados"""
        # Verificar relatório de integração se existir
        relatorio_path = Path("relatorio_integracao_dados_reais.json")
        if relatorio_path.exists():
            try:
                with open(relatorio_path, "r", encoding="utf-8") as f:
                    relatorio = json.load(f)
                    self.status["modo_atual"] = relatorio.get("modo", "simulado")
                    logger.info(f"Modo atual conforme relatório de integração: {self.status['modo_atual']}")
            except Exception as e:
                logger.error(f"Erro ao ler relatório de integração: {e}")
        
        # Se tem credenciais e conexão OK, provavelmente pode usar dados reais
        if self.status["credenciais_configuradas"] and self.status["conexao_api_ok"]:
            self.status["modo_possivel"] = "real"
        else:
            self.status["modo_possivel"] = "simulado"
    
    def criar_env_exemplo(self):
        """Cria um arquivo .env de exemplo se não existir"""
        env_path = Path(".env")
        if not env_path.exists():
            try:
                sample_path = Path(".env.sample")
                if sample_path.exists():
                    with open(sample_path, "r", encoding="utf-8") as f:
                        sample_content = f.read()
                    
                    with open(env_path, "w", encoding="utf-8") as f:
                        f.write(sample_content)
                    
                    logger.info("Arquivo .env criado com base no modelo .env.sample")
                    print(f"{Fore.GREEN}✅ Arquivo .env criado com sucesso!{Style.RESET_ALL}")
                    return True
                else:
                    logger.warning("Arquivo .env.sample não encontrado para criar modelo")
                    return False
            except Exception as e:
                logger.error(f"Erro ao criar arquivo .env: {e}")
                return False
        return True
    
    def mostrar_status(self):
        """Mostra o status da configuração no terminal"""
        print("\n" + "="*60)
        print(f"{Fore.CYAN}CONFIGURAÇÃO DE DADOS REAIS DO NEW RELIC{Style.RESET_ALL}")
        print("="*60)
        
        # Status das credenciais
        if self.status["credenciais_configuradas"]:
            print(f"{Fore.GREEN}✅ Credenciais configuradas{Style.RESET_ALL}")
            print(f"   Account ID: {self.account_id[:5]}...{'*' * 5}")
            print(f"   API Key: {'*' * 5}...{'*' * 5}")
        else:
            print(f"{Fore.RED}❌ Credenciais não configuradas{Style.RESET_ALL}")
        
        # Status da conexão
        if self.status["conexao_api_ok"]:
            print(f"{Fore.GREEN}✅ Conexão com a API do New Relic funcionando{Style.RESET_ALL}")
        else:
            if self.status["credenciais_configuradas"]:
                print(f"{Fore.RED}❌ Falha na conexão com a API do New Relic{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠️  Conexão não testada (credenciais ausentes){Style.RESET_ALL}")
        
        # Modo atual
        modo_atual = self.status.get("modo_atual", "simulado")
        if modo_atual == "real":
            print(f"{Fore.GREEN}✅ Sistema usando DADOS REAIS{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠️  Sistema usando DADOS SIMULADOS{Style.RESET_ALL}")
        
        # Modo possível
        modo_possivel = self.status.get("modo_possivel", "simulado")
        if modo_possivel == "real":
            if modo_atual == "simulado":
                print(f"{Fore.GREEN}ℹ️  Sistema pode usar dados reais, mas está configurado para simulados{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}ℹ️  Sistema só pode usar dados simulados no momento{Style.RESET_ALL}")
        
        print("\n" + "="*60)
        print(f"{Fore.CYAN}PRÓXIMOS PASSOS{Style.RESET_ALL}")
        print("="*60)
        
        if not self.status["credenciais_configuradas"]:
            print(f"1. Configure suas credenciais do New Relic no arquivo {Fore.CYAN}.env{Style.RESET_ALL}")
            print(f"   ⚠️ Use o arquivo {Fore.CYAN}.env.sample{Style.RESET_ALL} como modelo")
            print(f"   ⚠️ Obtenha suas credenciais em https://one.newrelic.com/ > User settings > API keys")
        
        if self.status["credenciais_configuradas"] and not self.status["conexao_api_ok"]:
            print(f"1. Verifique suas credenciais do New Relic no arquivo {Fore.CYAN}.env{Style.RESET_ALL}")
            print(f"   ⚠️ A conexão com a API do New Relic falhou")
        
        if self.status["modo_possivel"] == "real" and self.status["modo_atual"] == "simulado":
            print(f"1. Execute o comando para integrar dados reais:")
            print(f"   {Fore.CYAN}python integrar_dados_reais_newrelic.py{Style.RESET_ALL}")
            
        if self.status["modo_atual"] == "real":
            print(f"✅ Parabéns! Seu sistema já está configurado para usar dados reais do New Relic.")
            print(f"   Para manter os dados atualizados, considere executar regularmente:")
            print(f"   {Fore.CYAN}python sincronizar_periodico_newrelic.py{Style.RESET_ALL}")
        
        print("\n" + "="*60)

def main():
    """Função principal para execução do script"""
    print(f"{Fore.CYAN}Verificando configuração de dados reais do New Relic...{Style.RESET_ALL}")
    
    # Criar diretório de logs se não existir
    os.makedirs("logs", exist_ok=True)
    
    # Instanciar o verificador
    verificador = ConfiguracaoNewRelic()
    
    # Criar arquivo .env de exemplo se necessário
    verificador.criar_env_exemplo()
    
    # Testar conexão com a API
    if verificador.status["credenciais_configuradas"]:
        verificador.testar_conexao_api()
    
    # Verificar o modo atual
    verificador.verificar_modo_atual()
    
    # Mostrar status
    verificador.mostrar_status()
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Operação cancelada pelo usuário.{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Erro inesperado: {e}{Style.RESET_ALL}")
        traceback.print_exc()
        sys.exit(1)
