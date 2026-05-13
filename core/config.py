import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    
    PLANFIX_ACCOUNT: str = os.getenv("PLANFIX_ACCOUNT", "")
    PLANFIX_API_KEY: str = os.getenv("PLANFIX_API_KEY", "")
    PLANFIX_PRIVATE_KEY: str = os.getenv("PLANFIX_PRIVATE_KEY", "")
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

settings = Settings()