import json

# Загружаем выгруженные данные
with open('planfix_history.json', 'r', encoding='utf-8') as f:
    actions = json.load(f)

print(f"Всего записей: {len(actions)}")
print("\n=== ПОЛЯ В ПЕРВОЙ ЗАПИСИ ===")
if actions:
    first = actions[0]
    for key, value in first.items():
        print(f"{key}: {value}")
else:
    print("Нет данных для анализа")