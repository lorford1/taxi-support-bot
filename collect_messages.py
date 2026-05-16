import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json
from core.config import settings

async def get_planfix_messages(days_back: int = 90):
    """
    Выгрузка сообщений водителей из Planfix за последние N дней
    """
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days_back)
    
    # Формируем XML запрос
    xml_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<request method="action.getListByPeriod">
    <account>{settings.PLANFIX_ACCOUNT}</account>
    <fromDate>{from_date.strftime("%Y-%m-%d")}</fromDate>
    <toDate>{to_date.strftime("%Y-%m-%d")}</toDate>
    <pageSize>500</pageSize>
</request>'''
    
    headers = {'Content-Type': 'application/xml', 'Accept': 'application/xml'}
    auth = aiohttp.BasicAuth(settings.PLANFIX_API_KEY, settings.PLANFIX_PRIVATE_KEY)
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.planfix.ru/xml/",
            data=xml_body.encode('utf-8'),
            headers=headers,
            auth=auth
        ) as response:
            text = await response.text()
            root = ET.fromstring(text)
            
            messages = []
            for action in root.findall('.//action'):
                # Извлекаем текст сообщения
                description = action.findtext('description', '')
                
                # Пропускаем пустые и служебные
                if not description or len(description) < 5:
                    continue
                
                messages.append({
                    'text': description,
                    'date': action.findtext('dateTime', ''),
                    'author': action.findtext('owner/name', 'Водитель'),
                    'task_id': action.findtext('task/id', '')
                })
            
            return messages

async def main():
    print("📤 Выгружаем сообщения из Planfix за последние 3 месяца...")
    messages = await get_planfix_messages(90)
    print(f"✅ Найдено {len(messages)} сообщений")
    
    # Сохраняем в JSON
    with open('raw_messages.json', 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)
    
    print("📁 Сохранено в raw_messages.json")
    print("\n📋 Первые 5 сообщений:")
    for i, msg in enumerate(messages[:5]):
        print(f"{i+1}. {msg['text'][:100]}...")

if __name__ == "__main__":
    asyncio.run(main())