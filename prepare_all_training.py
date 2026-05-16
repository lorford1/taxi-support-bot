import json
import re

# Загружаем все сообщения
with open('driver_messages.json', 'r', encoding='utf-8') as f:
    messages = json.load(f)

print(f"📂 Загружено {len(messages)} сообщений")

# Системный промпт (будет одинаков для всех)
SYSTEM_PROMPT = """Ты — AI-агент службы поддержки водителей такси.

Твои правила:
1. Будь вежливым и дружелюбным, используй смайлики
2. Если проблема решается автоматически — дай чёткое решение
3. Если нужен менеджер — сообщи о создании заявки
4. Отвечай коротко и по делу (2-3 предложения)

Категории проблем:
- 💵 Выплаты: деньги не пришли, квота, реквизиты, IBAN, зарплата
- ⛽ Топливная карта: блокировка, лимиты, заправка, разблокировка
- 🔐 Доступ к сайту: регистрация, вход, права, доступ
- 📦 WB Taxi: вывод денег, технические проблемы
- 🔧 Техподдержка: приложение, заказы, активность, Яндекс Про"""

# Функция для определения категории по тексту
def detect_category(text):
    text_lower = text.lower()
    if any(word in text_lower for word in ['деньг', 'выплат', 'зарплат', 'вывести', 'квот', 'баланс', 'ibán']):
        return "💵 Выплаты"
    elif any(word in text_lower for word in ['топливн', 'карт', 'блокир', 'заправк', 'разблокир']):
        return "⛽ Топливная карта"
    elif any(word in text_lower for word in ['доступ', 'сайт', 'регистрац', 'войти', 'почт']):
        return "🔐 Доступ к сайту"
    elif any(word in text_lower for word in ['вб', 'вайлдберриз', 'wildberri']):
        return "📦 WB Taxi"
    else:
        return "🔧 Техподдержка"

# Создаём обучающие пары
# Группируем сообщения по диалогам (по автору и дате)
training_pairs = []
current_dialog = []
current_author = None
current_date = None

# Проходим по всем сообщениям
for i, msg in enumerate(messages):
    text = msg.get('text', '')
    author = msg.get('author', '')
    date = msg.get('date', '')
    
    if not text or len(text) < 10:
        continue
    
    # Если сообщение от водителя (не Брониш Максим, не Николай, не робот)
    is_driver = 'Брониш' not in author and 'Николай' not in author and 'robot' not in author.lower()
    
    if is_driver:
        # Сообщение водителя - это вопрос
        # Ищем следующий ответ поддержки (обычно идёт следующим в списке)
        if i + 1 < len(messages):
            next_msg = messages[i + 1]
            next_author = next_msg.get('author', '')
            next_text = next_msg.get('text', '')
            
            # Если следующий автор - поддержка (Брониш или Николай)
            if 'Брониш' in next_author or 'Николай' in next_author:
                category = detect_category(text)
                
                # Очищаем текст от HTML и мусора
                clean_user = re.sub(r'<[^>]+>', '', text)
                clean_assistant = re.sub(r'<[^>]+>', '', next_text)
                
                # Ограничиваем длину (не больше 500 символов)
                if len(clean_user) > 500:
                    clean_user = clean_user[:500]
                if len(clean_assistant) > 500:
                    clean_assistant = clean_assistant[:500]
                
                training_pairs.append({
                    "user": clean_user,
                    "assistant": clean_assistant,
                    "category": category,
                    "date": date
                })

print(f"\n✅ Создано {len(training_pairs)} обучающих пар")

# Сохраняем в JSONL формате для OpenAI
import json

training_data = []
for pair in training_pairs:
    training_data.append({
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": pair["user"]},
            {"role": "assistant", "content": pair["assistant"]}
        ]
    })

# Сохраняем
with open('all_training_data.jsonl', 'w', encoding='utf-8') as f:
    for item in training_data:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

print(f"📁 Сохранено {len(training_data)} примеров в all_training_data.jsonl")

# Статистика по категориям
categories = {}
for pair in training_pairs:
    cat = pair['category']
    categories[cat] = categories.get(cat, 0) + 1

print("\n📊 Статистика по категориям:")
for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
    print(f"   {cat}: {count} примеров")

# Показываем примеры
print("\n📋 Примеры обучающих пар:")
for i, pair in enumerate(training_pairs[:10]):
    print(f"\n{i+1}. Вопрос ({pair['category']}): {pair['user'][:100]}...")
    print(f"   Ответ: {pair['assistant'][:100]}...")