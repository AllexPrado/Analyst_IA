"""
PlaybookEngine: playbooks dinâmicos configuráveis via YAML, com múltiplas ações.
Suporte a PT-BR e EN.
PlaybookEngine: dynamic playbooks via YAML, with multiple actions.
Supports PT-BR and EN.
"""

from typing import Dict, Any, List

try:
    import yaml
except ImportError:
    yaml = None

class PlaybookEngine:
    def __init__(self, playbook_path='playbooks.yaml'):
        self.playbook_path = playbook_path
        self.playbooks = self.load_playbooks()

    def load_playbooks(self) -> List[Dict]:
        """
        Carrega playbooks do arquivo YAML.
        Loads playbooks from YAML file.
        """
        if not yaml:
            return []
        try:
            with open(self.playbook_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or []
        except Exception as e:
            print(f"[PlaybookEngine] Erro ao carregar playbooks: {e}")
            return []

    def run_playbook(self, name: str, context: Dict[str, Any]) -> List[str]:
        """
        Executa um playbook pelo nome.
        Runs a playbook by name.
        """
        for pb in self.playbooks:
            if pb.get('name') == name:
                actions = pb.get('actions', [])
                return [f"Executando ação: {a.get('type')}" for a in actions]
        return ["Playbook não encontrado"]

    def exemplo_uso(self):
        """
        Exemplo de uso do PlaybookEngine.
        Example usage of PlaybookEngine.
        """
        return self.run_playbook('deploy', {'env': 'prod'})
