import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json
from core.config import settings

async def get_actions_by_period(days_back: int = 90):
    """Получение всех действий (комментариев) из хроники Planfix за период"""
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days_back)
    
    from_date_str = from_date.strftime("%Y-%m-%d")
    to_date_str = to_date.strftime("%Y-%m-%d")
    
    all_actions = []
    page = 1
    page_size = 100
    
    while True:
        xml_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<request method="action.getListByPeriod">
    <account>{settings.PLANFIX_ACCOUNT}</account>
    <fromDate>{from_date_str}</fromDate>
    <toDate>{to_date_str}</toDate>
    <pageCurrent>{page}</pageCurrent>
    <pageSize>{page_size}</pageSize>
    <sort>asc</sort>
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
                
                if root.get('status') != 'ok':
                    print(f"Ошибка API: {root.findtext('code')}")
                    break
                
                actions_node = root.find('actions')
                if actions_node is None:
                    break
                
                total_count = int(actions_node.get('totalCount', 0))
                
                for action in actions_node.findall('action'):
                    description = action.findtext('description', '')
                    
                    # Оставляем только комментарии длиннее 5 символов
                    if description and len(description) > 5 and not action.findtext('fromEmail'):
                        all_actions.append({
                            'description': description,
                            'date': action.findtext('dateTime'),
                            'author': action.findtext('owner/name'),
                            'task_title': action.findtext('task/title', ''),
                            'task_id': action.findtext('task/id', '')
                        })
                
                print(f"Страница {page}: получено {len(actions_node.findall('action'))} записей, комментариев: {len(all_actions)}")
                
                if len(actions_node.findall('action')) < page_size:
                    break
                
                page += 1
                await asyncio.sleep(0.5)
    
    return all_actions

async def main():
    print("📤 Выгружаем хронику Planfix за последние 3 месяца...")
    print(f"Аккаунт: {settings.PLANFIX_ACCOUNT}")
    
    actions = await get_actions_by_period(90)
    
    print(f"\n✅ Найдено {len(actions)} комментариев")
    
    # Сохраняем в JSON
    with open('planfix_history.json', 'w', encoding='utf-8') as f:
        json.dump(actions, f, ensure_ascii=False, indent=2)
    
    print("📁 Сохранено в planfix_history.json")
    
    # Показываем примеры
    if actions:
        print("\n📋 Первые 5 сообщений:")
        for i, action in enumerate(actions[:5]):
            print(f"{i+1}. Задача: {action['task_title'][:50]}")
            print(f"   Сообщение: {action['description'][:100]}...")
            print(f"   Дата: {action['date']}")
            print(f"   Автор: {action['author']}")
            print()
    else:
        print("\n⚠️ Сообщений не найдено.")

if __name__ == "__main__":
    asyncio.run(main())