import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json
from core.config import settings

async def get_all_actions(days_back: int = 90):
    """Выгружаем ВСЕ действия без фильтрации"""
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
                
                for action in actions_node.findall('action'):
                    # Сохраняем ВСЕ поля
                    action_data = {
                        'id': action.findtext('id'),
                        'type': action.findtext('type'),
                        'typeName': action.findtext('typeName'),
                        'dateTime': action.findtext('dateTime'),
                        'author': action.findtext('owner/name'),
                        'author_id': action.findtext('owner/id'),
                        'task_id': action.findtext('task/id'),
                        'task_title': action.findtext('task/title'),
                        'contact_name': action.findtext('contact/name'),
                        'description': action.findtext('description', ''),
                        'resultText': action.findtext('resultText', ''),
                        'data': action.findtext('data', ''),
                    }
                    all_actions.append(action_data)
                
                print(f"Страница {page}: получено {len(actions_node.findall('action'))} записей, всего собрано: {len(all_actions)}")
                
                if len(actions_node.findall('action')) < page_size:
                    break
                
                page += 1
                await asyncio.sleep(0.5)
    
    return all_actions

async def main():
    print("📤 Выгружаем ВСЮ хронику Planfix за последние 3 месяца...")
    print(f"Аккаунт: {settings.PLANFIX_ACCOUNT}")
    
    actions = await get_all_actions(90)
    
    print(f"\n✅ ВСЕГО выгружено: {len(actions)} записей")
    
    # Сохраняем всё в JSON
    with open('all_actions.json', 'w', encoding='utf-8') as f:
        json.dump(actions, f, ensure_ascii=False, indent=2)
    
    print("📁 Сохранено в all_actions.json")
    
    # Анализируем, где есть текст
    print("\n=== АНАЛИЗ ПОЛЕЙ С ТЕКСТОМ ===")
    
    fields_count = {
        'description': 0,
        'resultText': 0,
        'data': 0
    }
    
    for action in actions:
        if action.get('description') and len(action['description']) > 5:
            fields_count['description'] += 1
        if action.get('resultText') and len(action['resultText']) > 5:
            fields_count['resultText'] += 1
        if action.get('data') and len(action['data']) > 5:
            fields_count['data'] += 1
    
    print(f"Записей с description: {fields_count['description']}")
    print(f"Записей с resultText: {fields_count['resultText']}")
    print(f"Записей с data: {fields_count['data']}")
    
    # Показываем примеры записей с текстом
    print("\n=== ПРИМЕРЫ ЗАПИСЕЙ С ТЕКСТОМ ===")
    shown = 0
    for action in actions:
        text = action.get('description') or action.get('resultText') or action.get('data')
        if text and len(text) > 10 and shown < 10:
            print(f"\n--- Пример {shown+1} ---")
            print(f"Тип: {action.get('typeName')} (код: {action.get('type')})")
            print(f"Автор: {action.get('author')}")
            print(f"Текст: {text[:200]}...")
            print(f"Задача: {action.get('task_title')}")
            shown += 1
    
    if shown == 0:
        print("\n⚠️ НЕ НАЙДЕНО НИ ОДНОЙ ЗАПИСИ С ТЕКСТОМ!")
        print("Проверьте:")
        print("1. Есть ли комментарии в Planfix за последние 3 месяца?")
        print("2. Правильно ли настроены права API?")

if __name__ == "__main__":
    asyncio.run(main())