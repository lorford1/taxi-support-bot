import asyncio
import aiohttp
import json
from core.config import settings

TOKEN = settings.PLANFIX_TOKEN
ACCOUNT = settings.PLANFIX_ACCOUNT
BASE_URL = f"https://{ACCOUNT}.planfix.ru/rest"

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}

async def test_payload(payload, name):
    print(f"\n{'='*50}")
    print(f"Тест {name}:")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/task",
            json=payload,
            headers=headers
        ) as response:
            text = await response.text()
            print(f"Статус: {response.status}")
            print(f"Ответ: {text[:200]}")
            return response.status == 200

async def main():
    print(f"Аккаунт: {ACCOUNT}")
    print(f"URL: {BASE_URL}/task")
    
    # Вариант 1: плоский объект
    payload1 = {
        "title": "Тест 1 - плоский объект",
        "description": "Проверка формата JSON",
        "importance": 1
    }
    
    # Вариант 2: с оберткой task (как мы пробовали)
    payload2 = {
        "task": {
            "title": "Тест 2 - с оберткой task",
            "description": "Проверка формата JSON",
            "importance": 1
        }
    }
    
    # Вариант 3: с полем general (как в документации Planfix)
    payload3 = {
        "task": {
            "general": 0,
            "title": "Тест 3 - с general",
            "description": "Проверка формата JSON"
        }
    }
    
    # Вариант 4: минимальный набор
    payload4 = {
        "title": "Тест 4 - минимальный"
    }
    
    # Вариант 5: с типом задачи
    payload5 = {
        "title": "Тест 5 - с типом",
        "description": "Проверка",
        "type": 1
    }
    
    results = []
    for i, payload in enumerate([payload1, payload2, payload3, payload4, payload5], 1):
        success = await test_payload(payload, f"Вариант {i}")
        results.append(success)
        await asyncio.sleep(1)  # пауза между запросами
    
    print(f"\n{'='*50}")
    print("Результаты:")
    for i, success in enumerate(results, 1):
        print(f"Вариант {i}: {'✅ Успех' if success else '❌ Ошибка'}")

if __name__ == "__main__":
    asyncio.run(main())