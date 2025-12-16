import json
import threading
from datetime import datetime
from pathlib import Path
from collections import deque

STATE_FILE = Path("/home/ubuntu/oci-factory/state.json")
_LOCK = threading.Lock()

class FactoryState:
    def __init__(self):
        # Estado inicial padrão para 2 nós
        self.nodes = {
            "Instancia-1": {"status": "waiting", "desc": "1 OCPU / 6GB", "last_msg": "Aguardando..."},
            "Instancia-2": {"status": "waiting", "desc": "1 OCPU / 6GB", "last_msg": "Aguardando..."}
        }
        self.logs = [] # Lista simples para JSON
        self.last_update = datetime.utcnow().isoformat()
        
        # Tenta carregar estado anterior para não perder progresso
        loaded = self.load()
        if loaded:
            self.nodes = loaded.get("nodes", self.nodes)
            self.logs = loaded.get("logs", [])

    def add_log(self, message):
        """Adiciona log com timestamp e mantém apenas os últimos 50"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        with _LOCK:
            self.logs.insert(0, log_entry) # Adiciona no topo
            if len(self.logs) > 50:
                self.logs.pop() # Remove antigo
            self._save()

    def update_node(self, node_name, status=None, last_msg=None):
        with _LOCK:
            if node_name in self.nodes:
                if status:
                    self.nodes[node_name]["status"] = status
                if last_msg:
                    self.nodes[node_name]["last_msg"] = last_msg
            
            self.last_update = datetime.utcnow().isoformat()
            self._save()

    def _save(self):
        # Grava no disco
        try:
            data = {
                "nodes": self.nodes,
                "logs": self.logs,
                "last_update": self.last_update
            }
            STATE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception:
            pass # Evita crash se disco estiver ocupado

    @staticmethod
    def load():
        if not STATE_FILE.exists():
            return None
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            return None