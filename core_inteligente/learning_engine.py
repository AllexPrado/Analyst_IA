class LearningEngine:
    def __init__(self, storage):
        self.storage = storage

    def registrar_feedback(self, session_id, evento, resultado):
        contexto = self.storage.carregar_contexto(session_id)
        contexto.setdefault("feedbacks", []).append({"evento": evento, "resultado": resultado})
        self.storage.salvar_contexto(session_id, contexto)
        
    def registrar_interacao(self, session_id, dados):
        """
        Registra uma interação para o sistema de aprendizado.
        Este método é chamado pelo learning_integration e garante compatibilidade.
        
        Args:
            session_id: Identificador da sessão
            dados: Dicionário com os dados da interação
        """
        # Usa o método existente para manter a consistência
        self.registrar_feedback(session_id, "interacao_chat", dados)
        return True

    def sugerir_melhoria(self, session_id):
        contexto = self.storage.carregar_contexto(session_id)
        feedbacks = contexto.get("feedbacks", [])
        if feedbacks and any("falha" in f["resultado"] for f in feedbacks):
            return "Revisar playbook para este evento."
        return "Fluxo estável."
        
    def obter_estatisticas(self):
        """
        Retorna estatísticas sobre o sistema de aprendizado.
        
        Returns:
            Dict com estatísticas de uso e aprendizado
        """
        try:
            # Esta é uma implementação básica que pode ser expandida
            return {
                "status": "ativo",
                "método_principal": "registrar_feedback",
                "métodos_disponíveis": ["registrar_feedback", "registrar_interacao", "sugerir_melhoria", "obter_estatisticas"],
                "storage_ativo": self.storage is not None,
                "contextos_armazenados": self.storage.contar_contextos() if hasattr(self.storage, 'contar_contextos') else "desconhecido"
            }
        except Exception as e:
            return {"status": "erro", "mensagem": str(e)}
