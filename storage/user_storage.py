from storage.database import db

class UserStorage:
    """Обёртка для совместимости со старым кодом"""
    
    def get_user(self, telegram_id: str):
        return db.get_user(telegram_id)
    
    def save_user(self, telegram_id: str, data: dict):
        db.save_user(
            telegram_id=telegram_id,
            driver_id=data.get('driver_id'),
            fullname=data.get('fullname'),
            telegram_name=data.get('telegram_name'),
            telegram_username=data.get('telegram_username')
        )
    
    def is_registered(self, telegram_id: str) -> bool:
        return db.is_registered(telegram_id)

user_storage = UserStorage()