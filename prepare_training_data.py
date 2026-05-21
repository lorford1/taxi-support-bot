import json
import re

# Загружаем чистые сообщения
with open('clean_yearly_messages.json', 'r', encoding='utf-8') as f:
    messages = json.load(f)

print(f"📂 Загружено {len(messages)} сообщений")

# Системный промпт
SYSTEM_PROMPT = """Ты — AI-агент службы поддержки водителей такси.

Твои правила:
1. Будь вежливым и дружелюбным, используй эмодзи
2. Отвечай коротко и по делу (2-3 предложения)
3. Если проблема требует менеджера — сообщи о создании заявки
4. Всегда обращайся к водителю по имени

Категории проблем:
- 💵 Выплаты: деньги не пришли, квота, реквизиты, IBAN
- ⛽ Топливная карта: блокировка, лимиты, заправка
- 🔐 Доступ к сайту: регистрация, вход, права
- 📦 WB Taxi: вывод денег, проблемы с WB
- 🔧 Техподдержка: приложение, заказы, рейтинг"""

def detect_category(text):
    text_lower = text.lower()
    if any(w in text_lower for w in ['деньг', 'выплат', 'зарплат', 'вывести', 'квот', 'баланс', 'ibán']):
        return "Выплаты"
    elif any(w in text_lower for w in ['топливн', 'карт', 'блокир', 'заправк', 'разблокир']):
        return "Топливная карта"
    elif any(w in text_lower for w in ['доступ', 'сайт', 'регистрац', 'войти', 'почт']):
        return "Доступ к сайту"
    elif any(w in text_lower for w in ['вб', 'вайлдберриз', 'wildberri']):
        return "WB Taxi"
    else:
        return "Техподдержка"

def extract_first_name(author):
    """Извлекает имя из ФИО"""
    name_match = re.search(r'([А-Я][а-я]+)\s+([А-Я][а-я]+)', author)
    if name_match:
        return name_match.group(1)
    return "водитель"

# Создаём обучающие пары
training_pairs = []
skipped = 0

for msg in messages:
    text = msg.get('text', '')
    author = msg.get('author', '')
    
    # Пропускаем слишком короткие
    if len(text) < 10 or len(text) > 1000:
        skipped += 1
        continue
    
    # Пропускаем сообщения-ответы поддержки
    support_words = ['добрый день', 'здравствуйте', 'доступ предоставил', 'разблокировал']
    if any(word in text.lower() for word in support_words):
        skipped += 1
        continue
    
    category = detect_category(text)
    first_name = extract_first_name(author)
    
    # Создаём пример для обучения
    training_pairs.append({
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
            {"role": "assistant", "content": f"📝 Здравствуйте, {first_name}! Ваше обращение принято. Категория: {category}. Создана заявка для специалиста."}
        ]
    })

print(f"✅ Создано {len(training_pairs)} обучающих пар")
print(f"⏭️ Пропущено (короткие/сервисные): {skipped}")

# Сохраняем
with open('training_data_3000.jsonl', 'w', encoding='utf-8') as f:
    for pair in training_pairs:
        f.write(json.dumps(pair, ensure_ascii=False) + '\n')

print(f"📁 Сохранено в training_data_3000.jsonl")

# Статистика по категориям
categories = {}
for pair in training_pairs:
    # Извлекаем категорию из ответа
    content = pair['messages'][2]['content']
    if 'Выплаты' in content:
        cat = 'Выплаты'
    elif 'Топливная карта' in content:
        cat = 'Топливная карта'
    elif 'Доступ к сайту' in content:
        cat = 'Доступ к сайту'
    elif 'WB Taxi' in content:
        cat = 'WB Taxi'
    else:
        cat = 'Техподдержка'
    categories[cat] = categories.get(cat, 0) + 1

print("\n📊 Распределение по категориям:")
for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
    print(f"   {cat}: {count} примеров")