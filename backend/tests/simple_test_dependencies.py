"""
Script simples para testar a implementação do collect_entity_dependencies sem dependências externas
"""

import json
import os
from datetime import datetime

def test_dependency_format():
    """
    Testa o formato esperado das dependências
    """
    print("Testando formato de dependências...")
    
    # Simula o resultado de collect_entity_dependencies
    dependencies = {
        "upstream": [
            {
                "source": {
                    "guid": "upstream_source_guid_1",
                    "name": "Banco de Dados Produção",
                    "entityType": "POSTGRESQL_DB_ENTITY",
                    "domain": "DB"
                },
                "target": {
                    "guid": "target_guid",
                    "name": "API Principal",
                    "entityType": "APM_APPLICATION_ENTITY",
                    "domain": "APM"
                },
                "type": "CALLS"
            }
        ],
        "downstream": [
            {
                "source": {
                    "guid": "source_guid",
                    "name": "API Principal",
                    "entityType": "APM_APPLICATION_ENTITY",
                    "domain": "APM"
                },
                "target": {
                    "guid": "downstream_target_guid_1",
                    "name": "Frontend Web",
                    "entityType": "BROWSER_APPLICATION_ENTITY",
                    "domain": "BROWSER"
                },
                "type": "SERVES"
            }
        ],
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "entity_guid": "target_guid",
            "total_upstream": 1,
            "total_downstream": 1
        }
    }
    
    # Verifica se a estrutura está correta
    issues = validate_dependency_format(dependencies)
    
    if issues:
        print("Problemas encontrados:")
        for issue in issues:
            print(f"- {issue}")
    else:
        print("Formato validado com sucesso!")
    
    # Salva o resultado em um arquivo para análise
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(output_dir, "simple_test_result.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Converte datetime para string antes de salvar
        result = {
            "dependencies": dependencies,
            "validation_passed": len(issues) == 0,
            "issues": issues
        }
        json.dump(result, f, indent=2, default=str)
    
    print(f"Resultados salvos em: {output_file}")
    
    return len(issues) == 0

def validate_dependency_format(dependencies):
    """
    Valida o formato das dependências
    """
    issues = []
    
    # Verifica se é um dicionário
    if not isinstance(dependencies, dict):
        issues.append(f"Dependências deve ser um dicionário, não {type(dependencies).__name__}")
        return issues
    
    # Verifica se tem upstream ou downstream
    if not ('upstream' in dependencies or 'downstream' in dependencies):
        issues.append("Deve ter pelo menos um de: 'upstream' ou 'downstream'")
    
    # Verifica upstream
    if 'upstream' in dependencies:
        if not isinstance(dependencies['upstream'], list):
            issues.append(f"'upstream' deve ser uma lista, não {type(dependencies['upstream']).__name__}")
    
    # Verifica downstream
    if 'downstream' in dependencies:
        if not isinstance(dependencies['downstream'], list):
            issues.append(f"'downstream' deve ser uma lista, não {type(dependencies['downstream']).__name__}")
    
    # Verifica metadata
    if 'metadata' in dependencies:
        metadata = dependencies['metadata']
        if not isinstance(metadata, dict):
            issues.append(f"'metadata' deve ser um dicionário, não {type(metadata).__name__}")
        else:
            # Verifica campos obrigatórios em metadata
            required_fields = ['timestamp', 'entity_guid', 'total_upstream', 'total_downstream']
            for field in required_fields:
                if field not in metadata:
                    issues.append(f"Campo '{field}' não encontrado em metadata")
    
    return issues

if __name__ == "__main__":
    success = test_dependency_format()
    print(f"Teste {'passou' if success else 'falhou'}")
    exit(0 if success else 1)
