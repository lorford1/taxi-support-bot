import re
from typing import Dict, Any, Optional

class IntentClassifier:
    """
    Классификатор на основе вашей таблицы
    """
    
    # База знаний (сжатая версия из вашей таблицы)
    KNOWLEDGE_BASE = {
        "Выплаты": {
            "keywords": ["деньги", "выплат", "зарплат", "вывести", "вывод"],
            "problems": {
                "не_пришли": {
                    "keywords": ["не пришли", "не получил", "нет денег", "задержка"],
                    "solution": "🔧 Деньги не пришли:\n1. Проверьте статус запроса на вывод\n2. Деньги поступят в течение суток",
                    "need_manager": False
                },
                "отклонили": {
                    "keywords": ["отклонили", "отказ", "не одобрили"],
                    "solution": "🔧 Запрос отклонен. Проверьте баланс или обратитесь к менеджеру.",
                    "need_manager": True
                }
            }
        },
        "Топливная карта": {
            "keywords": ["топливн", "карт", "бензин", "азс", "заправ"],
            "problems": {
                "заблокирована": {
                    "keywords": ["заблокир", "не работает", "не заправ"],
                    "solution": "🔧 Карта заблокирована. Сообщите номер карты, я передам менеджеру для разблокировки.",
                    "need_manager": True
                },
                "не хватает": {
                    "keywords": ["не хватает", "лимит", "мало средств"],
                    "solution": "🔧 Проверьте суточный лимит карты. Сообщите менеджеру для корректировки.",
                    "need_manager": True
                }
            }
        },
        "Доступ к сайту": {
            "keywords": ["доступ", "сайт", "зайти", "войти", "тильд"],
            "problems": {
                "нет_доступа": {
                    "keywords": ["нет доступа", "не могу войти", "не пускает"],
                    "solution": "🔧 Для получения доступа напишите ваше ФИО и email. Менеджер предоставит доступ.",
                    "need_manager": True
                }
            }
        }
    }
    
    def classify(self, text: str) -> Dict[str, Any]:
        """
        Определяет проблему по тексту
        """
        text_lower = text.lower()
        
        # Ищем категорию
        for category, cat_data in self.KNOWLEDGE_BASE.items():
            if any(kw in text_lower for kw in cat_data["keywords"]):
                # Нашли категорию, ищем проблему
                for problem_key, problem_data in cat_data["problems"].items():
                    if any(kw in text_lower for kw in problem_data["keywords"]):
                        return {
                            "category": category,
                            "problem": problem_key,
                            "solution": problem_data["solution"],
                            "need_manager": problem_data.get("need_manager", False),
                            "found": True
                        }
                
                # Категория найдена, но проблема не определена
                return {
                    "category": category,
                    "problem": "уточнение",
                    "solution": f"Пожалуйста, уточните проблему в категории '{category}'. Опишите подробнее.",
                    "need_manager": False,
                    "found": True
                }
        
        # Ничего не найдено
        return {
            "category": "unknown",
            "problem": "unknown",
            "solution": "Я не смог определить вашу проблему. Пожалуйста, напишите 'Оператор' для связи со специалистом.",
            "need_manager": True,
            "found": False
        }

# Создаем экземпляр
classifier = IntentClassifier()