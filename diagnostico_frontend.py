#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para diagnóstico e correção de problemas no frontend do Analyst_IA.

Este script:
1. Verifica problemas comuns no código do frontend
2. Corrige automaticamente problemas identificados
3. Gera um relatório de problemas e soluções
"""

import os
import sys
import json
import re
import logging
import shutil
from pathlib import Path
from datetime import datetime
import argparse

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/diagnostico_frontend.log", mode='a')
    ]
)

logger = logging.getLogger(__name__)
os.makedirs("logs", exist_ok=True)

# Diretórios principais
FRONTEND_DIR = Path("frontend")
SRC_DIR = FRONTEND_DIR / "src"
COMPONENTS_DIR = SRC_DIR / "components"

class FrontendDiagnostico:
    def __init__(self):
        """Inicializa o diagnóstico do frontend"""
        self.problemas = []
        self.correcoes = []
        self.backup_realizado = False
        
    def verificar_estrutura_frontend(self):
        """Verifica se a estrutura básica do frontend está presente"""
        diretorios_essenciais = [
            FRONTEND_DIR,
            SRC_DIR,
            COMPONENTS_DIR,
            SRC_DIR / "assets",
            SRC_DIR / "views",
            SRC_DIR / "router"
        ]
        
        for diretorio in diretorios_essenciais:
            if not diretorio.exists():
                self.problemas.append({
                    "tipo": "estrutura",
                    "gravidade": "alta",
                    "mensagem": f"Diretório essencial não encontrado: {diretorio}",
                    "solucao": "Restaure o diretório a partir do repositório ou backup"
                })
                logger.warning(f"Diretório essencial não encontrado: {diretorio}")
        
        arquivos_essenciais = [
            FRONTEND_DIR / "package.json",
            SRC_DIR / "main.js",
            SRC_DIR / "App.vue"
        ]
        
        for arquivo in arquivos_essenciais:
            if not arquivo.exists():
                self.problemas.append({
                    "tipo": "estrutura",
                    "gravidade": "alta",
                    "mensagem": f"Arquivo essencial não encontrado: {arquivo}",
                    "solucao": "Restaure o arquivo a partir do repositório ou backup"
                })
                logger.warning(f"Arquivo essencial não encontrado: {arquivo}")
    
    def fazer_backup_arquivos(self):
        """Faz backup de arquivos importantes antes de fazer alterações"""
        if self.backup_realizado:
            return
            
        backup_dir = Path("backup_frontend_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(backup_dir, exist_ok=True)
        
        # Arquivos para backup
        arquivos_backup = [
            SRC_DIR / "main.js",
            SRC_DIR / "App.vue",
            SRC_DIR / "router.js",
            FRONTEND_DIR / "package.json"
        ]
        
        for arquivo in arquivos_backup:
            if arquivo.exists():
                shutil.copy2(arquivo, backup_dir / arquivo.name)
                
        logger.info(f"Backup realizado em: {backup_dir}")
        self.backup_realizado = True
    
    def verificar_problemas_icones(self):
        """Verifica problemas de importação e configuração de ícones"""
        main_js_path = SRC_DIR / "main.js"
        
        if not main_js_path.exists():
            return
            
        with open(main_js_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            
        # Verificar importações do FontAwesome
        if "fontawesome" in conteudo.lower() or "@fortawesome" in conteudo:
            # Verificar se há importações corretas
            padrao_importacao = re.compile(r"import\s+\{\s*[^}]*?library[^}]*?\}\s+from\s+['\"]\@fortawesome")
            if not padrao_importacao.search(conteudo):
                self.problemas.append({
                    "tipo": "icones",
                    "gravidade": "média",
                    "arquivo": str(main_js_path),
                    "mensagem": "Possível problema na importação da biblioteca FontAwesome",
                    "solucao": "Corrigir importações do FontAwesome no main.js"
                })
                
            # Verificar adições à biblioteca
            padrao_adicao = re.compile(r"library\.add\s*\(")
            if not padrao_adicao.search(conteudo):
                self.problemas.append({
                    "tipo": "icones",
                    "gravidade": "média",
                    "arquivo": str(main_js_path),
                    "mensagem": "Não foi encontrado o código para adicionar ícones à biblioteca FontAwesome",
                    "solucao": "Adicionar ícones à biblioteca FontAwesome no main.js"
                })
                
            # Verificar importação de marcas (brands)
            if "fas" in conteudo and "far" in conteudo and "fab" not in conteudo and "@fortawesome/free-brands-svg-icons" not in conteudo:
                self.problemas.append({
                    "tipo": "icones",
                    "gravidade": "baixa",
                    "arquivo": str(main_js_path),
                    "mensagem": "Importação de ícones de marcas (brands) ausente",
                    "solucao": "Adicionar importação de ícones de marcas se necessário"
                })
    
    def verificar_problemas_axios(self):
        """Verifica problemas na configuração e uso do Axios"""
        axios_path = SRC_DIR / "api" / "axios.js"
        interceptors_path = SRC_DIR / "interceptors.js"
        
        if axios_path.exists():
            with open(axios_path, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                
            # Verificar configuração de timeout
            if "timeout:" not in conteudo:
                self.problemas.append({
                    "tipo": "axios",
                    "gravidade": "baixa",
                    "arquivo": str(axios_path),
                    "mensagem": "Configuração de timeout ausente no Axios",
                    "solucao": "Adicionar timeout para evitar requisições pendentes"
                })
                
            # Verificar tratamento de erros
            if "interceptors" not in conteudo and not interceptors_path.exists():
                self.problemas.append({
                    "tipo": "axios",
                    "gravidade": "média",
                    "arquivo": str(axios_path),
                    "mensagem": "Interceptores Axios não configurados",
                    "solucao": "Implementar interceptores para tratar erros de API"
                })
    
    def verificar_tratamento_erros_componentes(self):
        """Verifica se componentes principais têm tratamento de erros adequado"""
        # Verificar componente InfraAvancada.vue
        infra_avancada_path = COMPONENTS_DIR / "pages" / "InfraAvancada.vue"
        
        if infra_avancada_path.exists():
            with open(infra_avancada_path, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                
            # Verificar tratamento de erro básico
            if "v-if=\"error\"" not in conteudo:
                self.problemas.append({
                    "tipo": "componente",
                    "gravidade": "média",
                    "arquivo": str(infra_avancada_path),
                    "mensagem": "Tratamento de erros pode estar incompleto em InfraAvancada.vue",
                    "solucao": "Adicionar tratamento de erros adequado"
                })
                
            # Verificar feedback de carregamento
            if "v-if=\"loading\"" not in conteudo:
                self.problemas.append({
                    "tipo": "componente",
                    "gravidade": "baixa",
                    "arquivo": str(infra_avancada_path),
                    "mensagem": "Feedback de carregamento ausente em InfraAvancada.vue",
                    "solucao": "Adicionar indicador de carregamento"
                })
    
    def corrigir_problemas_icones(self):
        """Corrige problemas de configuração de ícones"""
        self.fazer_backup_arquivos()
        
        main_js_path = SRC_DIR / "main.js"
        if not main_js_path.exists():
            logger.error(f"Arquivo não encontrado: {main_js_path}")
            return
            
        with open(main_js_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            
        # Verifica se há problemas para corrigir
        problemas_icones = [p for p in self.problemas if p["tipo"] == "icones" and p["arquivo"] == str(main_js_path)]
        
        if not problemas_icones:
            logger.info("Nenhum problema de ícones para corrigir")
            return
            
        # Verificar se já tem importações do FontAwesome
        tem_fontawesome = "fontawesome" in conteudo.lower() or "@fortawesome" in conteudo
        
        if tem_fontawesome:
            # Corrigir importações existentes
            logger.info("Corrigindo importações existentes do FontAwesome")
            
            # Verificar importações básicas
            importacoes_basicas = [
                "import { library } from '@fortawesome/fontawesome-svg-core'",
                "import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'",
                "import { fas } from '@fortawesome/free-solid-svg-icons'",
                "import { far } from '@fortawesome/free-regular-svg-icons'"
            ]
            
            # Verificar importação de brands
            if "fab" not in conteudo and "@fortawesome/free-brands-svg-icons" not in conteudo:
                importacoes_basicas.append("import { fab } from '@fortawesome/free-brands-svg-icons'")
                
            # Adicionar importações que estão faltando
            for importacao in importacoes_basicas:
                if importacao not in conteudo:
                    # Encontrar seção de importações
                    padrao_ultima_importacao = re.compile(r"(import\s+.*?['\"]\s*;?\s*)\n")
                    correspondencias = list(padrao_ultima_importacao.finditer(conteudo))
                    
                    if correspondencias:
                        ultima_importacao = correspondencias[-1]
                        pos = ultima_importacao.end()
                        conteudo = conteudo[:pos] + f"\n{importacao}" + conteudo[pos:]
                        logger.info(f"Adicionada importação: {importacao}")
                    else:
                        # Adicionar no início do arquivo
                        conteudo = f"{importacao}\n{conteudo}"
                        logger.info(f"Adicionada importação no início: {importacao}")
            
            # Verificar adição à biblioteca
            if "library.add" not in conteudo:
                padrao_criacao_vue = re.compile(r"new\s+Vue\s*\(\s*\{")
                correspondencias = list(padrao_criacao_vue.finditer(conteudo))
                
                if correspondencias:
                    pos = correspondencias[0].start()
                    novo_codigo = "// Adicionar ícones à biblioteca FontAwesome\nlibrary.add(fas, far, fab);\n\n"
                    conteudo = conteudo[:pos] + novo_codigo + conteudo[pos:]
                    logger.info("Adicionada configuração de ícones à biblioteca FontAwesome")
                else:
                    # Adicionar antes do registro de componentes
                    padrao_componente = re.compile(r"Vue\.component\s*\(\s*['\"]")
                    correspondencias = list(padrao_componente.finditer(conteudo))
                    
                    if correspondencias:
                        pos = correspondencias[0].start()
                        novo_codigo = "// Adicionar ícones à biblioteca FontAwesome\nlibrary.add(fas, far, fab);\n\n"
                        conteudo = conteudo[:pos] + novo_codigo + conteudo[pos:]
                        logger.info("Adicionada configuração de ícones à biblioteca FontAwesome")
            elif "fab" not in conteudo and ", fab" not in conteudo:
                # Adicionar fab à chamada existente de library.add
                conteudo = re.sub(
                    r"library\.add\s*\(\s*(fas\s*,\s*far|far\s*,\s*fas|fas|far)\s*\)",
                    r"library.add(\1, fab)",
                    conteudo
                )
                logger.info("Adicionado fab à chamada existente de library.add")
        
            # Registrar componente FontAwesomeIcon se ainda não estiver registrado
            if "Vue.component('font-awesome-icon'" not in conteudo:
                padrao_nova_vue = re.compile(r"new\s+Vue\s*\(\s*\{")
                correspondencias = list(padrao_nova_vue.finditer(conteudo))
                
                if correspondencias:
                    pos = correspondencias[0].start()
                    novo_codigo = "// Registrar componente FontAwesomeIcon\nVue.component('font-awesome-icon', FontAwesomeIcon);\n\n"
                    conteudo = conteudo[:pos] + novo_codigo + conteudo[pos:]
                    logger.info("Registrado componente FontAwesomeIcon")
                
            # Salvar alterações
            with open(main_js_path, 'w', encoding='utf-8') as f:
                f.write(conteudo)
                
            self.correcoes.append({
                "tipo": "icones",
                "arquivo": str(main_js_path),
                "mensagem": "Corrigidas importações e configuração do FontAwesome"
            })
            logger.info(f"Correções aplicadas ao arquivo: {main_js_path}")
            
            # Verificar package.json para garantir que as dependências estão instaladas
            package_json_path = FRONTEND_DIR / "package.json"
            if package_json_path.exists():
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                
                dependencies = package_data.get("dependencies", {})
                devDependencies = package_data.get("devDependencies", {})
                all_dependencies = {**dependencies, **devDependencies}
                
                fontawesome_deps = [
                    "@fortawesome/fontawesome-svg-core",
                    "@fortawesome/vue-fontawesome",
                    "@fortawesome/free-solid-svg-icons",
                    "@fortawesome/free-regular-svg-icons",
                    "@fortawesome/free-brands-svg-icons"
                ]
                
                missing_deps = [dep for dep in fontawesome_deps if dep not in all_dependencies]
                
                if missing_deps:
                    self.problemas.append({
                        "tipo": "dependencias",
                        "gravidade": "alta",
                        "arquivo": str(package_json_path),
                        "mensagem": f"Dependências FontAwesome ausentes: {', '.join(missing_deps)}",
                        "solucao": "Execute 'npm install --save " + " ".join(missing_deps) + "'"
                    })
    
    def criar_interceptores_axios(self):
        """Cria ou atualiza arquivo de interceptores Axios"""
        self.fazer_backup_arquivos()
        
        interceptors_path = SRC_DIR / "interceptors.js"
        
        # Conteúdo para o arquivo de interceptores
        interceptors_content = """/**
 * Interceptores globais para requisições Axios
 * Trata erros de API de forma centralizada e padronizada
 */

import axios from 'axios';

// Adicionar interceptores de requisição
axios.interceptors.request.use(
  config => {
    // Código a ser executado antes de enviar a requisição
    return config;
  },
  error => {
    // Código a ser executado em caso de erro na requisição
    console.error('Erro na requisição:', error);
    return Promise.reject(error);
  }
);

// Adicionar interceptores de resposta
axios.interceptors.response.use(
  response => {
    // Código a ser executado com respostas bem-sucedidas
    return response;
  },
  error => {
    // Código a ser executado com respostas de erro
    
    // Informações de erro padrão
    let errorMessage = 'Erro desconhecido na comunicação com o servidor';
    let statusCode = 500;
    let errorDetails = null;
    
    if (error.response) {
      // O servidor respondeu com um status de erro
      statusCode = error.response.status;
      
      switch(statusCode) {
        case 400:
          errorMessage = 'Requisição inválida';
          break;
        case 401:
          errorMessage = 'Não autorizado';
          break;
        case 403:
          errorMessage = 'Acesso negado';
          break;
        case 404:
          errorMessage = 'Recurso não encontrado';
          break;
        case 500:
          errorMessage = 'Erro interno do servidor';
          break;
        default:
          errorMessage = `Erro ${statusCode} no servidor`;
      }
      
      // Tentar extrair detalhes do erro
      try {
        errorDetails = error.response.data;
      } catch (e) {
        console.error('Não foi possível extrair detalhes do erro:', e);
      }
      
    } else if (error.request) {
      // A requisição foi feita mas não houve resposta
      errorMessage = 'Sem resposta do servidor. Verifique sua conexão.';
      statusCode = 0;
    }
    
    // Log detalhado do erro
    console.error(`[API Error] ${statusCode}: ${errorMessage}`, errorDetails || error);
    
    // Criar um erro enriquecido com informações úteis
    const enhancedError = {
      ...error,
      statusCode,
      message: errorMessage,
      details: errorDetails,
      timestamp: new Date().toISOString()
    };
    
    // Você pode adicionar lógica adicional aqui, como notificações globais
    // ou redirecionamento em caso de erros específicos
    
    return Promise.reject(enhancedError);
  }
);

export default axios;
"""

        # Criar o arquivo de interceptores
        with open(interceptors_path, 'w', encoding='utf-8') as f:
            f.write(interceptors_content)
            
        logger.info(f"Criado arquivo de interceptores: {interceptors_path}")
        
        # Atualizar o main.js para importar os interceptores
        main_js_path = SRC_DIR / "main.js"
        
        if main_js_path.exists():
            with open(main_js_path, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                
            # Verificar se já tem a importação
            if "import './interceptors'" not in conteudo:
                # Adicionar importação
                padrao_ultima_importacao = re.compile(r"(import\s+.*?['\"]\s*;?\s*)\n")
                correspondencias = list(padrao_ultima_importacao.finditer(conteudo))
                
                if correspondencias:
                    ultima_importacao = correspondencias[-1]
                    pos = ultima_importacao.end()
                    conteudo = conteudo[:pos] + "\n// Importar interceptores globais para Axios\nimport './interceptors';\n" + conteudo[pos:]
                else:
                    # Adicionar no início do arquivo
                    conteudo = "// Importar interceptores globais para Axios\nimport './interceptors';\n\n" + conteudo
                    
                # Salvar alterações
                with open(main_js_path, 'w', encoding='utf-8') as f:
                    f.write(conteudo)
                    
                logger.info(f"Atualizado {main_js_path} para importar interceptores")
                
        self.correcoes.append({
            "tipo": "axios",
            "arquivo": str(interceptors_path),
            "mensagem": "Criado arquivo de interceptores Axios para tratamento global de erros"
        })
    
    def atualizar_configuracao_axios(self):
        """Atualiza a configuração do Axios para incluir timeout"""
        self.fazer_backup_arquivos()
        
        axios_path = SRC_DIR / "api" / "axios.js"
        
        if not axios_path.exists():
            logger.warning(f"Arquivo não encontrado: {axios_path}")
            return
            
        with open(axios_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            
        # Verificar se já tem configuração de timeout
        if "timeout:" not in conteudo:
            # Procurar padrão de criação de instância Axios
            padrao_axios_create = re.compile(r"axios\.create\s*\(\s*\{")
            padrao_baseURL = re.compile(r"baseURL\s*:\s*['\"][^'\"]*['\"]")
            
            if padrao_axios_create.search(conteudo):
                # Adicionar timeout à configuração existente
                conteudo = re.sub(
                    r"axios\.create\s*\(\s*\{",
                    "axios.create({\n  timeout: 30000, // 30 segundos",
                    conteudo
                )
                logger.info("Adicionado timeout à configuração do Axios")
            elif padrao_baseURL.search(conteudo):
                # Adicionar timeout à baseURL existente
                conteudo = re.sub(
                    r"(baseURL\s*:\s*['\"][^'\"]*['\"])",
                    r"\1,\n  timeout: 30000, // 30 segundos",
                    conteudo
                )
                logger.info("Adicionado timeout à configuração existente do Axios")
            else:
                # Não encontrou padrão conhecido, adicionar timeout básico
                conteudo = re.sub(
                    r"import\s+axios\s+from\s+['\"](axios|.*)['\"]\s*;?",
                    r"import axios from 'axios';\n\n// Configurar timeout global\naxios.defaults.timeout = 30000; // 30 segundos\n",
                    conteudo
                )
                logger.info("Adicionado timeout global ao Axios")
                
            # Salvar alterações
            with open(axios_path, 'w', encoding='utf-8') as f:
                f.write(conteudo)
                
            self.correcoes.append({
                "tipo": "axios",
                "arquivo": str(axios_path),
                "mensagem": "Configuração de timeout adicionada ao Axios"
            })
    
    def executar_diagnostico(self):
        """Executa o diagnóstico completo do frontend"""
        logger.info("Iniciando diagnóstico do frontend...")
        
        # Verificar estrutura básica
        self.verificar_estrutura_frontend()
        
        # Verificar problemas específicos
        self.verificar_problemas_icones()
        self.verificar_problemas_axios()
        self.verificar_tratamento_erros_componentes()
        
        logger.info(f"Diagnóstico concluído. {len(self.problemas)} problemas encontrados.")
        return len(self.problemas) > 0
    
    def aplicar_correcoes(self):
        """Aplica correções para os problemas identificados"""
        logger.info("Aplicando correções automáticas...")
        
        # Backup antes de fazer alterações
        self.fazer_backup_arquivos()
        
        # Corrigir problemas de ícones
        self.corrigir_problemas_icones()
        
        # Criar/atualizar interceptores Axios
        if any(p["tipo"] == "axios" and "interceptores" in p["mensagem"].lower() for p in self.problemas):
            self.criar_interceptores_axios()
            
        # Atualizar configuração do Axios
        if any(p["tipo"] == "axios" and "timeout" in p["mensagem"].lower() for p in self.problemas):
            self.atualizar_configuracao_axios()
            
        logger.info(f"Correções aplicadas: {len(self.correcoes)}")
        return len(self.correcoes) > 0
    
    def gerar_relatorio(self):
        """Gera relatório de problemas e correções"""
        relatorio = {
            "timestamp": datetime.now().isoformat(),
            "problemas": self.problemas,
            "correcoes": self.correcoes,
            "resumo": {
                "total_problemas": len(self.problemas),
                "total_correcoes": len(self.correcoes),
                "problemas_por_tipo": {}
            }
        }
        
        # Contabilizar problemas por tipo
        for problema in self.problemas:
            tipo = problema["tipo"]
            if tipo not in relatorio["resumo"]["problemas_por_tipo"]:
                relatorio["resumo"]["problemas_por_tipo"][tipo] = 0
            relatorio["resumo"]["problemas_por_tipo"][tipo] += 1
            
        # Salvar relatório
        with open("diagnostico_frontend.json", "w", encoding="utf-8") as f:
            json.dump(relatorio, f, ensure_ascii=False, indent=2)
            
        logger.info("Relatório gerado: diagnostico_frontend.json")
        return relatorio
        
    def imprimir_resumo(self):
        """Imprime um resumo do diagnóstico e correções"""
        print("\n========== DIAGNÓSTICO DO FRONTEND ==========")
        print(f"Total de problemas encontrados: {len(self.problemas)}")
        
        if self.problemas:
            print("\nProblemas encontrados:")
            for i, problema in enumerate(self.problemas, 1):
                gravidade = problema.get("gravidade", "média").upper()
                mensagem = problema.get("mensagem", "")
                arquivo = problema.get("arquivo", "")
                solucao = problema.get("solucao", "")
                
                print(f"\n{i}. [{gravidade}] {mensagem}")
                if arquivo:
                    print(f"   Arquivo: {arquivo}")
                if solucao:
                    print(f"   Solução: {solucao}")
        
        print(f"\nTotal de correções aplicadas: {len(self.correcoes)}")
        
        if self.correcoes:
            print("\nCorreções aplicadas:")
            for i, correcao in enumerate(self.correcoes, 1):
                mensagem = correcao.get("mensagem", "")
                arquivo = correcao.get("arquivo", "")
                
                print(f"\n{i}. {mensagem}")
                if arquivo:
                    print(f"   Arquivo: {arquivo}")
                
        print("\nRelatório completo salvo em: diagnostico_frontend.json")
        
        if self.problemas and not self.correcoes:
            print("\nAVISO: Existem problemas não corrigidos automaticamente. Revise o relatório.")
        elif not self.problemas:
            print("\nSUCESSO: Nenhum problema encontrado no frontend!")
        else:
            print("\nINFO: Correções aplicadas, mas é recomendável verificar os resultados.")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Diagnóstico e correção do frontend")
    parser.add_argument('--apenas-diagnostico', action='store_true',
                      help="Executar apenas o diagnóstico sem aplicar correções")
    parser.add_argument('--relatorio', action='store_true',
                      help="Gerar apenas o relatório sem aplicar correções")
    args = parser.parse_args()
    
    try:
        # Verificar se o diretório frontend existe
        if not FRONTEND_DIR.exists():
            logger.error("Diretório frontend não encontrado. Este script deve ser executado no diretório raiz do projeto.")
            return 1
        
        # Criar e executar diagnóstico
        diagnostico = FrontendDiagnostico()
        
        # Executar diagnóstico
        tem_problemas = diagnostico.executar_diagnostico()
        
        # Aplicar correções se necessário e permitido
        if tem_problemas and not args.apenas_diagnostico and not args.relatorio:
            diagnostico.aplicar_correcoes()
            
        # Gerar relatório
        diagnostico.gerar_relatorio()
        
        # Imprimir resumo
        diagnostico.imprimir_resumo()
        
    except Exception as e:
        logger.error(f"Erro durante diagnóstico do frontend: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
