import json
import os
from typing import Optional, Dict, List

# Файл для хранения данных
USERS_FILE = "users_data.json"


class UserStorage:
    """Хранилище данных пользователей в JSON файле"""
    
    def __init__(self):
        self.users: Dict[str, dict] = {}
        self._load()
    
    def _load(self):
        """Загружает данные из файла"""
        if os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
                print(f"✅ Загружено {len(self.users)} пользователей из файла")
            except Exception as e:
                print(f"❌ Ошибка загрузки: {e}")
                self.users = {}
        else:
            print(f"📁 Файл {USERS_FILE} не найден, создаём новый")
            self._save()
    
    def _save(self):
        """Сохраняет данные в файл"""
        try:
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
            print(f"✅ Сохранено {len(self.users)} пользователей в файл")
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
    
    def get_user(self, telegram_id: str) -> Optional[dict]:
        """Получает пользователя по Telegram ID"""
        return self.users.get(str(telegram_id))
    
    def get_user_by_phone(self, phone: str) -> Optional[dict]:
        """Поиск пользователя по номеру телефона"""
        if not phone:
            return None
        # Очищаем номер от лишних символов для сравнения
        clean_phone = phone.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        for telegram_id, user in self.users.items():
            user_phone = user.get('telegram_phone', '')
            user_phone_clean = user_phone.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if user_phone_clean == clean_phone:
                return user
        return None
    
    def get_user_by_driver_id(self, driver_id: str) -> Optional[dict]:
        """Поиск пользователя по ID водителя"""
        for telegram_id, user in self.users.items():
            if str(user.get('driver_id', '')) == str(driver_id):
                return user
        return None
    
    def get_user_by_name(self, name: str) -> Optional[dict]:
        """Поиск пользователя по ФИО или имени"""
        name_lower = name.lower()
        for telegram_id, user in self.users.items():
            fullname = user.get('fullname', '').lower()
            if name_lower in fullname:
                return user
        return None
    
    def save_user(self, telegram_id: str, data: dict):
        """Сохраняет или обновляет пользователя"""
        telegram_id = str(telegram_id)
        if telegram_id in self.users:
            # Обновляем существующего пользователя
            old_data = self.users[telegram_id]
            old_data.update(data)
            self.users[telegram_id] = old_data
        else:
            self.users[telegram_id] = data
        self._save()
    
    def update_user(self, telegram_id: str, updates: dict) -> bool:
        """Обновляет данные пользователя"""
        telegram_id = str(telegram_id)
        if telegram_id in self.users:
            self.users[telegram_id].update(updates)
            self._save()
            return True
        return False
    
    def delete_user(self, telegram_id: str) -> bool:
        """Удаляет пользователя"""
        telegram_id = str(telegram_id)
        if telegram_id in self.users:
            del self.users[telegram_id]
            self._save()
            return True
        return False
    
    def is_registered(self, telegram_id: str) -> bool:
        """Проверяет, зарегистрирован ли пользователь"""
        return str(telegram_id) in self.users
    
    def get_all_users(self) -> List[dict]:
        """Возвращает всех пользователей"""
        return list(self.users.values())
    
    def get_registered_count(self) -> int:
        """Возвращает количество зарегистрированных пользователей"""
        return len(self.users)
    
    def get_users_by_category(self, category: str = None) -> List[dict]:
        """Возвращает пользователей по категории (если категория указана)"""
        if not category:
            return self.get_all_users()
        return [user for user in self.users.values() if user.get('category') == category]


# Глобальный экземпляр
user_storage = UserStorage()