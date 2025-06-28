import json, os
import os.path
import glob
from datetime import datetime

try:
    import redis, sqlite3
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False

class ContextStorage:
    def __init__(self, backend="json", path="contexts", redis_url=None, sqlite_path=None):
        self.backend = backend
        self.path = path
        self.redis_url = redis_url
        self.sqlite_path = sqlite_path
        
        # Cria diretório de contextos
        os.makedirs(path, exist_ok=True)
        
        # Inicializa backends específicos
        if backend == "redis" and DEPENDENCIES_AVAILABLE:
            self.redis = redis.Redis.from_url(redis_url)
        if backend == "sqlite" and DEPENDENCIES_AVAILABLE:
            self.conn = sqlite3.connect(sqlite_path or "core_inteligente.db")
            self.conn.execute("CREATE TABLE IF NOT EXISTS context (session_id TEXT, content TEXT)")

    def salvar_contexto(self, session_id, contexto):
        if self.backend == "json":
            with open(f"{self.path}/{session_id}.json", "w", encoding="utf-8") as f:
                json.dump(contexto, f, indent=2, ensure_ascii=False)
        elif self.backend == "redis" and DEPENDENCIES_AVAILABLE:
            self.redis.set(session_id, json.dumps(contexto))
        elif self.backend == "sqlite" and DEPENDENCIES_AVAILABLE:
            self.conn.execute(
                "INSERT OR REPLACE INTO context VALUES (?, ?)",
                (session_id, json.dumps(contexto)),
            )
            self.conn.commit()

    def carregar_contexto(self, session_id):
        if self.backend == "json":
            try:
                with open(f"{self.path}/{session_id}.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except FileNotFoundError:
                return {"eventos": []}
            except json.JSONDecodeError:
                # Em caso de erro de parsing JSON, retorna um contexto vazio
                return {"eventos": [], "erro": "Erro ao carregar contexto"}
        elif self.backend == "redis" and DEPENDENCIES_AVAILABLE:
            data = self.redis.get(session_id)
            return json.loads(data) if data else {"eventos": []}
        elif self.backend == "sqlite" and DEPENDENCIES_AVAILABLE:
            cursor = self.conn.execute(
                "SELECT content FROM context WHERE session_id = ?", (session_id,)
            )
            row = cursor.fetchone()
            return json.loads(row[0]) if row else {"eventos": []}
        return {"eventos": []}  # Fallback seguro

    def contar_contextos(self):
        """
        Conta quantos contextos estão armazenados e retorna estatísticas.
        
        Returns:
            Dict com estatísticas sobre os contextos armazenados
        """
        try:
            if self.backend == "json":
                # Conta arquivos JSON no diretório de contextos
                arquivos = glob.glob(f"{self.path}/*.json")
                
                # Estatísticas básicas
                stats = {
                    "total": len(arquivos),
                    "ultimo_dia": 0,
                    "ultima_semana": 0,
                    "ultimo_mes": 0,
                }
                
                # Analisa timestamp dos arquivos para estatísticas temporais
                agora = datetime.now()
                for arquivo in arquivos:
                    try:
                        mtime = os.path.getmtime(arquivo)
                        data_mod = datetime.fromtimestamp(mtime)
                        delta_dias = (agora - data_mod).days
                        
                        if delta_dias <= 1:
                            stats["ultimo_dia"] += 1
                        if delta_dias <= 7:
                            stats["ultima_semana"] += 1
                        if delta_dias <= 30:
                            stats["ultimo_mes"] += 1
                    except:
                        pass
                
                return stats
                
            elif self.backend == "redis" and DEPENDENCIES_AVAILABLE:
                # No Redis, precisaríamos de um padrão para os contextos
                total = len(self.redis.keys("sess_*"))
                return {"total": total}
                
            elif self.backend == "sqlite" and DEPENDENCIES_AVAILABLE:
                cursor = self.conn.execute("SELECT COUNT(*) FROM context")
                total = cursor.fetchone()[0]
                return {"total": total}
                
            return {"total": "desconhecido", "backend": self.backend}
            
        except Exception as e:
            return {"erro": str(e), "total": "erro"}
