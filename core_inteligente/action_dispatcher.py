def dispatch_action(acao, params=None):
    if "slack" in acao.lower():
        # Integração futura com Slack
        pass
    elif "webhook" in acao.lower():
        # Chamada webhook
        pass
    else:
        print(f"Ação genérica: {acao}")
