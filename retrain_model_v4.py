from openai import OpenAI
from core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

print("🚀 ПЕРЕОБУЧЕНИЕ МОДЕЛИ НА 3652 ПРИМЕРАХ")
print("=" * 60)

# Проверяем файл
with open("training_data_3000.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()
    print(f"✅ Найдено {len(lines)} примеров для обучения")

# Загружаем файл в OpenAI
print("\n📤 Загружаем файл в OpenAI...")
with open("training_data_3000.jsonl", "rb") as f:
    file = client.files.create(
        file=f,
        purpose="fine-tune"
    )

print(f"✅ Файл загружен! ID: {file.id}")

# Запускаем переобучение
print("\n🤖 Запускаем переобучение...")
job = client.fine_tuning.jobs.create(
    training_file=file.id,
    model="gpt-4o-mini-2024-07-18",
    suffix="taxi-support-v4"
)

print(f"✅ Переобучение запущено!")
print(f"📊 Job ID: {job.id}")
print(f"📊 Статус: {job.status}")
print(f"📊 Количество примеров: {len(lines)}")

# Сохраняем ID задачи
with open("fine_tune_job_v4.txt", "w") as f:
    f.write(job.id)

print("\n⏱️ ОБУЧЕНИЕ ЗАЙМЁТ 1-2 ЧАСА")
print("\n📋 Для проверки статуса выполните:")
print("python check_retrain_v4.py")