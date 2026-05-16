import sqlite3
import json
from typing import Optional, Dict, List
import os

DB_PATH = "users.db"

class Database:
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        """Создаёт таблицу пользователей, если её нет"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id TEXT PRIMARY KEY,
                driver_id TEXT NOT NULL,
                fullname TEXT NOT NULL,
                telegram_name TEXT,
                telegram_username TEXT,
                registered_at TEXT,
                updated_at TEXT
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ База данных инициализирована")
    
    def save_user(self, telegram_id: str, driver_id: str, fullname: str, **kwargs):
        """Сохраняет или обновляет пользователя"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (telegram_id, driver_id, fullname, telegram_name, telegram_username, registered_at, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        ''', (
            str(telegram_id),
            str(driver_id),
            fullname,
            kwargs.get('telegram_name', ''),
            kwargs.get('telegram_username', '')
        ))
        conn.commit()
        conn.close()
    
    def get_user(self, telegram_id: str) -> Optional[Dict]:
        """Получает пользователя по Telegram ID"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (str(telegram_id),))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_all_users(self) -> List[Dict]:
        """Получает всех пользователей"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY registered_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def is_registered(self, telegram_id: str) -> bool:
        """Проверяет, зарегистрирован ли пользователь"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE telegram_id = ?', (str(telegram_id),))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    def delete_user(self, telegram_id: str) -> bool:
        """Удаляет пользователя"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE telegram_id = ?', (str(telegram_id),))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

# Глобальный экземпляр
db = Database()