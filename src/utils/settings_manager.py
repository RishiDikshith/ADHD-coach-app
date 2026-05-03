import json
from pathlib import Path


class SettingsManager:
    """Manage user settings persistence"""
    
    DEFAULT_SETTINGS = {
        "theme": "dark",
        "language": "en",
        "notifications_enabled": True,
        "notification_frequency": "daily",
        "timer_duration": 25,
        "auto_check_in": True,
        "sound_enabled": True,
        "use_12h_format": False,
        "pin_hash": None
    }
    
    def __init__(self, username, settings_dir=".settings_data"):
        self.username = username
        self.settings_dir = Path(settings_dir)
        self.settings_dir.mkdir(exist_ok=True)
        self.settings_file = self.settings_dir / f"{username}_settings.json"
    
    def load_settings(self):
        """Load user settings with fallback to defaults"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    saved = json.load(f)
                # Merge with defaults (in case new settings were added)
                return {**self.DEFAULT_SETTINGS, **saved}
            except Exception as e:
                print(f"Error loading settings: {e}")
                return self.DEFAULT_SETTINGS.copy()
        return self.DEFAULT_SETTINGS.copy()
    
    def save_settings(self, settings):
        """Save user settings to disk"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def update_setting(self, key, value):
        """Update a single setting"""
        settings = self.load_settings()
        settings[key] = value
        return self.save_settings(settings)
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        return self.save_settings(self.DEFAULT_SETTINGS.copy())
