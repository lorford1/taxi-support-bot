import asyncio
import aiohttp
import json
from core.config import settings

async def test_rest():
    print(f"Аккаунт: {settings.PLANFIX_ACCOUNT}")
    print(f"Токен: {settings.PLANFIX_TOKEN[:20]}...")
    
    # Правильный URL для REST API
    url = f"https://{settings.PLANFIX_ACCOUNT}.planfix.ru/rest/task"
    print(f"URL: {url}")
    
    # Правильный формат JSON (плоский, без вложенных объектов)
    payload = {
        "title": "Тест от бота",
        "description": "Проверка REST API Planfix",
        "importance": 1
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {settings.PLANFIX_TOKEN}"
    }
    
    print(f"\nОтправляем запрос...")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            text = await response.text()
            print(f"\nСтатус: {response.status}")
            print(f"Ответ: {text}")
            
            if response.status == 200:
                print("\n✅ УСПЕХ! Задача создана!")
            else:
                print(f"\n❌ Ошибка: {response.status}")

if __name__ == "__main__":
    asyncio.run(test_rest())