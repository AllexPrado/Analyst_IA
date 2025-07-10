
import requests
import time
import random

AGNO_URL = "http://localhost:8000/agno"

ENTIDADES = ["Api Sites", "Api Users", "Api Pagamentos"]

def corrigir_entidade(entidade):
    payload = {"entidade": entidade, "acao": "corrigir"}
    try:
        resp = requests.post(f"{AGNO_URL}/corrigir", json=payload)
        data = resp.json()
        print(f"Correção {entidade}:", data)
        # Aceita tanto dict quanto string no campo resultado
        resultado = data.get("resultado") if isinstance(data, dict) else None
        if isinstance(resultado, dict):
            return data
        elif isinstance(resultado, str):
            return {"resultado": {"mensagem": resultado}}
        else:
            return data
    except Exception as e:
        print(f"Erro ao corrigir {entidade}:", e)
        return None

def disparar_alerta(mensagem, destino="equipe"):
    payload = {"mensagem": mensagem, "destino": destino}
    try:
        resp = requests.post(f"{AGNO_URL}/alerta", json=payload)
        print("Alerta:", resp.json())
        return resp.json()
    except Exception as e:
        print("Erro ao disparar alerta:", e)
        return None

def registrar_historico(session_id, acao, detalhe):
    payload = {"feedback": {"mensagem": f"Agent-S: {acao} - {detalhe}", "score": 5}}
    try:
        resp = requests.post(f"{AGNO_URL}/feedback", json=payload)
        print("Histórico:", resp.json())
        return resp.json()
    except Exception as e:
        print("Erro ao registrar histórico:", e)
        return None

def coletar_metricas(entidade, periodo="7d"):
    payload = {"entidade": entidade, "periodo": periodo, "tipo": "metricas"}
    try:
        resp = requests.post(f"{AGNO_URL}/coletar_newrelic", json=payload)
        print(f"Métricas {entidade}:", resp.json())
        return resp.json()
    except Exception as e:
        print(f"Erro ao coletar métricas {entidade}:", e)
        return None

def executar_playbook(nome, contexto=None):
    payload = {"nome": nome}
    if contexto:
        payload["contexto"] = contexto
    try:
        resp = requests.post(f"{AGNO_URL}/playbook", json=payload)
        print(f"Playbook {nome}:", resp.json())
        return resp.json()
    except Exception as e:
        print(f"Erro ao executar playbook {nome}:", e)
        return None

def monitorar_e_automatizar():
    session_id = "agent_s_session"
    while True:
        print("Agent-S monitorando múltiplas entidades...")
        for entidade in ENTIDADES:
            # Simula detecção de falha aleatória
            if random.random() < 0.3:
                resultado = corrigir_entidade(entidade)
                status = None
                if resultado:
                    res = resultado.get("resultado")
                    if isinstance(res, dict):
                        status = res.get("status")
                    elif isinstance(res, str):
                        # Se for string, considera sucesso se não for erro conhecido
                        if "ok" in res.lower():
                            status = "ok"
                if status == "ok":
                    disparar_alerta(f"Agent-S executou correção automática em {entidade}")
                    registrar_historico(session_id, "correcao", f"Correção automática em {entidade}")
            # Coleta métricas periodicamente
            metricas = coletar_metricas(entidade)
            if metricas and metricas.get("dados"):
                registrar_historico(session_id, "coleta_metricas", f"Métricas coletadas de {entidade}")
            # Executa playbook inteligente para Api Sites
            if entidade == "Api Sites" and random.random() < 0.2:
                executar_playbook("relatorio_tecnico", {"entidade": entidade})
                registrar_historico(session_id, "playbook", f"Playbook relatorio_tecnico executado para {entidade}")
        time.sleep(60)

if __name__ == "__main__":
    monitorar_e_automatizar()
