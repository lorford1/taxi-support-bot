from openai import OpenAI
from core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

try:
    with open("fine_tune_job_id.txt", "r") as f:
        job_id = f.read().strip()
    print(f"📋 Job ID: {job_id}")
except:
    job_id = input("Введите Job ID: ")

job = client.fine_tuning.jobs.retrieve(job_id)

print("\n" + "=" * 50)
print(f"📊 Статус обучения: {job.status}")
print("=" * 50)

if job.status == "succeeded":
    print(f"\n✅ МОДЕЛЬ ГОТОВА!")
    print(f"📌 Имя модели: {job.fine_tuned_model}")
    print("\n🎉 Сохраните это имя!")
    
    with open("tuned_model_name.txt", "w") as f:
        f.write(job.fine_tuned_model)
        
elif job.status == "failed":
    print(f"\n❌ Ошибка: {job.error}")
elif job.status == "running":
    print("\n⏳ Обучение идёт... Проверьте через 5-10 минут")
elif job.status == "queued":
    print("\n⏳ В очереди... Подождите")