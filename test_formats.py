import asyncio
import aiohttp
import json
from core.config import settings

async def test_payload(payload, name):
    url = f"https://{settings.PLANFIX_ACCOUNT}.planfix.ru/rest/task"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {settings.PLANFIX_TOKEN}"
    }
    
    print(f"\n{'='*50}")
    print(f"Тест: {name}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            text = await response.text()
            print(f"Статус: {response.status}")
            print(f"Ответ: {text}")
            return response.status == 200

async def main():
    print(f"Аккаунт: {settings.PLANFIX_ACCOUNT}")
    print(f"URL: https://{settings.PLANFIX_ACCOUNT}.planfix.ru/rest/task")
    
    # Вариант 1: как в документации Planfix
    payload1 = {
        "title": "Тест 1",
        "description": "Описание задачи"
    }
    
    # Вариант 2: с оберткой request
    payload2 = {
        "request": {
            "task": {
                "title": "Тест 2",
                "description": "Описание задачи"
            }
        }
    }
    
    # Вариант 3: с task и полем general
    payload3 = {
        "task": {
            "general": 0,
            "title": "Тест 3",
            "description": "Описание задачи"
        }
    }
    
    # Вариант 4: через метод (как в XML)
    payload4 = {
        "method": "task.add",
        "account": settings.PLANFIX_ACCOUNT,
        "task": {
            "title": "Тест 4",
            "description": "Описание задачи"
        }
    }
    
    # Вариант 5: с дополнительным полем type
    payload5 = {
        "title": "Тест 5",
        "description": "Описание задачи",
        "type": 1
    }
    
    # Вариант 6: минимальный
    payload6 = {
        "title": "Тест 6"
    }
    
    tests = [
        (payload1, "Плоский объект"),
        (payload2, "С оберткой request"),
        (payload3, "С оберткой task и general"),
        (payload4, "С методом и аккаунтом"),
        (payload5, "С полем type"),
        (payload6, "Минимальный")
    ]
    
    for payload, name in tests:
        await test_payload(payload, name)
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())