import json
import re

# Загружаем все данные
with open('all_actions.json', 'r', encoding='utf-8') as f:
    all_actions = json.load(f)

print(f"📂 Всего записей в исходном файле: {len(all_actions)}")

# Список ключевых слов, которые указывают на сообщение водителя
driver_keywords = [
    'деньги', 'выплат', 'зарплат', 'карт', 'блокировк', 'заправк',
    'доступ', 'сайт', 'не могу', 'помогите', 'ошибк', 'проблем',
    'пришли', 'получил', 'жду', 'завис', 'не работает', 'сбой'
]

# Слова, которые указывают на системные сообщения (мусор)
system_patterns = [
    r'\{log\d+\}',           # {log26}
    r'\{event\d+\}',         # {event1}
    r'\{\{log\d+\}\}',       # {{log29}}
    r'<[^>]+>',              # HTML теги
    r'event\d+\}',           # event1}
    r'К работе над задачей подключен',
    r'Больше не являются исполнителями',
    r'К участникам задачи добавлены',
    r'robot@',               # системные роботы
]

def is_system_message(text):
    """Проверяет, является ли сообщение системным (мусором)"""
    if not text or len(text) < 15:
        return True
    
    # Проверяем на системные паттерны
    for pattern in system_patterns:
        if re.search(pattern, text):
            return True
    
    return False

def is_driver_message(text):
    """Проверяет, похоже ли сообщение на сообщение водителя"""
    text_lower = text.lower()
    for keyword in driver_keywords:
        if keyword in text_lower:
            return True
    return False

def clean_html(text):
    """Удаляет HTML-теги"""
    return re.sub(r'<[^>]+>', '', text)

# Фильтруем
clean_messages = []
driver_messages = []

for action in all_actions:
    text = action.get('description', '')
    author = action.get('author', '')
    task_title = action.get('task_title', '')
    
    # Очищаем от HTML
    text = clean_html(text)
    
    # Пропускаем системные сообщения
    if is_system_message(text):
        continue
    
    # Пропускаем роботов
    if 'robot' in author.lower() or 'robot' in task_title.lower():
        continue
    
    # Сохраняем все чистые
    clean_messages.append({
        'text': text,
        'author': author,
        'date': action.get('dateTime'),
        'task_title': task_title,
    })
    
    # Отдельно сохраняем подозрительные на сообщения водителей
    if is_driver_message(text):
        driver_messages.append({
            'text': text,
            'author': author,
            'date': action.get('dateTime'),
        })

print(f"\n📊 Результаты фильтрации:")
print(f"   Чистых сообщений: {len(clean_messages)}")
print(f"   Из них похожи на сообщения водителей: {len(driver_messages)}")

# Сохраняем
with open('clean_messages.json', 'w', encoding='utf-8') as f:
    json.dump(clean_messages, f, ensure_ascii=False, indent=2)

with open('driver_messages.json', 'w', encoding='utf-8') as f:
    json.dump(driver_messages, f, ensure_ascii=False, indent=2)

print("\n📁 Сохранено:")
print("   - clean_messages.json (все чистые)")
print("   - driver_messages.json (похожие на сообщения водителей)")

# Показываем примеры сообщений водителей
print("\n=== ПРИМЕРЫ СООБЩЕНИЙ ВОДИТЕЛЕЙ ===")
if driver_messages:
    for i, msg in enumerate(driver_messages[:15]):
        print(f"\n{i+1}. От: {msg['author']}")
        print(f"   Текст: {msg['text'][:200]}")
        print(f"   Дата: {msg['date']}")
else:
    print("⚠️ Не найдено сообщений, похожих на водительские.")
    print("\nПоказываю общие чистые сообщения:")
    for i, msg in enumerate(clean_messages[:10]):
        print(f"\n{i+1}. От: {msg['author']}")
        print(f"   Текст: {msg['text'][:150]}")