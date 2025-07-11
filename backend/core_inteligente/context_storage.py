import json, os
import redis, sqlite3
import datetime
from typing import Optional

class ContextStorage:
    def consultar_historico(self, session_id: str = None, limite: int = 10):
        """
        Consulta histórico de interações ou decisões da IA.
        Retorna os últimos N contextos salvos, opcionalmente filtrando por session_id.
        """
        historico = []
        if self.backend == "json":
            arquivos = [f for f in os.listdir(self.path) if f.endswith('.json')]
            # Se session_id for fornecido, filtra arquivos que começam com session_id
            if session_id:
                arquivos = [f for f in arquivos if f.startswith(f"{session_id}")]
            arquivos.sort(key=lambda x: os.path.getmtime(os.path.join(self.path, x)), reverse=True)
            for fname in arquivos:
                fpath = os.path.join(self.path, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        historico.append(json.load(f))
                except Exception:
                    continue
                if len(historico) >= limite:
                    break
            return historico
        elif self.backend == "sqlite" and hasattr(self, 'conn'):
            try:
                if session_id:
                    cur = self.conn.execute("SELECT content FROM context WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?", (session_id, limite))
                else:
                    cur = self.conn.execute("SELECT content FROM context ORDER BY timestamp DESC LIMIT ?", (limite,))
                rows = cur.fetchall()
                return [json.loads(row[0]) for row in rows]
            except Exception:
                return []
        elif self.backend == "redis" and hasattr(self, 'redis') and self.redis:
            # Redis: retorna apenas o contexto atual, não histórico
            if session_id:
                val = self.redis.get(session_id)
                try:
                    return [json.loads(val)] if val else []
                except Exception:
                    return []
            return []
        return historico
    """
    ContextStorage: armazenamento persistente e flexível para eventos/contexto/histórico.
    Suporta JSON local, Redis e SQLite. Limpeza automática de dados antigos.
    ContextStorage: persistent and flexible storage for events/context/history.
    Supports local JSON, Redis and SQLite. Automatic cleanup of old data.
    """
    def __init__(self, backend="json", path="contexts", redis_url=None, sqlite_path=None, retention_days=30, redis_expire=None):
        self.backend = backend
        self.path = path
        self.redis_url = redis_url
        self.sqlite_path = sqlite_path
        self.retention_days = retention_days
        self.redis_expire = redis_expire
        if backend == "redis":
            try:
                self.redis = redis.Redis.from_url(redis_url)
            except Exception as e:
                print(f"[ContextStorage][Redis] Erro ao conectar: {e}")
                self.redis = None
        if backend == "sqlite":
            try:
                self.conn = sqlite3.connect(sqlite_path or "core_inteligente.db")
                self.conn.execute("CREATE TABLE IF NOT EXISTS context (session_id TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
            except Exception as e:
                print(f"[ContextStorage][SQLite] Erro ao conectar: {e}")
        if backend == "json":
            os.makedirs(path, exist_ok=True)

    def salvar_contexto(self, session_id, contexto):
        """
        Salva o contexto para uma sessão.
        Save context for a session.
        """
        if self.backend == "json":
            file_path = os.path.join(self.path, f"{session_id}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(contexto, f, ensure_ascii=False, indent=2)
        elif self.backend == "redis" and self.redis:
            self.redis.set(session_id, json.dumps(contexto), ex=self.redis_expire)
        elif self.backend == "sqlite" and hasattr(self, 'conn'):
            self.conn.execute("INSERT INTO context (session_id, content) VALUES (?, ?)", (session_id, json.dumps(contexto)))
            self.conn.commit()

    def carregar_contexto(self, session_id) -> Optional[dict]:
        """
        Carrega o contexto de uma sessão.
        Load context for a session.
        """
        if self.backend == "json":
            file_path = os.path.join(self.path, f"{session_id}.json")
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None
        elif self.backend == "redis" and self.redis:
            val = self.redis.get(session_id)
            return json.loads(val) if val else None
        elif self.backend == "sqlite" and hasattr(self, 'conn'):
            cur = self.conn.execute("SELECT content FROM context WHERE session_id = ? ORDER BY timestamp DESC LIMIT 1", (session_id,))
            row = cur.fetchone()
            return json.loads(row[0]) if row else None
        return None

    def limpar_antigos(self):
        """
        Limpa contextos antigos baseado na retenção.
        Clean old contexts based on retention.
        """
        if self.backend == "json":
            now = datetime.datetime.now()
            for fname in os.listdir(self.path):
                fpath = os.path.join(self.path, fname)
                if os.path.isfile(fpath):
                    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fpath))
                    if (now - mtime).days > self.retention_days:
                        os.remove(fpath)
        elif self.backend == "sqlite" and hasattr(self, 'conn'):
            cutoff = datetime.datetime.now() - datetime.timedelta(days=self.retention_days)
            self.conn.execute("DELETE FROM context WHERE timestamp < ?", (cutoff.isoformat(),))
            self.conn.commit()
        elif self.backend == "redis" and self.redis:
            # Redis já expira automaticamente se configurado
            pass
