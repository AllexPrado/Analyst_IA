

import requests
import time
import random
from typing import Any, Optional

# Helper para parse seguro de respostas do backend
def safe_parse_response(resp: requests.Response) -> Optional[Any]:
    try:
        if resp is None:
            return {"erro": "conexao", "mensagem": "Resposta nula do backend"}
        if resp.status_code != 200:
            print(f"[Agent-S] Erro HTTP: {resp.status_code} - {resp.text}")
            return {"erro": "http", "status": resp.status_code, "mensagem": resp.text}
        # Tenta parsear JSON
        try:
            data = resp.json()
        except Exception as e:
            print(f"[Agent-S] Erro ao parsear JSON: {e} - Conteúdo: {resp.text}")
            return {"erro": "json", "mensagem": f"{e} - Conteúdo: {resp.text}"}
        # Se for string, tenta parsear como JSON novamente
        if isinstance(data, str):
            import json
            try:
                data2 = json.loads(data)
                return data2
            except Exception:
                return {"mensagem": data}
        return data
    except Exception as e:
        print(f"[Agent-S] Erro inesperado ao tratar resposta: {e}")
        return {"erro": "exception", "mensagem": str(e)}

AGNO_URL = "http://localhost:8000/agno"

ENTIDADES = ["Api Sites", "Api Users", "Api Pagamentos"]

def corrigir_entidade(entidade):
    payload = {"entidade": entidade, "acao": "corrigir"}
    try:
        resp = requests.post(f"{AGNO_URL}/corrigir", json=payload)
        data = safe_parse_response(resp)
        print(f"Correção {entidade}:", data)
        # Padroniza retorno para dict
        if not data:
            return {"resultado": None}
        # Se vier erro de schema (campo 'detail'), retorna como erro padronizado
        if isinstance(data, dict) and "detail" in data:
            return {"erro": "schema", "mensagem": data["detail"]}
        if isinstance(data, dict) and "erro" in data:
            return data
        resultado = data.get("resultado") if isinstance(data, dict) else None
        if isinstance(resultado, dict):
            return data
        elif isinstance(resultado, str):
            return {"resultado": {"mensagem": resultado}}
        else:
            return {"resultado": resultado}
    except Exception as e:
        print(f"Erro ao corrigir {entidade}:", e)
        return {"erro": "exception", "mensagem": str(e)}

def disparar_alerta(mensagem, destino="equipe"):
    payload = {"mensagem": mensagem, "destino": destino}
    try:
        resp = requests.post(f"{AGNO_URL}/alerta", json=payload)
        data = safe_parse_response(resp)
        print("Alerta:", data)
        if not data:
            return {"erro": "vazio", "mensagem": "Resposta vazia ao disparar alerta"}
        if isinstance(data, dict) and "erro" in data:
            return data
        return data
    except Exception as e:
        print("Erro ao disparar alerta:", e)
        return {"erro": "exception", "mensagem": str(e)}

def registrar_historico(session_id, acao, detalhe):
    payload = {"feedback": {"mensagem": f"Agent-S: {acao} - {detalhe}", "score": 5}}
    try:
        resp = requests.post(f"{AGNO_URL}/feedback", json=payload)
        data = safe_parse_response(resp)
        print("Histórico:", data)
        if not data:
            return {"erro": "vazio", "mensagem": "Resposta vazia ao registrar histórico"}
        if isinstance(data, dict) and "erro" in data:
            return data
        return data
    except Exception as e:
        print("Erro ao registrar histórico:", e)
        return {"erro": "exception", "mensagem": str(e)}

def coletar_metricas(entidade, periodo="7d"):
    payload = {"entidade": entidade, "periodo": periodo, "tipo": "metricas"}
    try:
        resp = requests.post(f"{AGNO_URL}/coletar_newrelic", json=payload)
        data = safe_parse_response(resp)
        print(f"Métricas {entidade}:", data)
        if not data:
            return {"erro": "vazio", "mensagem": "Resposta vazia ao coletar métricas"}
        if isinstance(data, dict) and "erro" in data:
            return data
        return data
    except Exception as e:
        print(f"Erro ao coletar métricas {entidade}:", e)
        return {"erro": "exception", "mensagem": str(e)}

def executar_playbook(nome, contexto=None):
    payload = {"nome": nome}
    if contexto:
        payload["contexto"] = contexto
    try:
        resp = requests.post(f"{AGNO_URL}/playbook", json=payload)
        data = safe_parse_response(resp)
        print(f"Playbook {nome}:", data)
        if not data:
            return {"erro": "vazio", "mensagem": "Resposta vazia ao executar playbook"}
        if isinstance(data, dict) and "erro" in data:
            return data
        return data
    except Exception as e:
        print(f"Erro ao executar playbook {nome}:", e)
        return {"erro": "exception", "mensagem": str(e)}

def monitorar_e_automatizar():
    session_id = "agent_s_session"
    while True:
        print("Agent-S monitorando múltiplas entidades...")
        for entidade in ENTIDADES:
            # Correção automática sempre que detectado problema
            resultado = corrigir_entidade(entidade)
            status = None
            if resultado:
                if "erro" in resultado:
                    print(f"[Agent-S] Erro na correção de {entidade}: {resultado.get('mensagem')}")
                else:
                    res = resultado.get("resultado")
                    if isinstance(res, dict):
                        status = res.get("status")
                        # Se houver sugestões de correção, execute playbook de sugestão
                        if "sugestoes" in res:
                            for sugestao in res["sugestoes"]:
                                print(f"[Agent-S] Executando sugestão de correção: {sugestao}")
                                playbook_result = executar_playbook(sugestao, {"entidade": entidade})
                                print(f"[Agent-S] Resultado playbook sugestão: {playbook_result}")
                                registrar_historico(session_id, "playbook_sugestao", f"Playbook sugestão '{sugestao}' executado para {entidade}")
                    elif isinstance(res, str):
                        if "ok" in res.lower():
                            status = "ok"
                    elif res is None:
                        status = None
                    # Se a resposta indicar ação desconhecida, tentar playbook de correção
                    if isinstance(res, dict) and res.get("mensagem", "").lower().startswith("ação desconhecida"):
                        print(f"[Agent-S] Tentando playbook de correção para {entidade}...")
                        playbook_result = executar_playbook("corrigir_entidade", {"entidade": entidade})
                        print(f"[Agent-S] Resultado playbook de correção: {playbook_result}")
                        registrar_historico(session_id, "playbook_correcao", f"Playbook de correção executado para {entidade}")
            if status == "ok":
                disparar_alerta(f"Agent-S executou correção automática em {entidade}")
                registrar_historico(session_id, "correcao", f"Correção automática em {entidade}")
            # Otimização automática
            otimizar_result = executar_playbook("otimizar_entidade", {"entidade": entidade})
            print(f"[Agent-S] Otimização {entidade}: {otimizar_result}")
            registrar_historico(session_id, "otimizacao", f"Otimização automática em {entidade}")
            # Diagnóstico automático
            diagnostico_result = executar_playbook("diagnostico_entidade", {"entidade": entidade})
            print(f"[Agent-S] Diagnóstico {entidade}: {diagnostico_result}")
            registrar_historico(session_id, "diagnostico", f"Diagnóstico automático em {entidade}")
            # Coleta métricas periodicamente
            metricas = coletar_metricas(entidade)
            if metricas:
                if "erro" in metricas:
                    print(f"[Agent-S] Erro ao coletar métricas de {entidade}: {metricas.get('mensagem')}")
                elif metricas.get("dados"):
                    registrar_historico(session_id, "coleta_metricas", f"Métricas coletadas de {entidade}")
            # Executa playbook inteligente para Api Sites
            if entidade == "Api Sites":
                playbook_result = executar_playbook("relatorio_tecnico", {"entidade": entidade})
                if playbook_result and "erro" in playbook_result:
                    print(f"[Agent-S] Erro ao executar playbook: {playbook_result.get('mensagem')}")
                registrar_historico(session_id, "playbook", f"Playbook relatorio_tecnico executado para {entidade}")
        time.sleep(60)

if __name__ == "__main__":
    monitorar_e_automatizar()
