import yaml

def carregar_playbooks(path="playbooks.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)

def executar_playbook(tipo_evento, dados, playbooks):
    rules = playbooks.get(tipo_evento, [])
    acoes = []
    for rule in rules:
        acoes.append(rule["acao"])
    return acoes or ["Sem ação definida."]
