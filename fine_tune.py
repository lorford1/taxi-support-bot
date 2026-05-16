import json
from openai import OpenAI
from core.config import settings

# Инициализация клиента OpenAI
client = OpenAI(api_key=settings.OPENAI_API_KEY)

print("🚀 Начинаем процесс обучения модели...")
print("=" * 50)

# Шаг 1: Проверяем, есть ли файл с данными
try:
    with open("training_data.jsonl", "r", encoding="utf-8") as f:
        # Проверяем, что файл не пустой
        first_line = f.readline()
        if not first_line:
            raise ValueError("Файл training_data.jsonl пуст")
        print("✅ Файл training_data.jsonl найден и содержит данные")
except FileNotFoundError:
    print("❌ Ошибка: файл training_data.jsonl не найден!")
    print("Сначала запустите manual_training_data.py для создания данных")
    exit(1)
except Exception as e:
    print(f"❌ Ошибка: {e}")
    exit(1)

# Шаг 2: Загружаем файл в OpenAI
print("\n📤 Загружаем файл в OpenAI...")
with open("training_data.jsonl", "rb") as f:
    file = client.files.create(
        file=f,
        purpose="fine-tune"
    )

print(f"✅ Файл загружен! ID: {file.id}")

# Шаг 3: Запускаем обучение
print("\n🤖 Запускаем обучение модели...")
job = client.fine_tuning.jobs.create(
    training_file=file.id,
    model="gpt-4o-mini-2024-07-18",
    suffix="taxi-support"  # имя вашей модели
)

print(f"✅ Обучение запущено!")
print(f"📊 Job ID: {job.id}")
print(f"📊 Статус: {job.status}")
print("\n⏱️ Обучение обычно занимает 5-15 минут")
print("\n📋 Чтобы проверить статус, выполните:")
print(f'python -c "from openai import OpenAI; client = OpenAI(); job = client.fine_tuning.jobs.retrieve(\'{job.id}\'); print(f\'Статус: {job.status}\')"')

# Сохраняем ID задачи для проверки
with open("fine_tune_job_id.txt", "w") as f:
    f.write(job.id)

print(f"\n💾 Job ID сохранён в fine_tune_job_id.txt")