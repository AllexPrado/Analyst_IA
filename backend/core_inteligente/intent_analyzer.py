"""
IntentAnalyzer: análise semântica avançada para múltiplas intenções por mensagem.
Suporte a PT-BR e EN.
IntentAnalyzer: advanced semantic analysis for multiple intents per message.
Supports PT-BR and EN.
"""

from typing import List, Dict

try:
    import spacy
except ImportError:
    spacy = None

class IntentAnalyzer:
    def __init__(self, lang='pt'):
        self.lang = lang
        if spacy:
            if lang == 'pt':
                self.nlp = spacy.blank('pt')
            else:
                self.nlp = spacy.blank('en')
        else:
            self.nlp = None

    def analyze(self, text: str) -> List[Dict]:
        """
        Analisa o texto e retorna intenções detectadas.
        Analyze text and return detected intents.
        """
        intents = []
        txt = text.lower()
        # Regras simples, pode ser expandido para ML/NLP
        if any(w in txt for w in ['erro', 'falha', 'problema', 'error', 'fail']):
            intents.append({'intent': 'diagnose', 'confidence': 0.9})
        if any(w in txt for w in ['melhorar', 'otimizar', 'improve', 'optimize']):
            intents.append({'intent': 'suggest_improvement', 'confidence': 0.8})
        if any(w in txt for w in ['alerta', 'alert', 'notificar', 'notify']):
            intents.append({'intent': 'alert', 'confidence': 0.8})
        # Adicione mais regras conforme necessário
        return intents

    def exemplo_uso(self):
        """
        Exemplo de uso do IntentAnalyzer.
        Example usage of IntentAnalyzer.
        """
        return self.analyze("Erro crítico detectado. Precisa otimizar a API e notificar o time.")
