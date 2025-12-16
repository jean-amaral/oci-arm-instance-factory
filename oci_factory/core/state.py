import json
import threading
from datetime import datetime
from pathlib import Path

STATE_FILE = Path("/home/ubuntu/oci-factory/state.json")
_LOCK = threading.Lock()

class FactoryState:
    def __init__(self):
        # Estado inicial
        self.status = "Iniciando"
        self.nodes = {
            "Instancia-1": {"status": "waiting", "desc": "1 OCPU / 6GB", "last_msg": "Aguardando..."},
            "Instancia-2": {"status": "waiting", "desc": "1 OCPU / 6GB", "last_msg": "Aguardando..."}
        }
        self.logs = []
        # Adiciona o 'Z' para indicar UTC explicitamente
        self.last_update = datetime.utcnow().isoformat() + "Z"
        
        # Tenta carregar do disco
        loaded = self.load()
        if loaded:
            self.status = loaded.get("status", self.status)
            self.nodes = loaded.get("nodes", self.nodes)
            self.logs = loaded.get("logs", [])

    def add_log(self, message):
        """Adiciona log e salva estado"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        with _LOCK:
            self.logs.insert(0, log_entry)
            if len(self.logs) > 50:
                self.logs.pop()
            self._save()

    def update(self, status=None, last_message=None):
        """Atualização Global (usada pelo Runner)"""
        with _LOCK:
            if status:
                self.status = status
            if last_message:
                self.add_log(last_message)

            self.last_update = datetime.utcnow().isoformat() + "Z"
            self._save()

    def update_node(self, node_name, status=None, last_msg=None):
        """Atualização de Nó Específico"""
        with _LOCK:
            if node_name in self.nodes:
                if status:
                    self.nodes[node_name]["status"] = status
                if last_msg:
                    self.nodes[node_name]["last_msg"] = last_msg
            
            # Hora UTC com Z
            self.last_update = datetime.utcnow().isoformat() + "Z"
            self._save()

    def _save(self):
        try:
            data = {
                "status": self.status,
                "nodes": self.nodes,
                "logs": self.logs,
                "last_update": self.last_update
            }
            STATE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception:
            pass

    @staticmethod
    def load():
        if not STATE_FILE.exists():
            return None
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            return None