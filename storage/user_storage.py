import json
import os
from typing import Dict, Optional

# Файл для хранения данных
USERS_FILE = "users_data.json"

class UserStorage:
    """Простое хранилище данных пользователей в JSON файле"""
    
    def __init__(self):
        self.users: Dict[str, dict] = {}
        self._load()
    
    def _load(self):
        """Загружает данные из файла"""
        if os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
            except:
                self.users = {}
    
    def _save(self):
        """Сохраняет данные в файл"""
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
    
    def get_user(self, telegram_id: str) -> Optional[dict]:
        """Получить данные пользователя по Telegram ID"""
        return self.users.get(str(telegram_id))
    
    def save_user(self, telegram_id: str, data: dict):
        """Сохранить данные пользователя"""
        self.users[str(telegram_id)] = data
        self._save()
    
    def is_registered(self, telegram_id: str) -> bool:
        """Проверить, зарегистрирован ли пользователь"""
        return str(telegram_id) in self.users

# Глобальный экземпляр
user_storage = UserStorage()