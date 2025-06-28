class AlertManager:
    def __init__(self, threshold=3):
        self.threshold = threshold

    def check_alert(self, eventos, tipo):
        relevantes = [e for e in eventos if e["tipo"] == tipo]
        return len(relevantes) >= self.threshold

    def deduplicate(self, alerts):
        return list(set(alerts))
