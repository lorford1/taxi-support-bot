import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json
from core.config import settings

async def get_planfix_tasks(days_back: int = 90):
    """
    Выгрузка задач (task) из Planfix за последние N дней
    """
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days_back)
    
    # Формируем XML запрос для получения задач
    xml_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<request method="task.getList">
    <account>{settings.PLANFIX_ACCOUNT}</account>
    <filters>
        <filter>
            <type>12</type>  <!-- Дата создания -->
            <operator>gtAndEqual</operator>
            <value>
                <dateType>otherDate</dateType>
                <dateFrom>{from_date.strftime("%Y-%m-%d")}</dateFrom>
            </value>
        </filter>
    </filters>
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
            print(f"📄 Ответ API (первые 500 символов):\n{text[:500]}")
            
            root = ET.fromstring(text)
            
            tasks = []
            for task in root.findall('.//task'):
                title = task.findtext('title', '')
                description = task.findtext('description', '')
                
                if title or description:
                    tasks.append({
                        'title': title,
                        'description': description,
                        'date': task.findtext('createDateTime', ''),
                        'status': task.findtext('status/name', '')
                    })
            
            return tasks

async def main():
    print("📤 Выгружаем задачи из Planfix за последние 3 месяца...")
    tasks = await get_planfix_tasks(90)
    print(f"✅ Найдено {len(tasks)} задач")
    
    # Сохраняем в JSON
    with open('raw_tasks.json', 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    
    print("📁 Сохранено в raw_tasks.json")
    
    if tasks:
        print("\n📋 Первые 3 задачи:")
        for i, task in enumerate(tasks[:3]):
            print(f"{i+1}. {task.get('title', 'Без названия')[:100]}")

if __name__ == "__main__":
    asyncio.run(main())