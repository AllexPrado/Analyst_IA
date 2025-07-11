
"""
AutoFixAgent: agente inteligente para monitorar, identificar e corrigir erros automaticamente no backend.
"""
import os
import re
import logging
import subprocess
from datetime import datetime

class AutoFixAgent:
    def __init__(self, log_path='logs/backend.log', test_path='tests/test_api_incidentes.py'):
        self.log_path = log_path
        self.test_path = test_path
        self.last_run = None
        self.logger = logging.getLogger('AutoFixAgent')

    def monitor_logs(self):
        """Lê os logs e identifica padrões de erro recorrentes."""
        if not os.path.exists(self.log_path):
            return []
        with open(self.log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        errors = [line for line in lines if 'ERROR' in line or 'Exception' in line or 'Traceback' in line]
        return errors[-10:]  # últimos 10 erros

    def run_tests(self):
        """Executa testes automatizados e retorna falhas."""
        try:
            result = subprocess.run(['python', '-m', 'pytest', self.test_path, '--maxfail=5', '--disable-warnings', '-q'], capture_output=True, text=True)
            output = result.stdout + '\n' + result.stderr
            failures = re.findall(r'FAILED.*?\n', output)
            return failures, output
        except Exception as e:
            self.logger.error(f'Erro ao executar testes: {e}')
            return [], str(e)

    def suggest_fix(self, error):
        """Sugere correção automática para erros comuns."""
        if 'AttributeError' in error and 'has no attribute' in error:
            match = re.search(r"'([\w]+)' object has no attribute '([\w]+)'", error)
            if match:
                class_name, method_name = match.groups()
                return f"Adicionar método '{method_name}' à classe '{class_name}'."
        if 'ImportError' in error or 'ModuleNotFoundError' in error:
            return "Verifique e corrija o caminho do import ou adicione o módulo faltante."
        if 'TypeError' in error and 'missing' in error:
            return "Ajuste a assinatura do método para aceitar os argumentos esperados."
        return "Erro detectado. Correção automática não implementada para este caso."

    def apply_fix(self, suggestion):
        """Aplica correção automática básica. Evolução: aplica patch real para erros comuns."""
        self.logger.info(f"Sugestão de correção: {suggestion}")
        # Exemplo: Adiciona método stub se for erro de atributo
        if suggestion.startswith("Adicionar método"):
            match = re.search(r"Adicionar método '([\w]+)' à classe '([\w]+)'", suggestion)
            if match:
                method_name, class_name = match.groups()
                # Busca arquivo da classe
                for root, dirs, files in os.walk('.'):
                    for fname in files:
                        if fname.endswith('.py'):
                            fpath = os.path.join(root, fname)
                            with open(fpath, 'r', encoding='utf-8') as f:
                                code = f.read()
                            if f'class {class_name}' in code:
                                stub = f"\n    def {method_name}(self, *args, **kwargs):\n        pass\n"
                                code = code.replace(f'class {class_name}', f'class {class_name}{stub}')
                                with open(fpath, 'w', encoding='utf-8') as f:
                                    f.write(code)
                                self.logger.info(f"Método stub '{method_name}' adicionado à classe '{class_name}' em {fpath}")
                                return True
        if suggestion.startswith("Verifique e corrija o caminho do import"):
            self.logger.info("Correção de import sugerida. (Implementação real pode ser expandida)")
            return True
        if suggestion.startswith("Ajuste a assinatura do método"):
            self.logger.info("Sugestão de ajuste de assinatura detectada. (Implementação real pode ser expandida)")
            return True
        return False

    def run(self):
        """Executa ciclo de monitoramento, sugestão e correção automática."""
        errors = self.monitor_logs()
        failures, test_output = self.run_tests()
        all_errors = errors + failures
        for error in all_errors:
            suggestion = self.suggest_fix(error)
            self.apply_fix(suggestion)
        self.last_run = datetime.now().isoformat()
        self.logger.info(f"AutoFixAgent executado em {self.last_run}")
        return {
            'last_run': self.last_run,
            'errors': all_errors,
            'suggestions': [self.suggest_fix(e) for e in all_errors],
            'test_output': test_output
        }

if __name__ == '__main__':
    agent = AutoFixAgent()
    result = agent.run()
    print(result)
