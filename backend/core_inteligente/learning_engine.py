"""
LearningEngine: registro de feedbacks, aprendizado contínuo e sugestão de melhorias.
Suporte a PT-BR e EN.
LearningEngine: feedback registry, continuous learning and improvement suggestions.
Supports PT-BR and EN.
"""

from typing import List, Dict

class LearningEngine:
    def __init__(self):
        self.feedbacks = []

    def register_feedback(self, feedback: Dict):
        """
        Registra um feedback.
        Registers a feedback.
        """
        self.feedbacks.append(feedback)

    def suggest_improvements(self) -> List[str]:
        """
        Sugere melhorias com base nos feedbacks.
        Suggests improvements based on feedbacks.
        """
        suggestions = []
        for fb in self.feedbacks:
            if fb.get("type") == "negative":
                suggestions.append(f"Melhoria sugerida: {fb.get('suggestion')}")
        return suggestions

    def exemplo_uso(self):
        """
        Exemplo de uso do LearningEngine.
        Example usage of LearningEngine.
        """
        self.register_feedback({"type": "negative", "suggestion": "Melhorar logs"})
        return self.suggest_improvements()
