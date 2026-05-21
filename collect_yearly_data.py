import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import json
import re
from core.config import settings

async def collect_planfix_yearly():
    """Сбор чистых сообщений из Planfix за последний год (только диалоги водителей и поддержки)"""
    days_back = 365
    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    to_date = datetime.now().strftime("%Y-%m-%d")
    
    all_messages = []
    page = 1
    page_size = 100
    
    print(f"📤 Выгружаем чистые сообщения из Planfix за последние {days_back} дней")
    print(f"📅 Период: {from_date} — {to_date}")
    print("=" * 60)
    
    # Системные авторы для фильтрации
    system_authors = [
        'robot', 'bot', 'system', 'admin', 'support', 'service',
        'Брониш Максим', 'Николай', 'Стельмах Дмитрий'
    ]
    
    # Паттерны мусора
    trash_patterns = [
        r'\{log\d+\}',           # {log26}
        r'\{event\d+\}',         # {event1}
        r'\{\{log\d+\}\}',       # {{log29}}
        r'<[^>]+>',              # HTML теги
        r'event\d+\}',           # event1}
        r'class="[^"]+"',        # HTML классы
        r'&nbsp;',               # HTML entities
        r'&lt;', r'&gt;', r'&amp;',
        r'К работе над задачей подключен',
        r'Больше не являются исполнителями',
        r'К участникам задачи добавлены',
        r'Новая ->', r'Завершенная',
        r'Статус:', r'Исполнитель:',
        r'Создал заявку', r'Отправляю запрос',
        r'✅', r'❌', r'🔧', r'🚕', r'📝', r'🆔', r'👤',  # Эмодзи-мусор
    ]
    
    def is_clean_message(text: str, author: str, action_type: str) -> bool:
        """Проверяет, является ли сообщение чистым диалогом"""
        
        # Пропускаем слишком короткие
        if len(text) < 15:
            return False
        
        # Пропускаем системных авторов
        author_lower = author.lower()
        for sa in system_authors:
            if sa.lower() in author_lower:
                return False
        
        # Пропускаем системные типы действий
        if action_type in ['system', 'status', 'assign', 'notify']:
            return False
        
        # Пропускаем сообщения с мусорными паттернами
        for pattern in trash_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False
        
        # Пропускаем сообщения, начинающиеся со служебных фраз
        service_starts = [
            'создал заявку', 'отправляю запрос', 'обновил',
            'разблокировал', 'выставил лимит', 'назначил'
        ]
        text_lower = text.lower()
        for start in service_starts:
            if text_lower.startswith(start):
                return False
        
        # Пропускаем сообщения, которые выглядят как системные уведомления
        if text.startswith('Вы ') or text.startswith('вы '):
            return False
        if 'подключен' in text or 'отключен' in text:
            return False
        
        return True
    
    while True:
        xml_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<request method="action.getListByPeriod">
    <account>{settings.PLANFIX_ACCOUNT}</account>
    <fromDate>{from_date}</fromDate>
    <toDate>{to_date}</toDate>
    <pageCurrent>{page}</pageCurrent>
    <pageSize>{page_size}</pageSize>
    <sort>asc</sort>
</request>'''
        
        headers = {'Content-Type': 'application/xml', 'Accept': 'application/xml'}
        auth = aiohttp.BasicAuth(settings.PLANFIX_API_KEY, settings.PLANFIX_PRIVATE_KEY)
        
        try:
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
                        print(f"❌ Ошибка API: {root.findtext('code')}")
                        break
                    
                    actions_node = root.find('actions')
                    if actions_node is None:
                        break
                    
                    total_on_page = len(actions_node.findall('action'))
                    
                    for action in actions_node.findall('action'):
                        description = action.findtext('description', '')
                        author = action.findtext('owner/name', '')
                        date = action.findtext('dateTime', '')
                        task_title = action.findtext('task/title', '')
                        action_type = action.findtext('type', '')
                        
                        if is_clean_message(description, author, action_type):
                            # Очищаем текст от лишних пробелов
                            clean_text = ' '.join(description.split())
                            
                            all_messages.append({
                                'text': clean_text,
                                'author': author,
                                'date': date,
                                'task_title': task_title
                            })
                    
                    print(f"📄 Страница {page}: обработано {total_on_page} записей, очищено: {len(all_messages)}")
                    
                    if total_on_page < page_size:
                        break
                    
                    page += 1
                    await asyncio.sleep(0.3)  # небольшая задержка между запросами
                    
        except Exception as e:
            print(f"❌ Ошибка на странице {page}: {e}")
            break
    
    return all_messages

async def main():
    data = await collect_planfix_yearly()
    
    print("\n" + "=" * 60)
    print(f"✅ ВСЕГО СОБРАНО ЧИСТЫХ СООБЩЕНИЙ: {len(data)}")
    print("=" * 60)
    
    # Сохраняем в JSON
    with open('clean_yearly_messages.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("📁 Сохранено в clean_yearly_messages.json")
    
    # Статистика по месяцам
    months = {}
    for msg in data:
        month = msg['date'][:7] if msg['date'] else 'unknown'
        months[month] = months.get(month, 0) + 1
    
    print("\n📊 Сообщения по месяцам:")
    for month in sorted(months.keys())[-12:]:
        print(f"   {month}: {months[month]} сообщений")
    
    # Показываем примеры
    print("\n📋 Примеры чистых сообщений (первые 15):")
    for i, msg in enumerate(data[:15]):
        print(f"{i+1}. [{msg['date'][:10]}] {msg['author']}:")
        print(f"   {msg['text'][:150]}...")
        print()

if __name__ == "__main__":
    asyncio.run(main())