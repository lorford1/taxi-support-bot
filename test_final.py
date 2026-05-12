import asyncio
import json
from core.config import settings
from core.planfix_client import planfix

async def test():
    print(f"Аккаунт: {settings.PLANFIX_ACCOUNT}")
    print(f"Токен: {settings.PLANFIX_TOKEN[:20]}...")
    print(f"Используется JSON-RPC формат Planfix")
    
    result = await planfix.create_task(
        title="Тест от бота (JSON-RPC)",
        description="Проверка правильного формата Planfix API",
        importance=1
    )
    
    if result.get("success"):
        print(f"\n✅ УСПЕХ! Задача создана!")
        print(f"   ID: {result.get('id')}")
        print(f"   Сквозной номер: {result.get('general')}")
        print(f"   Ссылка: {result.get('url')}")
    else:
        print(f"\n❌ Ошибка: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test())