try:
    import spacy
    nlp = spacy.load("pt_core_news_sm")
except ImportError:
    nlp = None

def analisar_intencao(mensagem):
    intents = []
    lower = mensagem.lower()
    if "erro" in lower or "exception" in lower:
        intents.append("erro")
    if "lento" in lower or "slow" in lower or "latência" in lower:
        intents.append("performance")
    if "relatório" in lower or "report" in lower:
        intents.append("relatorio")
    if nlp:
        doc = nlp(mensagem)
        for ent in doc.ents:
            if ent.label_ == "DATE":
                intents.append("tempo")
    return intents or ["geral"]
