"""
Este script aplica permanentemente a correção para a função entidade_tem_dados
no módulo utils.newrelic_collector, tornando a validação menos restritiva para
reconhecer entidades com métricas que têm valores nulos.
"""

import os
import sys
import re

# Definição da nova função
new_function = '''
def entidade_tem_dados(metricas):
    """
    Verifica se uma entidade tem dados válidos nas métricas coletadas.
    Retorna True se a estrutura de métricas estiver correta, mesmo que os valores sejam nulos.
    
    Args:
        metricas: Dicionário com métricas coletadas do New Relic
    """
    if not metricas or not isinstance(metricas, dict):
        return False
        
    # Verifica cada período (30min, 24h, 7d, 30d)
    for periodo, periodo_data in metricas.items():
        if not isinstance(periodo_data, dict):
            continue
            
        # Se temos pelo menos uma métrica com estrutura correta, consideramos válida
        if periodo_data:
            return True
                
    return False
'''

def main():
    target_file = os.path.join('utils', 'newrelic_collector.py')
    
    # Verifica se o arquivo existe
    if not os.path.isfile(target_file):
        print(f"Erro: Arquivo {target_file} não encontrado.")
        return False
    
    # Lê o conteúdo do arquivo
    with open(target_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Procura e substitui a função original
    pattern = r'def entidade_tem_dados\(metricas\):.*?return False'
    if re.search(pattern, content, re.DOTALL):
        new_content = re.sub(pattern, new_function.strip(), content, flags=re.DOTALL)
        
        # Faz backup do arquivo original
        backup_file = f"{target_file}.bak"
        print(f"Criando backup em {backup_file}")
        with open(backup_file, 'w', encoding='utf-8') as file:
            file.write(content)
        
        # Escreve o novo conteúdo
        with open(target_file, 'w', encoding='utf-8') as file:
            file.write(new_content)
            
        print(f"Correção aplicada com sucesso em {target_file}")
        return True
    else:
        print("Função entidade_tem_dados não encontrada no arquivo.")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
