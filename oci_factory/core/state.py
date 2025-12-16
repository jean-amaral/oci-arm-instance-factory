import json
import threading
from datetime import datetime
from pathlib import Path

STATE_FILE = Path("/home/ubuntu/oci-factory/state.json")
_LOCK = threading.Lock()


class FactoryState:
    def __init__(self):
        self.status = "Parado"
        self.attempt = 0
        self.availability_domain = None
        self.last_message = None
        self.last_update = None
        self._save()

    def update(
        self,
        status=None,
        attempt=None,
        availability_domain=None,
        last_message=None,
    ):
        with _LOCK:
            if status is not None:
                self.status = status
            if attempt is not None:
                self.attempt = attempt
            if availability_domain is not None:
                self.availability_domain = availability_domain
            if last_message is not None:
                self.last_message = last_message

            self.last_update = datetime.utcnow().isoformat()
            self._save()

    def _save(self):
        STATE_FILE.write_text(
            json.dumps(
                {
                    "status": self.status,
                    "attempt": self.attempt,
                    "availability_domain": self.availability_domain,
                    "last_message": self.last_message,
                    "last_update": self.last_update,
                },
                indent=2,
                ensure_ascii=False,
            )
        )

    @staticmethod
    def load():
        if not STATE_FILE.exists():
            return None
        return json.loads(STATE_FILE.read_text())
