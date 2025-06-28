"""
Correlator: detecção de padrões, recorrências e picos temporais em eventos.
Suporte a PT-BR e EN.
Correlator: pattern, recurrence and peak detection in events.
Supports PT-BR and EN.
"""

from typing import List, Dict
from collections import Counter
import datetime

class Correlator:
    def detect_patterns(self, events: List[Dict]) -> Dict:
        """
        Detecta padrões de eventos recorrentes por tipo.
        Detects recurring event patterns by type.
        """
        type_counts = Counter(e['type'] for e in events if 'type' in e)
        most_common = type_counts.most_common(3)
        return {'most_common_types': most_common}

    def detect_peaks(self, events: List[Dict], window_minutes=60) -> List[Dict]:
        """
        Detecta picos de eventos por hora.
        Detects event peaks by hour.
        """
        buckets = {}
        for e in events:
            if 'timestamp' in e:
                try:
                    dt = datetime.datetime.fromisoformat(e['timestamp'])
                except Exception:
                    continue
                bucket = dt.replace(minute=0, second=0, microsecond=0)
                buckets.setdefault(bucket, 0)
                buckets[bucket] += 1
        peaks = [ {'time': str(k), 'count': v} for k, v in buckets.items() if v > 5 ]
        return peaks

    def exemplo_uso(self):
        """
        Exemplo de uso do Correlator.
        Example usage of Correlator.
        """
        return self.detect_patterns([
            {'type': 'error', 'timestamp': '2023-01-01T12:00:00'},
            {'type': 'error', 'timestamp': '2023-01-01T13:00:00'},
            {'type': 'warn', 'timestamp': '2023-01-01T14:00:00'}
        ])
