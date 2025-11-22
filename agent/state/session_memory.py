# agent/state/memory.py
import json
from pathlib import Path
import logging

MEMORY_FILE = Path("memory_store.json")

class SessionMemory:
    def _load(self):
        if not MEMORY_FILE.exists() or MEMORY_FILE.stat().st_size == 0:
            # create an empty JSON file if it doesn’t exist or is empty
            MEMORY_FILE.write_text("{}")
            return {}
        try:
            return json.loads(MEMORY_FILE.read_text())
        except json.JSONDecodeError:
            # fallback if file gets corrupted
            MEMORY_FILE.write_text("{}")
            return {}


    def _save(self, data):
        MEMORY_FILE.write_text(json.dumps(data, indent=2))

    def set_context(self, session_id, key, value):
        data = self._load()
        session = data.get(session_id, {})
        session[key] = value
        data[session_id] = session
        self._save(data)
        logging.info(f"[MEMORY] Stored {key} for {session_id}")

    def get_context(self, session_id, key, default=None):
        return self._load().get(session_id, {}).get(key, default)

    def get_all(self, session_id):
        return self._load().get(session_id, {})

    def clear(self, session_id):
        data = self._load()
        data.pop(session_id, None)
        self._save(data)
        logging.info(f"[MEMORY] Cleared session {session_id}")

memory = SessionMemory()
