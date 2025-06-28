import os
from dotenv import load_dotenv
load_dotenv()


def montar_analise_cruzada(entidade):
    nome = entidade.get("name") or entidade.get("nome", "Entidade desconhecida")
    try:
        metrica = entidade["metricas_nrql"]["30min"].get("response_time_max")
        if metrica and isinstance(metrica, list) and len(metrica) > 0:
            valor = metrica[0].get("value", metrica[0])
            return f"A entidade {nome} teve tempo de resposta máximo de {valor} ms nos últimos 30 minutos."
        return f"Sem dados de tempo de resposta máximo para {nome}."
    except Exception as e:
        return f"Não foi possível montar análise cruzada para {nome}. Erro: {e}"
