import json
import re

# Загружаем все данные
with open('all_actions.json', 'r', encoding='utf-8') as f:
    all_actions = json.load(f)

print(f"Всего записей: {len(all_actions)}")

# Фильтруем
clean_messages = []

for action in all_actions:
    text = action.get('description', '')
    author = action.get('author', '')
    task_title = action.get('task_title', '')
    
    # Пропускаем пустые
    if not text or len(text) < 10:
        continue
    
    # Пропускаем системных роботов
    if 'robot' in author.lower():
        continue
    if 'robot' in task_title.lower():
        continue
    
    # Пропускаем технический мусор
    if text.startswith('{log2}') or text.startswith('{event'):
        continue
    if '<' in text and '>' in text:
        # Оставляем, но очистим от HTML тегов
        text = re.sub(r'<[^>]+>', '', text)
    
    # Пропускаем слишком короткие
    if len(text) < 15:
        continue
    
    clean_messages.append({
        'text': text,
        'author': author,
        'date': action.get('dateTime'),
        'task_title': task_title,
        'type': action.get('typeName')
    })

print(f"После фильтрации: {len(clean_messages)} сообщений")

# Сохраняем чистые сообщения
with open('clean_messages.json', 'w', encoding='utf-8') as f:
    json.dump(clean_messages, f, ensure_ascii=False, indent=2)

# Показываем примеры
print("\n=== ПРИМЕРЫ ОЧИЩЕННЫХ СООБЩЕНИЙ ===")
for i, msg in enumerate(clean_messages[:20]):
    print(f"\n{i+1}. Автор: {msg['author']}")
    print(f"   Текст: {msg['text'][:150]}...")
    print(f"   Дата: {msg['date']}")