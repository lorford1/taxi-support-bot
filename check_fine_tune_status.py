from openai import OpenAI
from core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Читаем сохранённый Job ID
try:
    with open("fine_tune_job_id.txt", "r") as f:
        job_id = f.read().strip()
    print(f"📋 Job ID: {job_id}")
except:
    print("❌ Не найден файл fine_tune_job_id.txt")
    print("Укажите Job ID вручную или сначала запустите fine_tune.py")
    job_id = input("Введите Job ID: ")

# Получаем статус
job = client.fine_tuning.jobs.retrieve(job_id)

print("\n" + "="*50)
print(f"📊 Статус обучения: {job.status}")
print("="*50)

if job.status == "succeeded":
    print(f"\n✅ МОДЕЛЬ ГОТОВА!")
    print(f"📌 Имя модели: {job.fine_tuned_model}")
    print("\n🎉 Теперь вы можете использовать эту модель в боте!")
    
    # Сохраняем имя модели в файл
    with open("tuned_model_name.txt", "w") as f:
        f.write(job.fine_tuned_model)
        
elif job.status == "failed":
    print(f"\n❌ Обучение не удалось: {job.error}")
elif job.status == "running":
    print("\n⏳ Обучение ещё идёт... Подождите несколько минут и проверьте снова.")
elif job.status == "queued":
    print("\n⏳ Задача в очереди...")
else:
    print(f"\nСтатус: {job.status}")