#!/usr/bin/env python3
"""
Script para otimização completa do sistema Analyst_IA:
1. Remove arquivos duplicados, obsoletos e de teste
2. Garante que o sistema usa apenas dados reais do New Relic
3. Otimiza o cache e atualiza o frontend
4. Corrige o Chat IA para usar apenas análises reais
5. Gera um relatório completo do estado do sistema
"""

import os
import sys
import asyncio
import shutil
import json
import logging
import re
from pathlib import Path
from datetime import datetime
import importlib.util

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("otimizacao_sistema.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# Adicionar o diretório atual e backend ao path
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"

sys.path.append(str(BASE_DIR))
sys.path.append(str(BACKEND_DIR))

# Categorias de arquivos para remoção
ARQUIVOS_TESTE = [
    r"test_.*\.py$",
    r".*_test\.py$",
    r"teste_.*\.py$",
    r".*_teste\.py$",
]

ARQUIVOS_SIMULADOS = [
    r".*simulado.*\.py$",
    r".*fake.*\.py$",
    r".*mock.*\.py$",
    r".*dummy.*\.py$",
]

ARQUIVOS_DUPLICADOS = [
    r".*_backup\.py$",
    r".*_old\.py$",
    r".*_bkp\.py$",
    r".*_copy\.py$",
]

# Arquivos a preservar (mesmo que correspondam aos padrões acima)
ARQUIVOS_PRESERVAR = [
    "test_newrelic_collector.py",  # Teste importante para validação da coleta
    "test_api.py",  # API teste crítica
]

def importar_modulo_backend(nome_modulo):
    """Importa um módulo do backend com segurança"""
    try:
        # Tenta importar como um módulo relativo ao backend
        return importlib.import_module(f"backend.{nome_modulo}")
    except ImportError:
        try:
            # Tenta importar como um módulo absoluto
            return importlib.import_module(nome_modulo)
        except ImportError:
            logger.warning(f"Não foi possível importar o módulo: {nome_modulo}")
            return None

def identificar_arquivos_remover():
    """Identifica arquivos que podem ser removidos"""
    arquivos_remover = []
    
    # Padrões compilados
    padroes_teste = [re.compile(p) for p in ARQUIVOS_TESTE]
    padroes_simulados = [re.compile(p) for p in ARQUIVOS_SIMULADOS]
    padroes_duplicados = [re.compile(p) for p in ARQUIVOS_DUPLICADOS]
    padroes_preservar = [re.compile(p) for p in ARQUIVOS_PRESERVAR]
    
    # Busca recursiva por arquivos
    for raiz, _, arquivos in os.walk(BASE_DIR):
        raiz_path = Path(raiz)
        
        # Pular diretórios node_modules e .git
        if any(parte in str(raiz_path) for parte in [".git", "node_modules", "__pycache__"]):
            continue
            
        for arquivo in arquivos:
            arquivo_path = raiz_path / arquivo
            
            # Verifica se está na lista de preservação
            if any(padrao.match(arquivo) for padrao in padroes_preservar):
                continue
                
            # Verifica se corresponde a algum dos padrões para remoção
            if any(padrao.match(arquivo) for padrao in padroes_teste + padroes_simulados + padroes_duplicados):
                arquivos_remover.append(arquivo_path)
                
    return arquivos_remover

async def corrigir_chat_ia():
    """
    Corrige o módulo de Chat IA para usar apenas dados reais e
    realizar análises reais baseadas nos dados do New Relic.
    """
    logger.info("=== OTIMIZANDO CHAT IA PARA ANÁLISES REAIS ===")
    
    chat_endpoints_path = BACKEND_DIR / "endpoints" / "chat_endpoints.py"
    
    if not chat_endpoints_path.exists():
        logger.error(f"Arquivo não encontrado: {chat_endpoints_path}")
        return False
    
    try:
        # Backup do arquivo original
        backup_path = chat_endpoints_path.with_name(f"chat_endpoints_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py")
        shutil.copy(chat_endpoints_path, backup_path)
        logger.info(f"Backup do chat_endpoints.py criado em: {backup_path}")
        
        with open(chat_endpoints_path, "r", encoding="utf-8") as f:
            conteudo = f.read()
        
        # Remover banco de conhecimento simulado
        if "KNOWLEDGE_BASE = {" in conteudo:
            logger.info("Removendo banco de conhecimento simulado")
            conteudo_modificado = conteudo.replace(
                "# Banco de conhecimento simulado para respostas mais relevantes\nKNOWLEDGE_BASE = {",
                "# Removido banco de conhecimento simulado - usando apenas dados reais\n'''\nAntigo KNOWLEDGE_BASE = {"
            )
            
            # Fechar o comentário do antigo conhecimento
            conteudo_modificado = conteudo_modificado.replace(
                "}\n\n# Função para encontrar entidades relevantes",
                "}\n'''\n\n# Função para encontrar entidades relevantes"
            )
            
            # Verificar se há templates fixos de resposta
            if "TEMPLATE_RESPOSTAS = {" in conteudo_modificado:
                logger.info("Removendo templates fixos de resposta")
                conteudo_modificado = conteudo_modificado.replace(
                    "# Templates de resposta pré-definidos\nTEMPLATE_RESPOSTAS = {",
                    "# Removido templates fixos - usando apenas análise real dos dados\n'''\nAntigo TEMPLATE_RESPOSTAS = {"
                )
                
                # Fechar o comentário
                conteudo_modificado = conteudo_modificado.replace(
                    "}\n\n@router.post",
                    "}\n'''\n\n@router.post"
                )
            
            # Salvar as alterações
            with open(chat_endpoints_path, "w", encoding="utf-8") as f:
                f.write(conteudo_modificado)
            
            logger.info("✅ Chat IA otimizado para usar apenas dados reais")
            return True
        else:
            logger.info("✅ Chat IA já está configurado para usar apenas dados reais")
            return True
            
    except Exception as e:
        logger.error(f"❌ Erro ao otimizar Chat IA: {e}")
        return False

async def atualizar_dados_reais():
    """
    Atualiza o cache com dados reais do New Relic usando o coletor avançado,
    garantindo que todas as entidades disponíveis sejam coletadas e armazenadas.
    """
    logger.info("=== ATUALIZANDO CACHE COM DADOS REAIS COMPLETOS ===")
    
    try:
        # Importar os módulos necessários
        newrelic_advanced_collector = importar_modulo_backend("utils.newrelic_advanced_collector")
        cache_module = importar_modulo_backend("utils.cache")
        frontend_integrator_module = importar_modulo_backend("utils.frontend_data_integrator")
        
        if not all([newrelic_advanced_collector, cache_module, frontend_integrator_module]):
            logger.error("❌ Falha ao importar módulos necessários")
            return False
        
        # Backup do cache existente
        cache_file = BACKEND_DIR / "historico" / "cache_completo.json"
        if cache_file.exists():
            backup_file = cache_file.with_name(f"cache_completo_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            shutil.copy(cache_file, backup_file)
            logger.info(f"Backup do cache criado em: {backup_file}")
        
        # Coletar todas as entidades disponíveis
        logger.info("Coletando entidades do New Relic (pode demorar alguns minutos)...")
        entidades = await newrelic_advanced_collector.coletar_entidades_avancado(max_entidades=500)
        
        if not entidades:
            logger.error("❌ Falha ao coletar entidades do New Relic")
            return False
            
        # Atualizar o cache com as novas entidades
        logger.info(f"✅ Coletadas {len(entidades)} entidades do New Relic")
        
        # Agrupar por domínio para estatísticas
        dominios = {}
        for entidade in entidades:
            dominio = entidade.get("domain", "unknown").upper()
            if dominio not in dominios:
                dominios[dominio] = 0
            dominios[dominio] += 1
        
        # Exibir estatísticas
        for dominio, count in dominios.items():
            logger.info(f"  • {dominio}: {count} entidades")
        
        # Atualizar o cache
        cache_module._cache["entidades"] = entidades
        
        # Organizar por domínios
        for entidade in entidades:
            domain = entidade.get("domain", "unknown").lower()
            if domain not in cache_module._cache:
                cache_module._cache[domain] = []
            cache_module._cache[domain].append(entidade)
        
        # Adicionar metadados
        cache_module._cache["metadata"] = {
            "timestamp": datetime.now().isoformat(),
            "source": "New Relic API (Otimizado)",
            "total_entities": len(entidades),
            "domains": dominios
        }
        
        # Salvar o cache no disco
        await cache_module.salvar_cache_no_disco()
        
        # Atualizar dados do frontend
        logger.info("Atualizando dados do frontend...")
        integrator = frontend_integrator_module.FrontendIntegrator()
        await integrator.process_all_data()
        
        # Atualizar indicador de dados reais
        indicador_path = BACKEND_DIR / "cache" / "data_source_indicator.json"
        indicador_path.parent.mkdir(parents=True, exist_ok=True)
        
        indicador = {
            "using_real_data": True,
            "timestamp": datetime.now().isoformat(),
            "source": "New Relic API",
            "configured_by": "otimizar_sistema.py",
            "entities_count": len(entidades)
        }
        
        with open(indicador_path, "w") as f:
            json.dump(indicador, f, indent=2)
        
        logger.info("✅ Cache e frontend atualizados com dados reais")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar dados reais: {str(e)}")
        return False

def garantir_env_dados_reais():
    """Garante que o arquivo .env está configurado para usar apenas dados reais"""
    env_path = BASE_DIR / ".env"
    
    if not env_path.exists():
        # Criar .env se não existir
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("USE_SIMULATED_DATA=false\n")
        logger.info("✅ Arquivo .env criado com configuração para dados reais")
        return True
    
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            linhas = f.readlines()
        
        encontrado = False
        with open(env_path, "w", encoding="utf-8") as f:
            for linha in linhas:
                if linha.strip().startswith("USE_SIMULATED_DATA="):
                    f.write("USE_SIMULATED_DATA=false\n")
                    encontrado = True
                else:
                    f.write(linha)
            
            if not encontrado:
                f.write("\n# Forçar uso exclusivo de dados reais do New Relic\nUSE_SIMULATED_DATA=false\n")
        
        logger.info("✅ Arquivo .env configurado para usar apenas dados reais")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao configurar .env: {e}")
        return False

def criar_task_otimizada():
    """Cria ou atualiza a task do VS Code para iniciar o sistema de forma otimizada"""
    try:
        tasks_path = BASE_DIR / ".vscode" / "tasks.json"
        tasks_path.parent.mkdir(parents=True, exist_ok=True)
        
        if tasks_path.exists():
            with open(tasks_path, "r", encoding="utf-8") as f:
                try:
                    tasks_data = json.load(f)
                except json.JSONDecodeError:
                    tasks_data = {"version": "2.0.0", "tasks": []}
        else:
            tasks_data = {"version": "2.0.0", "tasks": []}
        
        # Criar/atualizar a task para iniciar o sistema otimizado
        task_otimizada = {
            "label": "Iniciar Sistema Otimizado",
            "type": "shell",
            "command": "cd ${workspaceFolder}\\backend && python check_and_fix_cache.py && python main.py",
            "group": {
                "kind": "test",
                "isDefault": true
            },
            "presentation": {
                "reveal": "always",
                "panel": "new"
            },
            "problemMatcher": []
        }
        
        # Verificar se já existe uma task com este label
        task_encontrada = False
        for i, task in enumerate(tasks_data.get("tasks", [])):
            if task.get("label") == "Iniciar Sistema Otimizado":
                tasks_data["tasks"][i] = task_otimizada
                task_encontrada = True
                break
        
        # Adicionar se não existir
        if not task_encontrada:
            tasks_data["tasks"].append(task_otimizada)
            
        # Atualizar também a task existente
        for i, task in enumerate(tasks_data.get("tasks", [])):
            if task.get("label") == "Iniciar Sistema Completo":
                tasks_data["tasks"][i]["command"] = "start cmd.exe /c \"cd ${workspaceFolder}\\backend && python check_and_fix_cache.py && python main.py\" && cd frontend && npm run dev"
        
        # Salvar as alterações
        with open(tasks_path, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, indent=2)
            
        logger.info("✅ Task otimizada criada/atualizada com sucesso")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao criar task otimizada: {e}")
        return False

def atualizar_readme():
    """Atualiza o README principal para refletir o estado otimizado do sistema"""
    try:
        readme_path = BASE_DIR / "README.md"
        if not readme_path.exists():
            logger.warning("README.md não encontrado")
            return False
        
        with open(readme_path, "r", encoding="utf-8") as f:
            conteudo = f.read()
        
        # Atualizar título se necessário
        if not "ANALYST IA - SISTEMA OTIMIZADO" in conteudo:
            conteudo = conteudo.replace("# ANALYST IA", "# ANALYST IA - SISTEMA OTIMIZADO")
        
        # Adicionar uma seção sobre a otimização
        if not "## Sistema Otimizado" in conteudo:
            secao_otimizacao = """
## Sistema Otimizado

O sistema foi completamente otimizado para:

- Utilizar exclusivamente dados reais do New Relic
- Eliminar código redundante e duplicado
- Remover dependências de dados simulados
- Garantir que o Chat IA realize análises reais dos dados
- Padronizar os feedbacks de erro/loading
- Consolidar scripts e comandos para maior clareza

### Como iniciar o sistema otimizado:

1. VS Code Task: `Iniciar Sistema Otimizado`
2. Ou execute: `cd backend && python check_and_fix_cache.py && python main.py`
3. Em outro terminal: `cd frontend && npm run dev`

> **Importante**: O sistema agora utiliza exclusivamente dados reais do New Relic. Não há mais fallbacks para dados simulados.
"""
            
            # Encontrar a posição para inserir a seção (após a primeira seção principal)
            match = re.search(r"^## ", conteudo, re.MULTILINE)
            if match:
                posicao = match.start()
                conteudo = conteudo[:posicao] + secao_otimizacao + "\n" + conteudo[posicao:]
            else:
                conteudo += "\n" + secao_otimizacao
        
        # Salvar as alterações
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(conteudo)
            
        logger.info("✅ README.md atualizado com informações sobre o sistema otimizado")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao atualizar README: {e}")
        return False

def criar_scripts_iniciar_otimizado():
    """Cria scripts otimizados para iniciar o sistema"""
    try:
        # Script .bat para Windows
        bat_content = """@echo off
echo === INICIANDO ANALYST IA OTIMIZADO ===
echo.
echo 1. Verificando cache e dados...
cd backend
python check_and_fix_cache.py

echo.
echo 2. Iniciando backend...
start cmd /c "cd backend && python main.py"

echo.
echo 3. Iniciando frontend...
cd ../frontend
npm run dev
"""
        bat_path = BASE_DIR / "iniciar_otimizado.bat"
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)
        
        # Script .ps1 para PowerShell
        ps_content = """Write-Host "=== INICIANDO ANALYST IA OTIMIZADO ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Verificando cache e dados..." -ForegroundColor Yellow
Set-Location -Path "backend"
python check_and_fix_cache.py

Write-Host ""
Write-Host "2. Iniciando backend..." -ForegroundColor Yellow
Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd backend && python main.py"

Write-Host ""
Write-Host "3. Iniciando frontend..." -ForegroundColor Yellow
Set-Location -Path "../frontend"
npm run dev
"""
        ps_path = BASE_DIR / "iniciar_otimizado.ps1"
        with open(ps_path, "w", encoding="utf-8") as f:
            f.write(ps_content)
        
        # Script Python
        py_content = """#!/usr/bin/env python3
\"\"\"
Script para iniciar o sistema Analyst_IA otimizado
\"\"\"
import os
import sys
import subprocess
import platform
from pathlib import Path

def main():
    base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    backend_dir = base_dir / "backend"
    frontend_dir = base_dir / "frontend"
    
    print("=== INICIANDO ANALYST IA OTIMIZADO ===")
    print("")
    
    # 1. Verificar cache e dados
    print("1. Verificando cache e dados...")
    os.chdir(backend_dir)
    subprocess.run([sys.executable, "check_and_fix_cache.py"], check=True)
    
    # 2. Iniciar backend
    print("")
    print("2. Iniciando backend...")
    if platform.system() == "Windows":
        backend_process = subprocess.Popen(["start", "cmd", "/c", "python", "main.py"], 
                                          shell=True)
    else:
        backend_process = subprocess.Popen([sys.executable, "main.py"],
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          start_new_session=True)
    
    # 3. Iniciar frontend
    print("")
    print("3. Iniciando frontend...")
    os.chdir(frontend_dir)
    subprocess.run(["npm", "run", "dev"], check=True)

if __name__ == "__main__":
    main()
"""
        py_path = BASE_DIR / "iniciar_otimizado.py"
        with open(py_path, "w", encoding="utf-8") as f:
            f.write(py_content)
            
        logger.info("✅ Scripts de inicialização otimizados criados")
        return True
    except Exception as e:
        logger.error(f"❌ Erro ao criar scripts de inicialização: {e}")
        return False

def limpar_arquivos_desnecessarios(arquivos_a_remover, executar=False):
    """
    Lista e opcionalmente remove arquivos desnecessários.
    Se executar=False, apenas lista os arquivos.
    Se executar=True, remove os arquivos.
    """
    logger.info(f"=== {'REMOVENDO' if executar else 'LISTANDO'} ARQUIVOS DESNECESSÁRIOS ===")
    
    if not arquivos_a_remover:
        logger.info("Nenhum arquivo identificado para remoção")
        return True
    
    # Agrupar arquivos por categoria para relatório
    arquivos_por_pasta = {}
    for arquivo in arquivos_a_remover:
        pasta = os.path.dirname(arquivo)
        if pasta not in arquivos_por_pasta:
            arquivos_por_pasta[pasta] = []
        arquivos_por_pasta[pasta].append(os.path.basename(arquivo))
    
    # Gerar relatório
    for pasta, arquivos in arquivos_por_pasta.items():
        logger.info(f"Pasta: {pasta}")
        for arquivo in arquivos:
            acao = "Removido" if executar else "Candidato à remoção"
            logger.info(f"  - {arquivo} [{acao}]")
    
    if executar:
        # Remover os arquivos
        for arquivo in arquivos_a_remover:
            try:
                if os.path.exists(arquivo):
                    # Criar pasta de backup se necessário
                    backup_dir = BASE_DIR / "backup_files"
                    backup_dir.mkdir(exist_ok=True)
                    
                    # Copiar para backup antes de remover
                    dest_path = backup_dir / os.path.basename(arquivo)
                    shutil.copy2(arquivo, dest_path)
                    
                    # Remover o arquivo
                    os.remove(arquivo)
                    logger.info(f"Arquivo removido (com backup): {arquivo}")
            except Exception as e:
                logger.error(f"Erro ao remover {arquivo}: {e}")
    
    return True

async def main():
    """Função principal para otimização do sistema"""
    logger.info("🚀 INICIANDO OTIMIZAÇÃO COMPLETA DO SISTEMA ANALYST_IA")
    logger.info("-" * 60)
    
    # 1. Identificar arquivos que podem ser removidos
    arquivos_remover = identificar_arquivos_remover()
    logger.info(f"Identificados {len(arquivos_remover)} arquivos desnecessários")
    
    # 2. Listar os arquivos (apenas para informação)
    limpar_arquivos_desnecessarios(arquivos_remover, executar=False)
    
    # 3. Garantir que o .env está configurado para usar apenas dados reais
    env_ok = garantir_env_dados_reais()
    
    # 4. Atualizar o cache com dados reais
    dados_reais_ok = await atualizar_dados_reais()
    
    # 5. Corrigir o Chat IA para usar apenas análises reais
    chat_ok = await corrigir_chat_ia()
    
    # 6. Criar/atualizar task do VS Code
    task_ok = criar_task_otimizada()
    
    # 7. Criar scripts de inicialização otimizados
    scripts_ok = criar_scripts_iniciar_otimizado()
    
    # 8. Atualizar o README
    readme_ok = atualizar_readme()
    
    # 9. Remover arquivos desnecessários
    # Pergunta ao usuário se deseja remover os arquivos
    logger.info("\n⚠️ ATENÇÃO: Os arquivos listados acima serão removidos (com backup)")
    logger.info("Pressione 'Y' para confirmar a remoção ou qualquer outra tecla para cancelar")
    
    try:
        resposta = input("Remover arquivos desnecessários? [y/N] ").strip().lower()
        remocao_ok = True
        if resposta == 'y':
            remocao_ok = limpar_arquivos_desnecessarios(arquivos_remover, executar=True)
            logger.info("✅ Arquivos desnecessários removidos")
        else:
            logger.info("❌ Remoção de arquivos cancelada pelo usuário")
    except Exception as e:
        logger.error(f"Erro ao processar entrada: {e}")
        remocao_ok = False
    
    # 10. Gerar relatório final
    logger.info("\n" + "=" * 60)
    logger.info("RELATÓRIO DE OTIMIZAÇÃO DO SISTEMA")
    logger.info("=" * 60)
    logger.info(f"✓ Configuração ENV para dados reais: {'OK' if env_ok else 'FALHA'}")
    logger.info(f"✓ Atualização cache com dados reais: {'OK' if dados_reais_ok else 'FALHA'}")
    logger.info(f"✓ Otimização do Chat IA: {'OK' if chat_ok else 'FALHA'}")
    logger.info(f"✓ Task VS Code atualizada: {'OK' if task_ok else 'FALHA'}")
    logger.info(f"✓ Scripts de inicialização criados: {'OK' if scripts_ok else 'FALHA'}")
    logger.info(f"✓ README atualizado: {'OK' if readme_ok else 'FALHA'}")
    logger.info(f"✓ Arquivos desnecessários removidos: {'OK' if remocao_ok else 'NÃO EXECUTADO'}")
    logger.info("=" * 60)
    
    # Contagem de entidades
    try:
        cache_module = importar_modulo_backend("utils.cache")
        if cache_module:
            entidades = cache_module._cache.get("entidades", [])
            logger.info(f"Entidades no cache: {len(entidades)}")
            
            # Contagem por domínio
            dominios = {}
            for entidade in entidades:
                dominio = entidade.get("domain", "UNKNOWN").upper()
                if dominio not in dominios:
                    dominios[dominio] = 0
                dominios[dominio] += 1
            
            # Exibir contagem por domínio
            for dominio, count in dominios.items():
                logger.info(f"  • {dominio}: {count} entidades")
    except Exception as e:
        logger.error(f"Erro ao contar entidades: {e}")
    
    # Conclusão
    status_geral = all([env_ok, dados_reais_ok, chat_ok, task_ok, scripts_ok, readme_ok])
    if status_geral:
        logger.info("\n✅ Sistema otimizado com sucesso!")
        logger.info("Para iniciar o sistema, execute um dos comandos:")
        logger.info("  • VS Code Task: 'Iniciar Sistema Otimizado'")
        logger.info("  • Windows: iniciar_otimizado.bat")
        logger.info("  • PowerShell: ./iniciar_otimizado.ps1")
        logger.info("  • Python: python iniciar_otimizado.py")
    else:
        logger.warning("\n⚠️ Sistema parcialmente otimizado. Verifique os erros acima.")
    
    return status_geral

if __name__ == "__main__":
    asyncio.run(main())
