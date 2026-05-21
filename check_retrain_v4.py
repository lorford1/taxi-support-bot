from openai import OpenAI
from core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

try:
    with open("fine_tune_job_v4.txt", "r") as f:
        job_id = f.read().strip()
    print(f"📋 Job ID: {job_id}")
except:
    job_id = input("Введите Job ID: ")

job = client.fine_tuning.jobs.retrieve(job_id)

print("\n" + "=" * 60)
print(f"📊 СТАТУС ОБУЧЕНИЯ: {job.status.upper()}")
print("=" * 60)

if job.status == "succeeded":
    print(f"\n✅ МОДЕЛЬ ГОТОВА!")
    print(f"📌 Имя модели: {job.fine_tuned_model}")
    print("\n🎉 Сохраните это имя для обновления бота!")
    
    with open("tuned_model_v4.txt", "w") as f:
        f.write(job.fine_tuned_model)
        
elif job.status == "failed":
    print(f"\n❌ Ошибка: {job.error}")
elif job.status == "running":
    print("\n⏳ Обучение идёт...")
    print("⏱️ Осталось примерно 30-60 минут")
elif job.status == "queued":
    print("\n⏳ В очереди... Ожидание начала обучения")