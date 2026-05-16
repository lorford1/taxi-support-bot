import aiohttp
import logging
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from core.config import settings

logger = logging.getLogger(__name__)

class PlanfixClient:
    """
    Клиент для Planfix XML API
    Документация: https://planfix.com/ru/help/#api
    """
    
    def __init__(self):
        self.account = settings.PLANFIX_ACCOUNT
        self.api_key = settings.PLANFIX_API_KEY
        self.private_key = settings.PLANFIX_PRIVATE_KEY
        self.url = "https://api.planfix.ru/xml/"
        
        # Basic Auth: логин = API Key, пароль = Токен авторизации
        self.auth = aiohttp.BasicAuth(self.api_key, self.private_key)
    
    async def create_task(
        self,
        title: str,
        description: str = "",
        client_id: Optional[int] = None,
        assignee_id: Optional[int] = None,
        importance: int = 1,
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """
        Создание задачи через XML API Planfix
        Задача отображается в Планировщике (календаре)
        """
        # Если даты не указаны — ставим сегодня и завтра
        if start_date is None:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if end_date is None:
            end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Экранируем спецсимволы для XML
        title = self._escape_xml(title)
        description = self._escape_xml(description)
        
        # Формируем XML запрос с ПОЛНЫМИ данными для планировщика
        xml_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<request method="task.add">
    <account>{self.account}</account>
    <task>
        <title>{title}</title>
        <description>{description}</description>
        
        <!-- ПОЛЯ ДЛЯ ОТОБРАЖЕНИЯ В ПЛАНИРОВЩИКЕ -->
        <startDateIsSet>1</startDateIsSet>
        <startDate>{start_date}</startDate>
        <startTimeIsSet>1</startTimeIsSet>
        <startTime>09:00:00</startTime>
        
        <endDateIsSet>1</endDateIsSet>
        <endDate>{end_date}</endDate>
        <endTimeIsSet>1</endTimeIsSet>
        <endTime>18:00:00</endTime>
        
        <durationIsSet>1</durationIsSet>
        <duration>480</duration>
        <durationUnit>0</durationUnit>
    </task>
</request>'''
        
        headers = {
            'Content-Type': 'application/xml',
            'Accept': 'application/xml'
        }
        
        logger.info(f"📤 Создаем задачу в Planfix: {title}")
        logger.debug(f"📋 XML запрос: {xml_body}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.url,
                    data=xml_body.encode('utf-8'),
                    headers=headers,
                    auth=self.auth
                ) as response:
                    text = await response.text()
                    logger.info(f"📊 Статус HTTP: {response.status}")
                    logger.info(f"📨 Ответ Planfix: {text}")
                    
                    if response.status == 200:
                        root = ET.fromstring(text)
                        status = root.get('status')
                        
                        if status == 'ok':
                            task_id = root.findtext('.//task/id')
                            task_general = root.findtext('.//task/general')
                            logger.info(f"✅ Задача успешно создана! ID: {task_id}, General: {task_general}")
                            return {
                                "success": True,
                                "id": task_id,
                                "general": task_general,
                                "url": f"https://{self.account}.planfix.ru/task/{task_general}"
                            }
                        else:
                            error_code = root.findtext('.//code', 'Unknown')
                            error_msg = root.findtext('.//message', 'No message')
                            logger.error(f"❌ API ошибка: {error_code} - {error_msg}")
                            return {
                                "success": False,
                                "error": f"API error {error_code}: {error_msg}"
                            }
                    else:
                        logger.error(f"❌ HTTP ошибка {response.status}: {text[:500]}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {text[:200]}"
                        }
        except Exception as e:
            logger.error(f"❌ Исключение при запросе: {e}")
            return {"success": False, "error": str(e)}
    
    def _escape_xml(self, text: str) -> str:
        """Экранирование спецсимволов для XML"""
        if not text:
            return ""
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&apos;"
        }
        for char, escape in replacements.items():
            text = text.replace(char, escape)
        return text
    
    async def add_comment(self, task_general: int, comment: str) -> bool:
        """Добавление комментария к задаче"""
        comment = self._escape_xml(comment)
        
        xml_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<request method="action.add">
    <account>{self.account}</account>
    <action>
        <task general="{task_general}"/>
        <description>{comment}</description>
    </action>
</request>'''
        
        headers = {
            'Content-Type': 'application/xml',
            'Accept': 'application/xml'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.url,
                    data=xml_body.encode('utf-8'),
                    headers=headers,
                    auth=self.auth
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Ошибка добавления комментария: {e}")
            return False
    
    async def find_contact_by_phone(self, phone: str) -> Optional[Dict]:
        """Поиск контакта по номеру телефона"""
        phone = self._escape_xml(phone)
        
        xml_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<request method="contact.getList">
    <account>{self.account}</account>
    <filters>
        <filter>
            <type>2</type>
            <operator>equal</operator>
            <value>{phone}</value>
        </filter>
    </filters>
    <pageSize>1</pageSize>
</request>'''
        
        headers = {
            'Content-Type': 'application/xml',
            'Accept': 'application/xml'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.url,
                    data=xml_body.encode('utf-8'),
                    headers=headers,
                    auth=self.auth
                ) as response:
                    if response.status == 200:
                        text = await response.text()
                        root = ET.fromstring(text)
                        contact = root.find('.//contact')
                        if contact is not None:
                            return {
                                "id": contact.findtext('id'),
                                "general": contact.findtext('general'),
                                "name": contact.findtext('name')
                            }
        except Exception as e:
            logger.error(f"Ошибка поиска контакта: {e}")
        
        return None

# Создаем глобальный экземпляр
planfix = PlanfixClient()