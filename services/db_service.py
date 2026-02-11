import json
import os
from datetime import datetime

class DBService:
    def __init__(self, file_path="db.json"):
        self.file_path = file_path
        self._init_db()

    def _init_db(self):
        needs_init = not os.path.exists(self.file_path) or os.stat(self.file_path).st_size == 0
        if needs_init:
            from services.auth_service import auth_svc
            schema = {
                "users": {
                    "admin": {"pw": auth_svc.hash_password("admin123"), "role": "admin"},
                    "user1": {"pw": auth_svc.hash_password("user123"), "role": "user"}
                },
                "history": [],
                "telemetry": {"total_api_calls": 0, "last_call_timestamp": None}
            }
            self._write_db(schema)

    def _read_db(self):
        with open(self.file_path, "r") as f:
            return json.load(f)

    def _write_db(self, data):
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=4)

    def get_data(self):
        return self._read_db()

    def log_generation(self, username: str, prompt: str, response: str):
        db = self._read_db()
        new_entry = {
            "user_id": username,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "prompt_preview": prompt[:40],
            "full_content": response
        }
        db["history"].insert(0, new_entry)
        db["history"] = db["history"][:50]
        db["telemetry"]["total_api_calls"] += 1
        db["telemetry"]["last_call_timestamp"] = new_entry["timestamp"]
        self._write_db(db)

    def get_user_history(self, username: str, role: str):
        db = self._read_db()
        if role == "admin": return db["history"]
        return [h for h in db["history"] if h["user_id"] == username]

db_svc = DBService()
