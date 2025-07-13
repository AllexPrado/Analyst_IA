"""
Script para expandir as capacidades dos agentes Agent-S e Agno.
Este módulo adiciona novas funcionalidades aos agentes, incluindo capacidade
de correção de erros NRQL, validação de código, e outras melhorias.
"""

import os
import sys
import re
import json
import logging
import importlib
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentCapabilityExpander:
    """
    Adiciona novas capacidades aos agentes Agent-S e Agno.
    """
    
    def __init__(self, agent_module="core_inteligente.agno_agent"):
        """
        Inicializa o expansor de capacidades.
        
        Args:
            agent_module (str): Nome do módulo do agente
        """
        self.agent_module_name = agent_module
        self.agent_module_path = self._get_module_path(agent_module)
        self.agent_tools_path = self._get_module_path("core_inteligente.agent_tools")
        self.playbook_engine_path = self._get_module_path("core_inteligente.playbook_engine")
    
    def _get_module_path(self, module_name):
        """
        Obtém o caminho do arquivo para um módulo.
        
        Args:
            module_name (str): Nome do módulo
            
        Returns:
            Path: Caminho do arquivo do módulo
        """
        # Converter nome do módulo para caminho relativo
        module_path = module_name.replace(".", "/") + ".py"
        
        # Verificar se o arquivo existe
        if os.path.exists(module_path):
            return Path(module_path)
        
        # Tentar achar no sistema
        try:
            module = importlib.import_module(module_name)
            file_path = module.__file__
            return Path(file_path)
        except (ImportError, AttributeError):
            logger.warning(f"Não foi possível encontrar o caminho para o módulo {module_name}")
            
            # Último recurso: tentar adivinhar a localização
            guess_path = Path(f"d:/projetos/Analyst_IA/backend/{module_path}")
            if guess_path.exists():
                return guess_path
            
            return None
    
    def add_nrql_error_correction(self):
        """
        Adiciona capacidade de correção de erros NRQL.
        
        Returns:
            bool: True se bem-sucedido, False caso contrário
        """
        logger.info("Adicionando capacidade de correção de erros NRQL")
        
        if not self.agent_tools_path or not self.agent_tools_path.exists():
            logger.error(f"Arquivo de ferramentas do agente não encontrado: {self.agent_tools_path}")
            return False
        
        try:
            # Ler o conteúdo do arquivo
            with open(self.agent_tools_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar se a ferramenta já existe
            if "class NRQLCorrectionTool" in content:
                logger.info("Ferramenta de correção NRQL já existe")
                return True
            
            # Adicionar nova classe de ferramenta
            tool_code = '''

class NRQLCorrectionTool:
    """
    Ferramenta para corrigir erros em consultas NRQL.
    """
    
    def __init__(self):
        """
        Inicializa a ferramenta de correção NRQL.
        """
        try:
            from core_inteligente.knowledge_base.knowledge_loader import KnowledgeBase
            self.kb = KnowledgeBase()
        except ImportError:
            logger.warning("Base de conhecimento não disponível para correção NRQL")
            self.kb = None
    
    def extract_error_info(self, error_message):
        """
        Extrai informações detalhadas da mensagem de erro.
        
        Args:
            error_message (str): Mensagem de erro NRQL
            
        Returns:
            dict: Informações extraídas do erro
        """
        result = {
            "has_position": False,
            "position": None,
            "unexpected_char": None,
            "error_type": "unknown"
        }
        
        # Buscar erros de posição
        position_match = re.search(r'position (\d+), unexpected \'([^\']+)\'', error_message)
        if position_match:
            result["has_position"] = True
            result["position"] = int(position_match.group(1))
            result["unexpected_char"] = position_match.group(2)
            result["error_type"] = "position_error"
        
        # Buscar erros de atributo desconhecido
        attr_match = re.search(r'Unknown attribute \'([^\']+)\'', error_message)
        if attr_match:
            result["error_type"] = "unknown_attribute"
            result["attribute"] = attr_match.group(1)
        
        # Buscar erros de função
        func_match = re.search(r'Function \'([^\']+)\' requires', error_message)
        if func_match:
            result["error_type"] = "function_error"
            result["function"] = func_match.group(1)
        
        return result
    
    def correct_position_error(self, query, position, char):
        """
        Corrige erros baseados em posição específica.
        
        Args:
            query (str): Consulta NRQL com erro
            position (int): Posição do erro
            char (str): Caractere inesperado
            
        Returns:
            str: Consulta corrigida ou None
        """
        # Extrair contexto ao redor da posição do erro
        start = max(0, position - 10)
        end = min(len(query), position + 10)
        context = query[start:end]
        
        # Estratégias de correção baseadas no caractere e contexto
        
        # 1. Erros de vírgula em números
        if char in ',.' and re.search(r'\d[,\.]\d', context):
            # Se for vírgula em um número, remover a vírgula
            if ',' in context and any(c.isdigit() for c in context):
                return query[:position] + query[position+1:]  # Remover a vírgula
        
        # 2. Erros de aspas
        if char in '\'"' and context.count(char) % 2 == 1:
            # Aspas não fechadas, adicionar aspas
            return query[:position] + query[position+1:] + char
        
        # 3. Erros de caracteres especiais em identificadores
        if char in '-+*/&|%':
            # Verificar se está entre identificadores
            before = query[:position].rstrip()
            after = query[position+1:].lstrip()
            if before and after and before[-1].isalnum() and after[0].isalnum():
                # Colocar aspas ao redor do identificador
                identifier_start = position
                while identifier_start > 0 and query[identifier_start-1].isalnum():
                    identifier_start -= 1
                
                identifier_end = position
                while identifier_end < len(query) and query[identifier_end].isalnum():
                    identifier_end += 1
                
                identifier = query[identifier_start:identifier_end]
                return query[:identifier_start] + '"' + identifier + '"' + query[identifier_end:]
        
        # Se não conseguir corrigir automaticamente
        return None
    
    def correct_unknown_attribute(self, query, attribute):
        """
        Tenta corrigir atributos desconhecidos.
        
        Args:
            query (str): Consulta NRQL com erro
            attribute (str): Atributo desconhecido
            
        Returns:
            str: Consulta corrigida ou None
        """
        # Lista de atributos comuns por tipo
        common_attributes = {
            "Transaction": ["duration", "name", "appName", "errorMessage", "httpResponseCode"],
            "SystemSample": ["cpuPercent", "memoryUsedBytes", "diskUsedPercent"],
            "PageView": ["pageUrl", "duration", "userAgentName"]
        }
        
        # Encontrar o tipo de dados na consulta
        data_type_match = re.search(r'FROM\s+([A-Za-z0-9]+)', query)
        if not data_type_match:
            return None
            
        data_type = data_type_match.group(1)
        
        # Procurar correspondências próximas
        if data_type in common_attributes:
            import difflib
            matches = difflib.get_close_matches(attribute, common_attributes[data_type])
            
            if matches:
                closest = matches[0]
                return query.replace(attribute, closest)
        
        return None
    
    def run(self, query, error_message):
        """
        Corrige uma consulta NRQL com erro.
        
        Args:
            query (str): Consulta NRQL original
            error_message (str): Mensagem de erro
            
        Returns:
            dict: Resultado da correção
        """
        result = {
            "query_original": query,
            "error_message": error_message,
            "correction": None,
            "success": False,
            "explanation": "Não foi possível corrigir automaticamente."
        }
        
        # Extrair informações do erro
        error_info = self.extract_error_info(error_message)
        
        # Tentar correções específicas com base no tipo de erro
        if error_info["error_type"] == "position_error" and error_info["has_position"]:
            correction = self.correct_position_error(
                query, 
                error_info["position"], 
                error_info["unexpected_char"]
            )
            
            if correction:
                result["correction"] = correction
                result["success"] = True
                result["explanation"] = f"Corrigido erro na posição {error_info['position']} (caractere '{error_info['unexpected_char']}')."
                
        elif error_info["error_type"] == "unknown_attribute":
            correction = self.correct_unknown_attribute(query, error_info["attribute"])
            
            if correction:
                result["correction"] = correction
                result["success"] = True
                result["explanation"] = f"Corrigido atributo desconhecido '{error_info['attribute']}'."
        
        # Se a correção falhou mas temos base de conhecimento
        if not result["success"] and self.kb:
            # Procurar solução na base de conhecimento
            solution = self.kb.get_nrql_error_solution(error_message)
            
            if solution:
                result["knowledge_base_reference"] = solution
                result["explanation"] += f" Consulte a documentação sobre este tipo de erro."
        
        return result
'''

            # Adicionar a nova ferramenta ao final do arquivo
            content += tool_code
            
            # Salvar o arquivo modificado
            with open(self.agent_tools_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("Ferramenta de correção NRQL adicionada com sucesso")
            
            # Agora adicionar ao arquivo de agente
            return self._add_tool_to_agent("NRQLCorrectionTool")
        
        except Exception as e:
            logger.error(f"Erro ao adicionar capacidade de correção NRQL: {str(e)}")
            return False

    def add_code_validation(self):
        """
        Adiciona capacidade de validação de código.
        
        Returns:
            bool: True se bem-sucedido, False caso contrário
        """
        logger.info("Adicionando capacidade de validação de código")
        
        if not self.agent_tools_path or not self.agent_tools_path.exists():
            logger.error(f"Arquivo de ferramentas do agente não encontrado: {self.agent_tools_path}")
            return False
        
        try:
            # Ler o conteúdo do arquivo
            with open(self.agent_tools_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar se a ferramenta já existe
            if "class CodeValidationTool" in content:
                logger.info("Ferramenta de validação de código já existe")
                return True
            
            # Adicionar nova classe de ferramenta
            tool_code = '''

class CodeValidationTool:
    """
    Ferramenta para validação e análise de código.
    """
    
    def __init__(self):
        """
        Inicializa a ferramenta de validação de código.
        """
        self.linter_available = self._check_linter_available()
    
    def _check_linter_available(self):
        """
        Verifica se as ferramentas de lint estão disponíveis.
        
        Returns:
            bool: True se pelo menos uma ferramenta de lint estiver disponível
        """
        linters = {
            'pylint': False,
            'flake8': False,
            'eslint': False
        }
        
        try:
            import pylint
            linters['pylint'] = True
        except ImportError:
            pass
            
        try:
            import flake8
            linters['flake8'] = True
        except ImportError:
            pass
        
        # Verificar se eslint está instalado (via npm)
        try:
            import subprocess
            result = subprocess.run(["eslint", "--version"], 
                                   capture_output=True, 
                                   text=True, 
                                   shell=True)
            if result.returncode == 0:
                linters['eslint'] = True
        except:
            pass
        
        return any(linters.values())
    
    def detect_language(self, code):
        """
        Detecta a linguagem do código.
        
        Args:
            code (str): Código a ser analisado
            
        Returns:
            str: Linguagem detectada ('python', 'javascript', 'unknown')
        """
        # Detectar com base em características específicas
        
        # Python
        if re.search(r'import\s+[\w.]+|from\s+[\w.]+\s+import|def\s+\w+\s*\(\s*.*\s*\)\s*:', code):
            return 'python'
        
        # JavaScript
        if re.search(r'function\s+\w+\s*\(\s*.*\s*\)\s*{|const\s+|let\s+|var\s+|=>\s*{|\)\s*=>\s*', code):
            return 'javascript'
        
        # Mais linguagens podem ser adicionadas aqui
        
        # Fallback para tentar adivinhar com base em keywords
        python_keywords = ['def', 'class', 'import', 'from', 'with', 'as', 'try', 'except']
        js_keywords = ['function', 'const', 'let', 'var', 'async', 'await', 'export', 'import']
        
        python_score = sum(1 for kw in python_keywords if re.search(r'\\b' + kw + r'\\b', code))
        js_score = sum(1 for kw in js_keywords if re.search(r'\\b' + kw + r'\\b', code))
        
        if python_score > js_score:
            return 'python'
        elif js_score > python_score:
            return 'javascript'
        
        return 'unknown'
    
    def validate_python(self, code):
        """
        Valida código Python.
        
        Args:
            code (str): Código Python a ser validado
            
        Returns:
            dict: Resultados da validação
        """
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Verificação básica de sintaxe
        try:
            compile(code, '<string>', 'exec')
            result["valid"] = True
        except SyntaxError as e:
            result["errors"].append({
                "line": e.lineno,
                "col": e.offset,
                "message": str(e),
                "type": "syntax_error"
            })
            return result
        
        # Se disponível, usar pylint para análise mais profunda
        if self.linter_available:
            try:
                import tempfile
                import subprocess
                
                # Criar arquivo temporário
                with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False) as tmp:
                    tmp.write(code)
                    tmp_name = tmp.name
                
                try:
                    # Executar pylint
                    cmd = f"pylint {tmp_name} --output-format=json"
                    process = subprocess.run(cmd, 
                                           capture_output=True, 
                                           text=True, 
                                           shell=True)
                    
                    if process.returncode != 0:
                        lint_output = process.stdout
                        try:
                            issues = json.loads(lint_output)
                            for issue in issues:
                                if issue['type'] in ('error', 'fatal'):
                                    result["errors"].append({
                                        "line": issue.get('line', 0),
                                        "col": issue.get('column', 0),
                                        "message": issue.get('message', ''),
                                        "type": issue.get('symbol', 'unknown')
                                    })
                                elif issue['type'] == 'warning':
                                    result["warnings"].append({
                                        "line": issue.get('line', 0),
                                        "col": issue.get('column', 0),
                                        "message": issue.get('message', ''),
                                        "type": issue.get('symbol', 'unknown')
                                    })
                                else:
                                    result["suggestions"].append({
                                        "line": issue.get('line', 0),
                                        "col": issue.get('column', 0),
                                        "message": issue.get('message', ''),
                                        "type": issue.get('symbol', 'unknown')
                                    })
                        except json.JSONDecodeError:
                            # Fallback para output não-JSON
                            issues = process.stdout.split('\\n')
                            for issue in issues:
                                if issue.strip():
                                    if 'error' in issue.lower():
                                        result["errors"].append({
                                            "message": issue.strip(),
                                            "type": "lint_error"
                                        })
                                    elif 'warning' in issue.lower():
                                        result["warnings"].append({
                                            "message": issue.strip(),
                                            "type": "lint_warning"
                                        })
                finally:
                    # Remover arquivo temporário
                    os.unlink(tmp_name)
                    
            except Exception as e:
                result["errors"].append({
                    "message": f"Erro ao executar linter: {str(e)}",
                    "type": "linter_error"
                })
        
        # Verificar se o código é válido apesar dos warnings
        result["valid"] = len(result["errors"]) == 0
        
        return result
    
    def validate_javascript(self, code):
        """
        Valida código JavaScript.
        
        Args:
            code (str): Código JavaScript a ser validado
            
        Returns:
            dict: Resultados da validação
        """
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Verificação básica de sintaxe usando Node.js
        try:
            import tempfile
            import subprocess
            
            # Criar arquivo temporário
            with tempfile.NamedTemporaryFile(suffix='.js', mode='w', delete=False) as tmp:
                tmp.write(code)
                tmp_name = tmp.name
            
            try:
                # Usar node para verificar sintaxe
                cmd = f"node --check {tmp_name}"
                process = subprocess.run(cmd, 
                                       capture_output=True, 
                                       text=True, 
                                       shell=True)
                
                if process.returncode != 0:
                    for line in process.stderr.split('\\n'):
                        if line.strip():
                            result["errors"].append({
                                "message": line.strip(),
                                "type": "syntax_error"
                            })
                else:
                    result["valid"] = True
                    
                # Se eslint estiver disponível, usá-lo para análise mais profunda
                if self.linter_available:
                    cmd = f"eslint {tmp_name} -f json"
                    process = subprocess.run(cmd, 
                                           capture_output=True, 
                                           text=True, 
                                           shell=True)
                    
                    if process.stdout:
                        try:
                            issues = json.loads(process.stdout)
                            for file_issues in issues:
                                for msg in file_issues.get('messages', []):
                                    if msg.get('severity') == 2:  # error
                                        result["errors"].append({
                                            "line": msg.get('line', 0),
                                            "col": msg.get('column', 0),
                                            "message": msg.get('message', ''),
                                            "type": msg.get('ruleId', 'unknown')
                                        })
                                    elif msg.get('severity') == 1:  # warning
                                        result["warnings"].append({
                                            "line": msg.get('line', 0),
                                            "col": msg.get('column', 0),
                                            "message": msg.get('message', ''),
                                            "type": msg.get('ruleId', 'unknown')
                                        })
                        except json.JSONDecodeError:
                            pass  # Ignora erros de parse do JSON
            finally:
                # Remover arquivo temporário
                os.unlink(tmp_name)
                
        except Exception as e:
            result["errors"].append({
                "message": f"Erro ao validar JavaScript: {str(e)}",
                "type": "validation_error"
            })
        
        # Verificar se o código é válido apesar dos warnings
        result["valid"] = len(result["errors"]) == 0
        
        return result
    
    def suggest_improvements(self, code, language):
        """
        Sugere melhorias para o código.
        
        Args:
            code (str): Código a ser analisado
            language (str): Linguagem do código
            
        Returns:
            list: Lista de sugestões de melhoria
        """
        suggestions = []
        
        if language == 'python':
            # Verificar import não utilizados
            imports = re.findall(r'^import\s+([\w.]+)|^from\s+([\w.]+)\s+import', code, re.MULTILINE)
            all_imports = []
            for imp in imports:
                all_imports.extend([i for i in imp if i])
            
            for imp in all_imports:
                # Verificar se o import é usado no código
                if imp not in ['__future__', 'typing'] and not re.search(r'\\b' + re.escape(imp.split('.')[-1]) + r'\\b', code):
                    suggestions.append({
                        "type": "unused_import",
                        "message": f"O import '{imp}' parece não ser utilizado."
                    })
            
            # Verificar variáveis não utilizadas
            var_defs = re.findall(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=', code, re.MULTILINE)
            for var in var_defs:
                if var not in ['self', 'cls'] and code.count(var) <= 1:
                    suggestions.append({
                        "type": "unused_variable",
                        "message": f"A variável '{var}' parece ser definida mas não utilizada."
                    })
            
            # Verificar funções longas
            functions = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(.*\):', code, re.MULTILINE)
            for func in functions:
                # Encontrar o bloco da função
                func_pattern = r'def\s+' + re.escape(func) + r'\s*\(.*\):(.*?)(?=^(?:\s*def|class|\S)|$)'
                func_match = re.search(func_pattern, code, re.MULTILINE | re.DOTALL)
                if func_match:
                    func_body = func_match.group(1)
                    lines = func_body.count('\\n')
                    if lines > 30:
                        suggestions.append({
                            "type": "long_function",
                            "message": f"A função '{func}' tem {lines} linhas e pode ser muito longa. Considere refatorá-la."
                        })
        
        elif language == 'javascript':
            # Verificar import não utilizados
            imports = re.findall(r'import\s+{\s*([^}]+)\s*}|import\s+([a-zA-Z_$][a-zA-Z0-9_$]*)', code)
            all_imports = []
            for imp_group in imports:
                for imp in imp_group:
                    if imp:
                        if ',' in imp:
                            # Múltiplos imports separados por vírgula
                            for sub_imp in imp.split(','):
                                clean_imp = sub_imp.strip()
                                if clean_imp:
                                    all_imports.append(clean_imp)
                        else:
                            all_imports.append(imp.strip())
            
            for imp in all_imports:
                if not re.search(r'\\b' + re.escape(imp) + r'\\b', code):
                    suggestions.append({
                        "type": "unused_import",
                        "message": f"O import '{imp}' parece não ser utilizado."
                    })
            
            # Verificar variáveis não utilizadas
            var_defs = re.findall(r'(const|let|var)\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=', code)
            for _, var in var_defs:
                if code.count(var) <= 1:
                    suggestions.append({
                        "type": "unused_variable",
                        "message": f"A variável '{var}' parece ser definida mas não utilizada."
                    })
            
            # Verificar funções longas
            functions = re.findall(r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)|const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*function', code)
            all_functions = []
            for func_group in functions:
                for func in func_group:
                    if func:
                        all_functions.append(func)
            
            for func in all_functions:
                # Encontrar o bloco da função
                func_pattern = r'function\s+' + re.escape(func) + r'\s*\([^)]*\)\s*{(.*?)}'
                func_match = re.search(func_pattern, code, re.MULTILINE | re.DOTALL)
                if func_match:
                    func_body = func_match.group(1)
                    lines = func_body.count('\\n')
                    if lines > 30:
                        suggestions.append({
                            "type": "long_function",
                            "message": f"A função '{func}' tem {lines} linhas e pode ser muito longa. Considere refatorá-la."
                        })
        
        return suggestions
    
    def run(self, code):
        """
        Valida e analisa um código.
        
        Args:
            code (str): Código a ser validado
            
        Returns:
            dict: Resultado da validação e análise
        """
        result = {
            "language": "unknown",
            "valid": False,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Detectar linguagem
        language = self.detect_language(code)
        result["language"] = language
        
        # Validar de acordo com a linguagem
        if language == 'python':
            validation = self.validate_python(code)
            result.update(validation)
            
        elif language == 'javascript':
            validation = self.validate_javascript(code)
            result.update(validation)
        
        # Adicionar sugestões gerais de melhorias
        if result["valid"]:
            suggestions = self.suggest_improvements(code, language)
            result["suggestions"].extend(suggestions)
        
        return result
'''
            
            # Adicionar a nova ferramenta ao final do arquivo
            content += tool_code
            
            # Salvar o arquivo modificado
            with open(self.agent_tools_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("Ferramenta de validação de código adicionada com sucesso")
            
            # Agora adicionar ao arquivo de agente
            return self._add_tool_to_agent("CodeValidationTool")
        
        except Exception as e:
            logger.error(f"Erro ao adicionar capacidade de validação de código: {str(e)}")
            return False
    
    def add_playbook_nrql_correction(self):
        """
        Adiciona um playbook para correção de NRQL.
        
        Returns:
            bool: True se bem-sucedido, False caso contrário
        """
        logger.info("Adicionando playbook de correção NRQL")
        
        if not self.playbook_engine_path or not self.playbook_engine_path.exists():
            logger.error(f"Arquivo de motor de playbook não encontrado: {self.playbook_engine_path}")
            return False
        
        try:
            # Ler o arquivo do motor de playbook
            with open(self.playbook_engine_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar se já temos o playbook registrado
            if "corrigir_consulta_nrql" in content:
                logger.info("Playbook de correção NRQL já existe")
                return True
            
            # Localizar o dicionário de playbooks
            playbooks_match = re.search(r'self\.playbooks\s*=\s*{([^}]+)}', content, re.DOTALL)
            if not playbooks_match:
                logger.error("Não foi possível encontrar o dicionário de playbooks")
                return False
            
            # Obter o conteúdo atual do dicionário de playbooks
            playbooks_content = playbooks_match.group(1)
            
            # Criar novo playbook
            new_playbook = '''
            "corrigir_consulta_nrql": {
                "metadata": {
                    "name": "corrigir_consulta_nrql",
                    "description": "Corrige erros em consultas NRQL",
                    "version": "1.0.0",
                    "tags": ["nrql", "correção", "new relic"]
                },
                "inputs": {
                    "required": ["consulta", "mensagem_erro"]
                },
                "steps": [
                    {
                        "name": "parse_error",
                        "action": "analisar_erro_nrql",
                        "inputs": {
                            "mensagem": "{{inputs.mensagem_erro}}"
                        }
                    },
                    {
                        "name": "correct_query",
                        "action": "corrigir_consulta",
                        "inputs": {
                            "consulta": "{{inputs.consulta}}",
                            "mensagem_erro": "{{inputs.mensagem_erro}}"
                        }
                    },
                    {
                        "name": "validate_correction",
                        "action": "validar_consulta",
                        "inputs": {
                            "consulta_original": "{{inputs.consulta}}",
                            "consulta_corrigida": "{{steps.correct_query.output.correction}}"
                        },
                        "conditional": "{{steps.correct_query.success}}"
                    },
                    {
                        "name": "registrar_historico",
                        "action": "registrar_historico",
                        "inputs": {
                            "session_id": "{{inputs.session_id}}",
                            "contexto": {
                                "consulta_original": "{{inputs.consulta}}",
                                "erro": "{{inputs.mensagem_erro}}",
                                "consulta_corrigida": "{{steps.correct_query.output.correction}}",
                                "explicacao": "{{steps.correct_query.output.explanation}}"
                            }
                        }
                    }
                ],
                "outputs": {
                    "success": "{{steps.correct_query.success}}",
                    "consulta_original": "{{inputs.consulta}}",
                    "consulta_corrigida": "{{steps.correct_query.output.correction}}",
                    "explicacao": "{{steps.correct_query.output.explanation}}"
                }
            },'''
            
            # Inserir o novo playbook no dicionário
            updated_playbooks = playbooks_content + new_playbook
            
            # Atualizar o conteúdo do arquivo
            updated_content = content.replace(playbooks_content, updated_playbooks)
            
            # Salvar o arquivo atualizado
            with open(self.playbook_engine_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            # Adicionar ações de playbook
            return self._add_playbook_actions()
        
        except Exception as e:
            logger.error(f"Erro ao adicionar playbook de correção NRQL: {str(e)}")
            return False
    
    def _add_playbook_actions(self):
        """
        Adiciona ações necessárias para o playbook de correção NRQL.
        
        Returns:
            bool: True se bem-sucedido, False caso contrário
        """
        logger.info("Adicionando ações para o playbook de correção NRQL")
        
        if not self.playbook_engine_path or not self.playbook_engine_path.exists():
            logger.error(f"Arquivo de motor de playbook não encontrado: {self.playbook_engine_path}")
            return False
        
        try:
            # Ler o arquivo do motor de playbook
            with open(self.playbook_engine_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Localizar o bloco que manipula ações (tipo)
            action_block_match = re.search(r'if tipo == "([^"]+)":(.*?)elif tipo ==', content, re.DOTALL)
            if not action_block_match:
                logger.error("Não foi possível encontrar o bloco de manipulação de ações")
                return False
            
            # Verificar se as ações já existem
            if "analisar_erro_nrql" in content and "corrigir_consulta" in content:
                logger.info("Ações de correção NRQL já existem")
                return True
            
            # Obter o conteúdo atual do bloco de ação
            action_block_content = action_block_match.group(2)
            
            # Criar novas ações
            new_actions = '''
                    elif tipo == "analisar_erro_nrql":
                        from core_inteligente.agent_tools import NRQLCorrectionTool
                        tool = NRQLCorrectionTool()
                        error_info = tool.extract_error_info(context.get("mensagem", ""))
                        results.append(error_info)
                    elif tipo == "corrigir_consulta":
                        from core_inteligente.agent_tools import NRQLCorrectionTool
                        tool = NRQLCorrectionTool()
                        correction_result = tool.run(
                            context.get("consulta", ""),
                            context.get("mensagem_erro", "")
                        )
                        results.append(correction_result)
                    elif tipo == "validar_consulta":
                        # Validação simplificada: apenas verifica se a consulta corrigida é diferente da original
                        original = context.get("consulta_original", "")
                        corrected = context.get("consulta_corrigida", "")
                        is_valid = corrected and corrected != original
                        results.append({"valid": is_valid})'''
            
            # Adicionar novas ações ao conteúdo do bloco
            updated_action_block = action_block_content + new_actions
            
            # Atualizar o conteúdo do arquivo
            updated_content = content.replace(action_block_content, updated_action_block)
            
            # Salvar o arquivo atualizado
            with open(self.playbook_engine_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            logger.info("Ações de playbook adicionadas com sucesso")
            return True
        
        except Exception as e:
            logger.error(f"Erro ao adicionar ações de playbook: {str(e)}")
            return False
    
    def _add_tool_to_agent(self, tool_class):
        """
        Adiciona uma ferramenta ao agente.
        
        Args:
            tool_class (str): Nome da classe da ferramenta
            
        Returns:
            bool: True se bem-sucedido, False caso contrário
        """
        logger.info(f"Adicionando ferramenta {tool_class} ao agente")
        
        if not self.agent_module_path or not self.agent_module_path.exists():
            logger.error(f"Arquivo de módulo do agente não encontrado: {self.agent_module_path}")
            return False
        
        try:
            # Ler o arquivo do módulo do agente
            with open(self.agent_module_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verificar se a ferramenta já está registrada
            if f"self.{tool_class.lower()}" in content:
                logger.info(f"Ferramenta {tool_class} já registrada no agente")
                return True
            
            # Encontrar a classe AgnoAgent
            agent_class_match = re.search(r'class\s+AgnoAgent\s*\(', content)
            if not agent_class_match:
                logger.error("Não foi possível encontrar a classe AgnoAgent")
                return False
            
            # Encontrar o método __init__
            init_match = re.search(r'def\s+__init__\s*\([^)]*\):[^\n]*\n', content)
            if not init_match:
                logger.error("Não foi possível encontrar o método __init__ do agente")
                return False
            
            # Adicionar importação da ferramenta
            import_line = f"from core_inteligente.agent_tools import {tool_class}\n"
            if import_line not in content:
                # Encontrar a última importação
                last_import_match = re.search(r'^import|^from\s+\w+\s+import', content, re.MULTILINE)
                if last_import_match:
                    # Encontrar o fim do bloco de importação
                    last_import_end = content.find('\\n\\n', last_import_match.start())
                    if last_import_end == -1:
                        last_import_end = content.find('\\n', last_import_match.start())
                    
                    # Inserir nova importação após o bloco de importação
                    content = content[:last_import_end] + '\\n' + import_line + content[last_import_end:]
                else:
                    # Adicionar no início do arquivo
                    content = import_line + content
            
            # Adicionar inicialização da ferramenta no __init__
            init_end = init_match.end()
            tool_init = f"        self.{tool_class.lower()} = {tool_class}()\n"
            
            # Adicionar após a primeira linha do __init__
            content = content[:init_end] + tool_init + content[init_end:]
            
            # Salvar o arquivo modificado
            with open(self.agent_module_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Ferramenta {tool_class} adicionada com sucesso ao agente")
            return True
        
        except Exception as e:
            logger.error(f"Erro ao adicionar ferramenta ao agente: {str(e)}")
            return False
    
    def expand_all(self):
        """
        Expande todas as capacidades dos agentes.
        
        Returns:
            dict: Resultados da expansão
        """
        results = {
            "nrql_correction": self.add_nrql_error_correction(),
            "code_validation": self.add_code_validation(),
            "playbook_nrql": self.add_playbook_nrql_correction()
        }
        
        success = all(results.values())
        
        if success:
            logger.info("Expansão de capacidades concluída com sucesso!")
        else:
            logger.warning("Expansão de capacidades concluída com alguns problemas")
        
        return {
            "success": success,
            "results": results
        }

if __name__ == "__main__":
    logger.info("Iniciando expansão de capacidades dos agentes")
    
    # Carregar base de conhecimento primeiro
    try:
        import load_knowledge_base
        load_knowledge_base.main()
    except ImportError:
        logger.warning("Não foi possível carregar o módulo da base de conhecimento")
    
    # Expandir capacidades
    expander = AgentCapabilityExpander()
    results = expander.expand_all()
    
    # Exibir resultados
    logger.info(f"Resultado da expansão: {'SUCESSO' if results['success'] else 'FALHA PARCIAL'}")
    for capability, success in results["results"].items():
        logger.info(f"  - {capability}: {'✓' if success else '✗'}")
    
    logger.info("Processo de expansão de capacidades concluído")
