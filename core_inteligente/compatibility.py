"""
Implementa métodos adicionais para o LearningEngine para
garantir compatibilidade com diferentes padrões de chamada.
"""

# Método original já presente na classe:
# def registrar_feedback(self, session_id, evento, resultado):
#     contexto = self.storage.carregar_contexto(session_id)
#     contexto.setdefault("feedbacks", []).append({"evento": evento, "resultado": resultado})
#     self.storage.salvar_contexto(session_id, contexto)

def registrar_interacao(self, session_id, resultado):
    """
    Método alternativo de registro para compatibilidade com diferentes padrões de chamada.
    Este método é uma adaptação mais simples do registrar_feedback.
    
    Args:
        session_id: Identificador único da sessão
        resultado: Dados da interação a serem registrados
    """
    return self.registrar_feedback(session_id, "interacao", resultado)

# Adiciona o método como método da classe
if __name__ == "__main__":
    import sys
    import importlib
    
    # Tenta importar a classe LearningEngine
    try:
        from core_inteligente.learning_engine import LearningEngine
        
        # Verifica se o método já existe
        if not hasattr(LearningEngine, 'registrar_interacao'):
            # Adiciona o método à classe
            setattr(LearningEngine, 'registrar_interacao', registrar_interacao)
            print("Método registrar_interacao adicionado à classe LearningEngine")
        else:
            print("Método registrar_interacao já existe na classe LearningEngine")
    except Exception as e:
        print(f"Erro ao adicionar método: {e}")
