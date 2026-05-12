import asyncio
import aiohttp
from core.config import settings

async def debug_planfix():
    # 1. Проверяем переменные окружения
    print(f"--- Debug Info ---")
    print(f"Account name from .env: {settings.PLANFIX_ACCOUNT}")
    print(f"Token (first 10 chars): {settings.PLANFIX_TOKEN[:10]}...")
    
    # ВАЖНО: Укажите здесь URL, который соответствует вашему аккаунту.
    # Если аккаунт на planfix.ru, используйте этот адрес.
    API_URL = "https://api.planfix.ru/xml/"
    # Если аккаунт на planfix.com, используйте: "https://api.planfix.com/xml/"
    print(f"API URL being used: {API_URL}")

    # 2. Готовим XML-запрос. Это самый простой способ проверить права токена.
    # Метод user.get возвращает информацию о том пользователе, от чьего имени
    # вызывается API. Для этого не нужно специальных прав.
    xml_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<request method="user.get">
    <account>{settings.PLANFIX_ACCOUNT}</account>
</request>'''

    headers = {
        'Content-Type': 'application/xml',
        'Accept': 'application/xml'
    }

    print(f"\n--- Sending Request ---")
    print(xml_body)

    # 3. Правильная авторизация для XML API.
    # Ваш ТОКЕН используется как пароль. Логин для Basic Auth - это API Key.
    # В вашем случае, когда у вас только токен (и нет API Key), Planfix ожидает,
    # что API Key и Token - это одно и то же? Или вы неверно поняли руководителя?
    # Давайте попробуем оба варианта.
    
    # Попробуем вариант 1: В качествелогина используем сам токен,
    # а в качестве пароля оставляем 'x' (или пустую строку), как в старой документации. [citation:10]
    auth_basic = aiohttp.BasicAuth(settings.PLANFIX_TOKEN, 'x')
    print(f"Trying authentication with Login=Token, Password='x'")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, data=xml_body.encode('utf-8'),
                                    headers=headers, auth=auth_basic) as response:
                text = await response.text()
                print(f"\n--- Response (Status: {response.status}) ---")
                print(text)
                if response.status == 200 and "status=\"ok\"" in text:
                    print("\n✅ SUCCESS! Authentication and account works!")
                elif "code>0012" in text or "code>0001" in text:
                    print("\n❌ Authentication failed! Invalid token or wrong API endpoint.")
                else:
                    print("\n⚠️ Something else happened. Look at the response above.")

    except Exception as e:
        print(f"\n!!! Exception: {e}")

asyncio.run(debug_planfix())