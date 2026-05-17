from openai import OpenAI
from core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

print("🚀 Начинаем fine-tuning модели...")
print("=" * 50)

# Проверяем файл
try:
    with open("all_training_data.jsonl", "r", encoding="utf-8") as f:
        lines = f.readlines()
        print(f"✅ Найдено {len(lines)} примеров для обучения")
except FileNotFoundError:
    print("❌ Файл all_training_data.jsonl не найден!")
    exit(1)

# Загружаем файл в OpenAI
print("\n📤 Загружаем файл в OpenAI...")
with open("all_training_data.jsonl", "rb") as f:
    file = client.files.create(
        file=f,
        purpose="fine-tune"
    )

print(f"✅ Файл загружен! ID: {file.id}")

# Запускаем обучение
print("\n🤖 Запускаем fine-tuning...")
job = client.fine_tuning.jobs.create(
    training_file=file.id,
    model="gpt-4o-mini-2024-07-18",
    suffix="taxi-support-v3"
)

print(f"✅ Fine-tuning запущен!")
print(f"📊 Job ID: {job.id}")
print(f"📊 Статус: {job.status}")

# Сохраняем ID
with open("fine_tune_job_id.txt", "w") as f:
    f.write(job.id)

print("\n⏱️ Обучение займёт 10-30 минут")
print("\n📋 Для проверки статуса выполните: python check_fine_tune_status.py")