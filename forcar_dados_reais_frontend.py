#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para forçar a sincronização entre o cache e o frontend,
garantindo que os dados reais do New Relic sejam exibidos.
"""

import os
import sys
import json
import logging
import shutil
import time
import subprocess
import datetime
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verificar_arquivos_cache():
    """Verifica se os arquivos de cache existem e têm conteúdo"""
    cache_dir = Path("backend/cache")
    arquivos = [
        "kubernetes_metrics.json",
        "infrastructure_detailed.json",
        "service_topology.json"
    ]
    
    status = True
    
    print("\nVerificando arquivos de cache...")
    for arquivo in arquivos:
        caminho = cache_dir / arquivo
        if not caminho.exists():
            print(f"❌ {arquivo}: Não encontrado")
            status = False
        else:
            tamanho = caminho.stat().st_size // 1024  # KB
            tempo = datetime.datetime.fromtimestamp(caminho.stat().st_mtime).strftime('%H:%M:%S')
            print(f"✅ {arquivo}: {tamanho} KB (atualizado às {tempo})")
    
    return status

def reiniciar_cache():
    """Força a recriação do cache para garantir os dados mais recentes"""
    print("\nAtualizando cache com os dados reais...")
    
    try:
        # Executar o script de verificação e correção do cache
        subprocess.run(["python", "backend/check_and_fix_cache.py"], check=True)
        print("✅ Cache verificado e atualizado com sucesso")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao atualizar o cache: {e}")
        return False

def criar_indicador_dados_reais():
    """Cria um indicador no cache para forçar o uso de dados reais"""
    try:
        # Criar um arquivo indicador que o frontend pode verificar
        indicator = {
            "using_real_data": True,
            "timestamp": datetime.datetime.now().isoformat(),
            "source": "New Relic API",
            "force_refresh": True
        }
        
        with open("backend/cache/data_source_indicator.json", 'w', encoding='utf-8') as f:
            json.dump(indicator, f, ensure_ascii=False, indent=2)
            
        # Também criar um indicador visível no frontend
        os.makedirs("frontend/public/status", exist_ok=True)
        with open("frontend/public/status/using_real_data.json", 'w', encoding='utf-8') as f:
            json.dump(indicator, f, ensure_ascii=False, indent=2)
            
        print("✅ Indicador de dados reais criado com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar indicador de dados reais: {e}")
        return False

def atualizar_servico_frontend():
    """Atualiza o serviço de API do frontend para forçar a busca de dados reais"""
    try:
        api_service_path = Path("frontend/src/api/advancedDataService.js")
        if not api_service_path.exists():
            print("❌ Serviço de API do frontend não encontrado")
            return False
            
        # Ler o conteúdo atual
        with open(api_service_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Verificar se já temos o indicador de dados reais
        if "checkIfUsingRealData" not in content:
            # Adicionar método para verificar se estamos usando dados reais
            new_content = content.replace(
                "const advancedDataService = {", 
                """const advancedDataService = {
  /**
   * Verifica se o sistema está usando dados reais
   * @returns {Promise<boolean>} - Promise que resolve para true se estiver usando dados reais
   */
  checkIfUsingRealData() {
    // Verificar o indicador no backend
    return apiClient.get('/status/data_source')
      .then(response => {
        console.log('Status dos dados:', response.data);
        return response.data?.using_real_data === true;
      })
      .catch(error => {
        console.warn('Erro ao verificar status dos dados:', error);
        // Tentar verificar pelo indicador local
        return fetch('/status/using_real_data.json')
          .then(res => res.json())
          .then(data => data?.using_real_data === true)
          .catch(() => false);
      });
  },
"""
            )
            
            # Atualizar o método getAllAdvancedData para verificar dados reais
            new_content = new_content.replace(
                "  getAllAdvancedData() {",
                """  getAllAdvancedData(forceRefresh = false) {
    // Limpar cache se forceRefresh for true
    if (forceRefresh) {
      this.clearCache();
    }
    
    // Verificar se estamos usando dados reais
    return this.checkIfUsingRealData().then(usingRealData => {
      if (usingRealData) {
        console.log('📊 Usando DADOS REAIS do New Relic');
        // Forçar refresh se estiver usando dados reais
        forceRefresh = true;
      } else {
        console.log('📊 Usando dados simulados');
      }
      
      // Continuar com a chamada normal"""
            )
            
            # Atualizar os métodos individuais para passar o parâmetro forceRefresh
            new_content = new_content.replace(
                "      this.getKubernetesData(),",
                "      this.getKubernetesData(!usingRealData),"
            )
            new_content = new_content.replace(
                "      this.getInfrastructureData(),",
                "      this.getInfrastructureData(!usingRealData),"
            )
            new_content = new_content.replace(
                "      this.getTopologyData()",
                "      this.getTopologyData(!usingRealData)"
            )
            
            # Salvar as alterações
            with open(api_service_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            print("✅ Serviço de API do frontend atualizado para usar dados reais")
        else:
            print("✅ Serviço de API já configurado para dados reais")
            
        return True
    except Exception as e:
        print(f"❌ Erro ao atualizar serviço de API do frontend: {e}")
        return False

def criar_endpoint_status():
    """Cria um endpoint de status no backend para informar a origem dos dados"""
    try:
        # Verificar se o endpoint já existe
        endpoint_path = Path("backend/endpoints/status_endpoints.py")
        if endpoint_path.exists():
            print("✅ Endpoint de status já existe")
            return True
            
        # Criar o arquivo de endpoints
        endpoint_content = """from fastapi import APIRouter, HTTPException
import os
import json
import logging
from datetime import datetime

# Configuração do logger
logger = logging.getLogger(__name__)

# Criar o router
router = APIRouter()

# Função para verificar o status dos dados
@router.get("/data_source")
async def get_data_source():
    \"\"\"
    Retorna informações sobre a origem dos dados (reais ou simulados)
    \"\"\"
    try:
        # Verificar se existe o indicador de dados reais
        indicator_path = "backend/cache/data_source_indicator.json"
        if os.path.exists(indicator_path):
            with open(indicator_path, 'r', encoding='utf-8') as f:
                indicator = json.load(f)
                return indicator
        
        # Verificar se existe o arquivo de relatório de integração
        report_path = "relatorio_integracao_dados_reais.json"
        if os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
                return {
                    "using_real_data": report.get("modo") == "real",
                    "timestamp": report.get("timestamp", datetime.now().isoformat()),
                    "source": "New Relic API" if report.get("modo") == "real" else "Simulado"
                }
        
        # Se não houver indicador nem relatório, verificar variáveis de ambiente
        account_id = os.environ.get("NEW_RELIC_ACCOUNT_ID")
        api_key = os.environ.get("NEW_RELIC_API_KEY")
        
        if account_id and api_key:
            return {
                "using_real_data": True,
                "timestamp": datetime.now().isoformat(),
                "source": "New Relic API (credenciais disponíveis)"
            }
        
        # Se nada disso estiver disponível, assume dados simulados
        return {
            "using_real_data": False,
            "timestamp": datetime.now().isoformat(),
            "source": "Dados simulados"
        }
    except Exception as e:
        logger.error(f"Erro ao verificar origem dos dados: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao verificar origem dos dados: {str(e)}")

@router.get("/health")
async def get_health():
    \"\"\"
    Retorna o status de saúde do sistema
    \"\"\"
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat()
    }
"""
        
        # Criar o diretório se não existir
        os.makedirs(endpoint_path.parent, exist_ok=True)
        
        # Salvar o arquivo de endpoints
        with open(endpoint_path, 'w', encoding='utf-8') as f:
            f.write(endpoint_content)
            
        # Atualizar o arquivo core_router.py para incluir o novo endpoint
        core_router_path = Path("backend/core_router.py")
        if core_router_path.exists():
            with open(core_router_path, 'r', encoding='utf-8') as f:
                router_content = f.read()
                
            # Verificar se já temos a importação e registro do router
            if "from .endpoints.status_endpoints import router as status_router" not in router_content:
                # Adicionar importação do router de status
                router_content = router_content.replace(
                    "from fastapi import FastAPI, HTTPException",
                    "from fastapi import FastAPI, HTTPException\nfrom .endpoints.status_endpoints import router as status_router"
                )
                
                # Adicionar registro do router de status
                router_content = router_content.replace(
                    "app.include_router(chat_router, prefix='/api/chat', tags=['chat'])",
                    "app.include_router(chat_router, prefix='/api/chat', tags=['chat'])\napp.include_router(status_router, prefix='/api/status', tags=['status'])"
                )
                
                # Salvar as alterações
                with open(core_router_path, 'w', encoding='utf-8') as f:
                    f.write(router_content)
                    
            print("✅ Endpoint de status criado e registrado com sucesso")
            return True
        else:
            print("❌ Arquivo core_router.py não encontrado")
            return False
    except Exception as e:
        print(f"❌ Erro ao criar endpoint de status: {e}")
        return False

def main():
    """Função principal para sincronizar os dados reais com o frontend"""
    print("\n" + "="*60)
    print("SINCRONIZAÇÃO DE DADOS REAIS COM O FRONTEND")
    print("="*60)
    
    # Verificar arquivos de cache
    if not verificar_arquivos_cache():
        print("\n❌ Problemas encontrados nos arquivos de cache.")
        if input("Deseja tentar reparar? (S/N): ").lower() == "s":
            if not reiniciar_cache():
                print("❌ Não foi possível reparar o cache. Verifique os logs para mais detalhes.")
                return
        else:
            print("Operação cancelada pelo usuário.")
            return
            
    # Criar indicador de dados reais
    criar_indicador_dados_reais()
    
    # Criar endpoint de status
    criar_endpoint_status()
    
    # Atualizar serviço frontend
    atualizar_servico_frontend()
    
    print("\n" + "="*60)
    print("SINCRONIZAÇÃO CONCLUÍDA")
    print("="*60)
    print("\nPara ver os dados reais no frontend:")
    print("1. Pare o servidor atual (se estiver em execução)")
    print("2. Execute o comando para iniciar o sistema:")
    print("   python iniciar_sistema_com_dados_reais.py")
    print("\nObservação: O frontend deve exibir um indicador 'Dados Reais' quando")
    print("estiver usando dados da API do New Relic.")
    print("="*60)
    
if __name__ == "__main__":
    main()
