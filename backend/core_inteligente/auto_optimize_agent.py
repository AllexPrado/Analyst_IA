"""
AutoOptimizeAgent: agente inteligente para sugerir e aplicar otimizações automáticas no backend.
"""
import os
import re
import logging
from datetime import datetime

class AutoOptimizeAgent:
    def __init__(self, code_dir='.', log_path='logs/backend.log'):
        self.code_dir = code_dir
        self.log_path = log_path
        self.last_run = None
        self.logger = logging.getLogger('AutoOptimizeAgent')

    def scan_code(self):
        """Varre arquivos Python e identifica pontos de otimização."""
        optimizations = []
        for root, dirs, files in os.walk(self.code_dir):
            for file in files:
                if file.endswith('.py') and 'test' not in file:
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    # Detecta funções longas
                    long_funcs = re.findall(r'def (\w+)\(.*?\):(.{200,})', code, re.DOTALL)
                    for func in long_funcs:
                        optimizations.append(f"Função '{func[0]}' em '{file}' pode ser modularizada.")
                    # Detecta imports não usados
                    unused_imports = re.findall(r'import (\w+)', code)
                    for imp in unused_imports:
                        if imp not in code:
                            optimizations.append(f"Import '{imp}' em '{file}' pode ser removido.")
        return optimizations

    def monitor_logs(self):
        """Lê os logs e identifica lentidão ou gargalos."""
        if not os.path.exists(self.log_path):
            return []
        with open(self.log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        slow_lines = [line for line in lines if 'slow' in line or 'timeout' in line or 'performance' in line]
        return slow_lines[-10:]

    def suggest_optimization(self, issue):
        """Sugere otimização automática para pontos detectados."""
        if 'modularizada' in issue:
            return "Divida funções longas em funções menores e reutilizáveis."
        if 'removido' in issue:
            return "Remova imports não utilizados para reduzir consumo de memória e tempo de carregamento."
        if 'slow' in issue or 'timeout' in issue:
            return "Analise e otimize algoritmos ou use cache para acelerar respostas."
        return "Otimização sugerida. Expanda para automação real."

    def apply_optimization(self, suggestion):
        """Aplica otimização automática básica (stub, para evoluir depois)."""
        self.logger.info(f"Sugestão de otimização: {suggestion}")
        # Aqui pode ser expandido para aplicar patch real
        return True

    def run(self):
        """Executa ciclo de varredura, sugestão e otimização automática."""
        optimizations = self.scan_code()
        slow_logs = self.monitor_logs()
        all_issues = optimizations + slow_logs
        for issue in all_issues:
            suggestion = self.suggest_optimization(issue)
            self.apply_optimization(suggestion)
        self.last_run = datetime.now().isoformat()
        self.logger.info(f"AutoOptimizeAgent executado em {self.last_run}")
        return {
            'last_run': self.last_run,
            'issues': all_issues,
            'suggestions': [self.suggest_optimization(i) for i in all_issues]
        }

if __name__ == '__main__':
    agent = AutoOptimizeAgent(code_dir='core_inteligente')
    result = agent.run()
    print(result)
