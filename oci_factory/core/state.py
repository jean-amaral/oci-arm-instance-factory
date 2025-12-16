import json
import threading
from datetime import datetime
from pathlib import Path

STATE_FILE = Path("/home/ubuntu/oci-factory/state.json")
_LOCK = threading.Lock()

class FactoryState:
    def __init__(self):
        # Estado inicial padrão
        self.status = "Iniciando"
        self.nodes = {
            "Instancia-1": {"status": "waiting", "desc": "1 OCPU / 6GB", "last_msg": "Aguardando..."},
            "Instancia-2": {"status": "waiting", "desc": "1 OCPU / 6GB", "last_msg": "Aguardando..."}
        }
        self.logs = []
        self.last_update = datetime.utcnow().isoformat() + "Z"
        
        # Carrega estado do disco
        loaded = self.load()
        if loaded:
            self.status = loaded.get("status", self.status)
            self.nodes = loaded.get("nodes", self.nodes)
            self.logs = loaded.get("logs", [])

            # === TRAVA DE SEGURANÇA (Autolimpeza) ===
            # Se o arquivo carregado tiver mais de 50 logs, corta o excesso agora.
            if len(self.logs) > 50:
                self.logs = self.logs[:50] # Mantém só os 50 primeiros (mais recentes)
                self._save() # Salva a versão limpa no disco imediatamente

    def add_log(self, message):
        """Adiciona log, limita tamanho e salva."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        with _LOCK:
            self.logs.insert(0, log_entry) # Adiciona no topo
            # Garante que nunca passe de 50 itens em memória
            if len(self.logs) > 50:
                self.logs.pop() 
            self._save()

    def update(self, status=None, last_message=None):
        """Atualização Global"""
        with _LOCK:
            if status:
                self.status = status
            if last_message:
                self.add_log(last_message)
            
            self.last_update = datetime.utcnow().isoformat() + "Z"
            self._save()

    def update_node(self, node_name, status=None, last_msg=None):
        """Atualização de Nó"""
        with _LOCK:
            if node_name in self.nodes:
                if status:
                    self.nodes[node_name]["status"] = status
                if last_msg:
                    self.nodes[node_name]["last_msg"] = last_msg
            
            self.last_update = datetime.utcnow().isoformat() + "Z"
            self._save()

    def _save(self):
        """
        Sobrescreve o arquivo JSON com o estado atual.
        Isso garante que o arquivo não cresça infinitamente (não é append).
        """
        try:
            data = {
                "status": self.status,
                "nodes": self.nodes,
                "logs": self.logs,
                "last_update": self.last_update
            }
            # write_text substitui todo o conteúdo do arquivo
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