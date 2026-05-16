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
        # Параметры для Планировщика
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """
        Создание задачи через XML API Planfix
        """
        # Если даты не указаны — ставим сегодня и завтра
        if start_date is None:
            start_date = datetime.now().strftime("%Y-%m-%d")
        if end_date is None:
            end_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Экранируем спецсимволы для XML
        title = self._escape_xml(title)
        description = self._escape_xml(description)
        
        # Формируем XML запрос
        xml_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<request method="task.add">
    <account>{self.account}</account>
    <task>
        <title>{title}</title>
        <description>{description}</description>
        <importance>{importance}</importance>
        <startDate>{start_date}</startDate>
        <endDate>{end_date}</endDate>
    </task>
</request>'''
        
        headers = {
            'Content-Type': 'application/xml',
            'Accept': 'application/xml'
        }
        
        logger.info(f"Создаем задачу в Planfix: {title}")
        logger.debug(f"XML запрос: {xml_body[:500]}...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.url,
                    data=xml_body.encode('utf-8'),
                    headers=headers,
                    auth=self.auth
                ) as response:
                    text = await response.text()
                    logger.info(f"Статус: {response.status}")
                    logger.debug(f"Ответ: {text[:500]}")
                    
                    if response.status == 200:
                        root = ET.fromstring(text)
                        status = root.get('status')
                        
                        if status == 'ok':
                            task_id = root.findtext('.//task/id')
                            task_general = root.findtext('.//task/general')
                            return {
                                "success": True,
                                "id": task_id,
                                "general": task_general,
                                "url": f"https://{self.account}.planfix.ru/task/{task_general}"
                            }
                        else:
                            error_code = root.findtext('.//code', 'Unknown')
                            error_msg = root.findtext('.//message', 'No message')
                            return {
                                "success": False,
                                "error": f"API error {error_code}: {error_msg}"
                            }
                    else:
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {text[:200]}"
                        }
        except Exception as e:
            logger.error(f"Ошибка: {e}")
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
            logger.error(f"Ошибка комментария: {e}")
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
            logger.error(f"Ошибка поиска: {e}")
        
        return None

planfix = PlanfixClient()