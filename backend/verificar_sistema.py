#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import json
import logging
import os
import sys
from datetime import datetime
from tabulate import tabulate
from typing import Dict, List, Any, Optional

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URLs dos backends
BACKEND_PRINCIPAL = "http://localhost:8000"
API_INCIDENTES = "http://localhost:8002"

# URLs do frontend
FRONTEND_URL = "http://localhost:5173"

class VerificadorSistema:
    """Classe para verificar se todos os componentes do sistema estão funcionando corretamente"""
    
    def __init__(self):
        self.resultados = {
            "backend_principal": False,
            "api_incidentes": False,
            "frontend": False,
            "integracao": False,
            "entidades": 0,
            "incidentes": 0,
            "alertas": 0
        }
    
    async def verificar_backend_principal(self, session):
        """Verifica se o backend principal está respondendo"""
        try:
            url = f"{BACKEND_PRINCIPAL}/api/status"
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    self.resultados["backend_principal"] = True
                    logger.info(f"Backend principal está online: {data.get('status', 'Unknown')}")
                    return True
                else:
                    logger.error(f"Backend principal retornou status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Erro ao verificar backend principal: {str(e)}")
            return False
    
    async def verificar_api_incidentes(self, session):
        """Verifica se a API de incidentes está respondendo"""
        try:
            url = f"{API_INCIDENTES}/incidentes"
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    self.resultados["api_incidentes"] = True
                    self.resultados["incidentes"] = len(data.get("incidentes", []))
                    self.resultados["alertas"] = len(data.get("alertas", []))
                    logger.info(f"API de incidentes está online: {self.resultados['incidentes']} incidentes, {self.resultados['alertas']} alertas")
                    return True
                else:
                    logger.error(f"API de incidentes retornou status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Erro ao verificar API de incidentes: {str(e)}")
            return False
    
    async def verificar_entidades(self, session):
        """Verifica se as entidades estão sendo carregadas corretamente"""
        try:
            url = f"{BACKEND_PRINCIPAL}/api/entidades"
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    entidades = data.get("entidades", [])
                    self.resultados["entidades"] = len(entidades)
                    logger.info(f"Total de entidades: {self.resultados['entidades']}")
                    return True
                else:
                    logger.error(f"Endpoint de entidades retornou status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Erro ao verificar entidades: {str(e)}")
            return False
    
    async def verificar_frontend(self, session):
        """Verifica se o frontend está configurado corretamente para consumir as APIs"""
        try:
            # Verificar o arquivo vite.config.js
            with open("../frontend/vite.config.js", "r", encoding="utf-8") as f:
                config_conteudo = f.read()
                
            # Verificar se os proxys estão configurados
            proxy_backend = "'/api': {" in config_conteudo and "target: 'http://localhost:8000'" in config_conteudo
            proxy_incidentes = "'/api/incidentes': {" in config_conteudo and "target: 'http://localhost:8002'" in config_conteudo
            
            self.resultados["frontend"] = proxy_backend and proxy_incidentes
            
            if self.resultados["frontend"]:
                logger.info("Frontend está configurado corretamente com os proxys")
            else:
                logger.error("Frontend não está configurado corretamente com os proxys")
            
            return self.resultados["frontend"]
        except Exception as e:
            logger.error(f"Erro ao verificar frontend: {str(e)}")
            return False
    
    async def verificar_integracao(self, session):
        """Verifica se os sistemas estão integrados corretamente"""
        try:
            # Se backend principal, API de incidentes e frontend estiverem ok, verificar integracao
            if self.resultados["backend_principal"] and self.resultados["api_incidentes"] and self.resultados["frontend"]:
                # Verificar correlação entre incidentes e entidades
                url = f"{API_INCIDENTES}/correlacionar"
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Correlação de incidentes: {data.get('mensagem')}")
                        
                        # Verificar se há entidades associadas
                        url = f"{API_INCIDENTES}/entidades"
                        async with session.get(url, timeout=5) as response:
                            if response.status == 200:
                                data = await response.json()
                                entidades_associadas = data.get("entidades", {})
                                if entidades_associadas:
                                    self.resultados["integracao"] = True
                                    logger.info(f"Integração verificada: {len(entidades_associadas)} entidades associadas")
                                else:
                                    logger.warning("Não há entidades associadas")
                            else:
                                logger.error(f"Endpoint de entidades associadas retornou status {response.status}")
                    else:
                        logger.error(f"Endpoint de correlação retornou status {response.status}")
            else:
                logger.warning("Não é possível verificar integração pois algum componente não está funcionando")
            
            return self.resultados["integracao"]
        except Exception as e:
            logger.error(f"Erro ao verificar integração: {str(e)}")
            return False
    
    async def verificar_tudo(self):
        """Verifica todos os componentes do sistema"""
        async with aiohttp.ClientSession() as session:
            await self.verificar_backend_principal(session)
            await self.verificar_api_incidentes(session)
            await self.verificar_entidades(session)
            await self.verificar_frontend(session)
            await self.verificar_integracao(session)
        
        # Exibir resultados
        self.exibir_resultados()
        
        # Sugerir próximos passos
        self.sugerir_proximos_passos()
        
        return all([
            self.resultados["backend_principal"],
            self.resultados["api_incidentes"],
            self.resultados["frontend"],
            self.resultados["integracao"]
        ])
    
    def exibir_resultados(self):
        """Exibe os resultados da verificação em formato tabular"""
        print("\n=== Verificação do Sistema Analyst_IA ===")
        
        headers = ["Componente", "Status"]
        data = [
            ["Backend Principal", "✅ OK" if self.resultados["backend_principal"] else "❌ FALHA"],
            ["API de Incidentes", "✅ OK" if self.resultados["api_incidentes"] else "❌ FALHA"],
            ["Frontend Config", "✅ OK" if self.resultados["frontend"] else "❌ FALHA"],
            ["Integração", "✅ OK" if self.resultados["integracao"] else "❌ FALHA"]
        ]
        
        print(tabulate(data, headers=headers, tablefmt="simple"))
        
        print("\n=== Dados Disponíveis ===")
        headers = ["Tipo", "Quantidade"]
        data = [
            ["Entidades", self.resultados["entidades"]],
            ["Incidentes", self.resultados["incidentes"]],
            ["Alertas", self.resultados["alertas"]]
        ]
        
        print(tabulate(data, headers=headers, tablefmt="simple"))
    
    def sugerir_proximos_passos(self):
        """Sugere próximos passos com base nos resultados da verificação"""
        print("\n=== Próximos Passos ===")
        
        if not self.resultados["backend_principal"]:
            print("1. Iniciar o backend principal: cd backend && uvicorn main:app --reload")
        
        if not self.resultados["api_incidentes"]:
            print("2. Iniciar a API de incidentes: cd backend && uvicorn api_incidentes:app --port 8002 --reload")
        
        if not self.resultados["frontend"]:
            print("3. Verificar configuração de proxy no frontend/vite.config.js")
        
        if not self.resultados["integracao"] and self.resultados["backend_principal"] and self.resultados["api_incidentes"]:
            print("4. Adicionar dados de exemplo: curl -X POST http://localhost:8002/adicionar-dados-exemplo")
        
        if all([
            self.resultados["backend_principal"],
            self.resultados["api_incidentes"],
            self.resultados["frontend"]
        ]):
            print("5. Iniciar o frontend: cd frontend && npm run dev")
            
        print("\nPara iniciar todos os componentes em ordem:")
        print("1. Backend principal: cd backend && uvicorn main:app --reload")
        print("2. API de incidentes: cd backend && uvicorn api_incidentes:app --port 8002 --reload")
        print("3. Frontend: cd frontend && npm run dev")

async def main():
    """Função principal"""
    verificador = VerificadorSistema()
    sucesso = await verificador.verificar_tudo()
    
    # Retornar status code apropriado
    if not sucesso:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
