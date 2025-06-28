from collections import Counter
from datetime import datetime, timedelta

def correlacionar_eventos(eventos, novo_evento, janela_dias=7):
    similares = [
        ev for ev in eventos
        if ev["entidade"] == novo_evento["entidade"]
        and ev["tipo"] == novo_evento["tipo"]
        and abs((datetime.fromisoformat(ev["timestamp"]) - datetime.fromisoformat(novo_evento["timestamp"])).days) <= janela_dias
    ]
    if len(similares) >= 3:
        return "recorrente"
    return "novo"

def detectar_picos(eventos):
    datas = [e["timestamp"].split("T")[0] for e in eventos]
    contagem = Counter(datas)
    pico = max(contagem.values()) if contagem else 0
    return pico > 3
