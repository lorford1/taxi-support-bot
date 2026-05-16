import json
import os

USERS_FILE = "users_data.json"

class UserStorage:
    def __init__(self):
        self.users = {}
        self._load()
    
    def _load(self):
        if os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            except:
                self.users = {}
    
    def _save(self):
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
    
    def get_user(self, telegram_id: str):
        return self.users.get(str(telegram_id))
    
    def save_user(self, telegram_id: str, data: dict):
        self.users[str(telegram_id)] = data
        self._save()
    
    def is_registered(self, telegram_id: str) -> bool:
        return str(telegram_id) in self.users

user_storage = UserStorage()