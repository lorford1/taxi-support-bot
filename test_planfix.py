import asyncio
from core.config import settings
from core.planfix_client import planfix

async def test():
    print(f"Аккаунт: {settings.PLANFIX_ACCOUNT}")
    print(f"API Key: {settings.PLANFIX_API_KEY[:10]}...")
    print(f"Private Key: {settings.PLANFIX_PRIVATE_KEY[:10]}...")
    print(f"URL: https://api.planfix.ru/xml/")
    
    result = await planfix.create_task(
        title="Тест Planfix от бота",
        description="Проверка подключения через XML API"
    )
    
    if result.get("success"):
        print(f"\n✅ Задача создана!")
        print(f"   ID: {result.get('id')}")
        print(f"   Сквозной номер: {result.get('general')}")
        print(f"   Ссылка: {result.get('url')}")
    else:
        print(f"\n❌ Ошибка: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test())