import json
import os

class SettingsService:
    def __init__(self, file_path="settings.json"):
        self.file_path = file_path
        self.defaults = {
            "system_persona": "Professional Marketing Expert",
            "default_voice": "Professional",
            "language": "English"
        }
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.file_path):
            self.save_settings(self.defaults)

    def get_settings(self):
        with open(self.file_path, "r") as f:
            return json.load(f)

    def save_settings(self, new_settings):
        with open(self.file_path, "w") as f:
            json.dump(new_settings, f, indent=4)

_settings_instance = None

def get_settings_service():
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = SettingsService()
    return _settings_instance