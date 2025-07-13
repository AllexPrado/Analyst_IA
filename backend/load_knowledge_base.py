"""
Script para carregar documentação de conhecimento nos agentes.
Este módulo prepara as bases de conhecimento para os agentes, permitindo
que eles tomem decisões informadas com base em documentação abrangente.
"""

import os
import json
import logging
import markdown
import re
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeLoader:
    """
    Carrega e processa documentação de conhecimento para os agentes.
    """
    
    def __init__(self, docs_dir="docs", output_dir="core_inteligente/knowledge_base"):
        """
        Inicializa o carregador de conhecimento.
        
        Args:
            docs_dir (str): Diretório contendo os arquivos de documentação
            output_dir (str): Diretório onde a base de conhecimento processada será salva
        """
        self.docs_dir = Path(docs_dir)
        self.output_dir = Path(output_dir)
        self.knowledge_base = {}
        
        # Criar diretório de saída se não existir
        os.makedirs(self.output_dir, exist_ok=True)
    
    def load_markdown_files(self):
        """
        Carrega todos os arquivos markdown do diretório de documentação.
        """
        logger.info(f"Carregando arquivos de documentação de {self.docs_dir}")
        
        for md_file in self.docs_dir.glob("*.md"):
            try:
                # Ler o conteúdo do arquivo
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Converter markdown para HTML para processamento
                html_content = markdown.markdown(content)
                
                # Extrair título do arquivo (nome do arquivo sem extensão)
                title = md_file.stem
                
                # Processar o conteúdo em seções
                sections = self._extract_sections(content)
                
                # Armazenar no dicionário de conhecimento
                self.knowledge_base[title] = {
                    "content": content,
                    "sections": sections
                }
                
                logger.info(f"Carregado: {title} com {len(sections)} seções")
                
            except Exception as e:
                logger.error(f"Erro ao carregar {md_file}: {str(e)}")
    
    def _extract_sections(self, content):
        """
        Extrai seções de um documento markdown.
        
        Args:
            content (str): Conteúdo do documento markdown
            
        Returns:
            dict: Dicionário de seções com seus conteúdos
        """
        sections = {}
        
        # Encontrar todos os cabeçalhos
        headers = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        
        if not headers:
            return {"main": content}
        
        # Processar cada cabeçalho e seu conteúdo
        for i in range(len(headers)):
            header_level, header_title = headers[i]
            
            # Determinar onde esta seção termina
            if i < len(headers) - 1:
                next_header = headers[i+1][0]
                if len(next_header) <= len(header_level):
                    # Próximo cabeçalho é do mesmo nível ou superior
                    section_end = content.find('\n' + next_header + ' ' + headers[i+1][1])
                else:
                    # Próximo cabeçalho é subordinado a este, continue até encontrar um do mesmo nível
                    j = i + 1
                    while j < len(headers) and len(headers[j][0]) > len(header_level):
                        j += 1
                    if j < len(headers):
                        section_end = content.find('\n' + headers[j][0] + ' ' + headers[j][1])
                    else:
                        section_end = len(content)
            else:
                # Último cabeçalho, vai até o fim do documento
                section_end = len(content)
            
            # Encontrar o início desta seção
            section_start = content.find(header_level + ' ' + header_title)
            section_start = content.find('\n', section_start) + 1
            
            # Extrair o conteúdo da seção
            section_content = content[section_start:section_end].strip()
            
            # Armazenar a seção
            section_key = header_title.lower().replace(' ', '_')
            sections[section_key] = section_content
        
        return sections
    
    def save_knowledge_base(self):
        """
        Salva a base de conhecimento processada em formato JSON.
        """
        logger.info(f"Salvando base de conhecimento em {self.output_dir}")
        
        # Salvar arquivo principal com toda a base de conhecimento
        main_file = self.output_dir / "knowledge_base.json"
        with open(main_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)
        
        # Salvar arquivos individuais para cada documento
        for title, content in self.knowledge_base.items():
            doc_file = self.output_dir / f"{title.lower()}.json"
            with open(doc_file, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Base de conhecimento salva com {len(self.knowledge_base)} documentos")
    
    def process(self):
        """
        Processa todos os arquivos de documentação e salva a base de conhecimento.
        """
        self.load_markdown_files()
        self.save_knowledge_base()
        return len(self.knowledge_base)

# Funções de indexação para busca rápida
def create_knowledge_index():
    """
    Cria um índice de busca para a base de conhecimento.
    """
    logger.info("Criando índice de busca para a base de conhecimento")
    
    # Implementação básica de um índice de busca
    # Em produção, considere usar ferramentas como Elasticsearch, 
    # FAISS para embeddings, ou pelo menos um índice invertido mais sofisticado
    
    knowledge_path = Path("core_inteligente/knowledge_base/knowledge_base.json")
    index_path = Path("core_inteligente/knowledge_base/search_index.json")
    
    if not knowledge_path.exists():
        logger.error(f"Arquivo base de conhecimento não encontrado: {knowledge_path}")
        return False
    
    try:
        with open(knowledge_path, 'r', encoding='utf-8') as f:
            knowledge_base = json.load(f)
        
        # Criar um índice invertido básico (palavra -> [documentos, seções])
        index = {}
        
        for doc_title, doc_content in knowledge_base.items():
            # Processar cada seção do documento
            for section_title, section_content in doc_content["sections"].items():
                # Tokenizar o conteúdo (simplificação - em produção use NLP adequado)
                words = re.findall(r'\b\w+\b', section_content.lower())
                
                # Adicionar ao índice
                for word in set(words):  # usar set para evitar duplicatas
                    if len(word) < 3:  # ignorar palavras muito curtas
                        continue
                        
                    if word not in index:
                        index[word] = []
                    
                    index[word].append({
                        "document": doc_title,
                        "section": section_title,
                        "frequency": words.count(word)  # contagem de frequência básica
                    })
        
        # Salvar o índice
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Índice criado com {len(index)} termos")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao criar índice: {str(e)}")
        return False

def integrate_with_agents():
    """
    Integra a base de conhecimento com os agentes.
    """
    logger.info("Integrando base de conhecimento com os agentes")
    
    # Caminho para o módulo dos agentes
    agent_module_path = Path("core_inteligente/agno_agent.py")
    
    if not agent_module_path.exists():
        logger.warning(f"Módulo de agente não encontrado: {agent_module_path}")
        return False
    
    try:
        # Ler o arquivo do módulo do agente
        with open(agent_module_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar se a integração já existe
        if "from core_inteligente.knowledge_base.knowledge_loader import KnowledgeBase" in content:
            logger.info("Integração com a base de conhecimento já existe")
            return True
        
        # Adicionar importação
        import_line = "\nfrom core_inteligente.knowledge_base.knowledge_loader import KnowledgeBase\n"
        
        # Encontrar classe do agente
        agent_class_match = re.search(r'class\s+AgnoAgent\s*\(', content)
        
        if agent_class_match:
            # Adicionar inicialização da base de conhecimento no __init__ do agente
            init_match = re.search(r'def\s+__init__\s*\([^)]*\):[^\n]*\n', content)
            if init_match:
                init_end = init_match.end()
                kb_init = "        self.knowledge_base = KnowledgeBase()\n"
                
                # Adicionar após a primeira linha do __init__
                content = content[:init_end] + kb_init + content[init_end:]
                
                # Adicionar importação no início do arquivo
                content = import_line + content
                
                # Salvar o arquivo modificado
                with open(agent_module_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info("Integração com a base de conhecimento realizada com sucesso")
                return True
            
        logger.warning("Não foi possível encontrar o local correto para integração")
        return False
        
    except Exception as e:
        logger.error(f"Erro ao integrar com agentes: {str(e)}")
        return False

# Criar classe KnowledgeBase para acesso fácil ao conhecimento
def create_knowledge_base_class():
    """
    Cria uma classe para facilitar o acesso à base de conhecimento.
    """
    kb_module_path = Path("core_inteligente/knowledge_base/knowledge_loader.py")
    os.makedirs(kb_module_path.parent, exist_ok=True)
    
    try:
        with open(kb_module_path, 'w', encoding='utf-8') as f:
            f.write('''"""
Módulo para carregamento e acesso à base de conhecimento.
"""

import json
import re
import os
from pathlib import Path

class KnowledgeBase:
    """
    Fornece acesso à base de conhecimento para os agentes.
    """
    
    def __init__(self, base_path="core_inteligente/knowledge_base"):
        """
        Inicializa a base de conhecimento.
        
        Args:
            base_path (str): Caminho para o diretório da base de conhecimento
        """
        self.base_path = Path(base_path)
        self.kb = {}
        self.index = {}
        self.load()
    
    def load(self):
        """
        Carrega a base de conhecimento e o índice de busca.
        """
        kb_path = self.base_path / "knowledge_base.json"
        index_path = self.base_path / "search_index.json"
        
        if kb_path.exists():
            with open(kb_path, 'r', encoding='utf-8') as f:
                self.kb = json.load(f)
                
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                self.index = json.load(f)
    
    def get_document(self, title):
        """
        Recupera um documento completo da base de conhecimento.
        
        Args:
            title (str): Título do documento
            
        Returns:
            dict: Documento ou None se não encontrado
        """
        return self.kb.get(title)
    
    def get_section(self, doc_title, section_title):
        """
        Recupera uma seção específica de um documento.
        
        Args:
            doc_title (str): Título do documento
            section_title (str): Título da seção
            
        Returns:
            str: Conteúdo da seção ou None se não encontrado
        """
        doc = self.get_document(doc_title)
        if doc and "sections" in doc:
            return doc["sections"].get(section_title)
        return None
    
    def search(self, query, limit=5):
        """
        Realiza uma busca na base de conhecimento.
        
        Args:
            query (str): Termos de busca
            limit (int): Número máximo de resultados
            
        Returns:
            list: Lista de resultados relevantes
        """
        # Tokenizar a consulta
        query_terms = set(re.findall(r'\\b\\w+\\b', query.lower()))
        
        # Calcular pontuações para documentos e seções
        scores = {}
        
        for term in query_terms:
            if term in self.index:
                for entry in self.index[term]:
                    doc_key = f"{entry['document']}:{entry['section']}"
                    if doc_key not in scores:
                        scores[doc_key] = 0
                    
                    scores[doc_key] += entry['frequency']
        
        # Ordenar resultados por pontuação
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Formatar resultados
        results = []
        for i, (doc_key, score) in enumerate(sorted_results):
            if i >= limit:
                break
                
            doc_title, section_title = doc_key.split(':')
            section_content = self.get_section(doc_title, section_title)
            
            results.append({
                "document": doc_title,
                "section": section_title,
                "content": section_content,
                "relevance": score
            })
        
        return results
    
    def get_topics(self):
        """
        Retorna todos os tópicos disponíveis na base de conhecimento.
        
        Returns:
            list: Lista de tópicos disponíveis
        """
        return list(self.kb.keys())
    
    def get_nrql_error_solution(self, error_message):
        """
        Busca uma solução para um erro NRQL específico.
        
        Args:
            error_message (str): Mensagem de erro NRQL
            
        Returns:
            dict: Solução encontrada ou None
        """
        # Extrair informações do erro
        position_match = re.search(r'position (\d+), unexpected \'([^\']+)\'', error_message)
        
        if position_match:
            position = int(position_match.group(1))
            unexpected_char = position_match.group(2)
            
            # Buscar especificamente em NRQL_ERROR_CORRECTION
            nrql_doc = self.get_document('NRQL_ERROR_CORRECTION')
            if nrql_doc:
                # Buscar em seções relevantes
                solutions = []
                
                for section_name, content in nrql_doc["sections"].items():
                    if "unexpected character" in section_name.lower():
                        solutions.append({
                            "section": section_name,
                            "content": content,
                            "relevance": 10  # Alta relevância para match direto
                        })
                    elif "syntax errors" in section_name.lower():
                        solutions.append({
                            "section": section_name,
                            "content": content,
                            "relevance": 5  # Relevância média para seção geral
                        })
                
                if solutions:
                    # Ordenar por relevância
                    solutions.sort(key=lambda x: x["relevance"], reverse=True)
                    return solutions[0]
        
        # Fallback: fazer uma busca geral
        return self.search("NRQL error " + error_message, limit=1)[0] if self.search("NRQL error " + error_message) else None
''')
        
        # Criar arquivo __init__.py para o pacote
        init_path = Path("core_inteligente/knowledge_base/__init__.py")
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write('"""Pacote para gerenciamento da base de conhecimento."""\n')
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao criar classe KnowledgeBase: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Iniciando carregamento da base de conhecimento")
    
    # Criar a classe de acesso à base de conhecimento
    if create_knowledge_base_class():
        logger.info("Classe KnowledgeBase criada com sucesso")
    
    # Carregar a documentação
    loader = KnowledgeLoader()
    num_docs = loader.process()
    logger.info(f"Processados {num_docs} documentos de conhecimento")
    
    # Criar índice de busca
    if create_knowledge_index():
        logger.info("Índice de busca criado com sucesso")
    
    # Integrar com os agentes
    if integrate_with_agents():
        logger.info("Base de conhecimento integrada com os agentes")
    
    logger.info("Processo concluído com sucesso!")
