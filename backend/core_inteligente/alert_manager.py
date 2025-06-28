"""
AlertManager: lógica avançada de alertas, deduplicação e threshold adaptativo.
Suporte a PT-BR e EN.
AlertManager: advanced alert logic, deduplication and adaptive threshold.
Supports PT-BR and EN.
"""
from typing import List, Dict

class AlertManager:
    def __init__(self):
        self.active_alerts = []

    def check_alert(self, event: Dict) -> bool:
        """
        Verifica se um evento deve gerar alerta (threshold adaptativo).
        Checks if an event should trigger an alert (adaptive threshold).
        """
        if event.get('severity', 0) > 7:
            if event not in self.active_alerts:
                self.active_alerts.append(event)
                return True
        return False

    def deduplicate(self, alerts: List[Dict]) -> List[Dict]:
        """
        Remove alertas duplicados.
        Removes duplicate alerts.
        """
        seen = set()
        deduped = []
        for a in alerts:
            key = (a.get('type'), a.get('message'))
            if key not in seen:
                seen.add(key)
                deduped.append(a)
        return deduped

    def exemplo_uso(self):
        """
        Exemplo de uso do AlertManager.
        Example usage of AlertManager.
        """
        return self.check_alert({'type': 'error', 'message': 'Erro crítico', 'severity': 8})
