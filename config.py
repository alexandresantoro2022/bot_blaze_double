import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TOKEN = os.getenv("TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")
    URL_API = os.getenv("URL_API")
    GALES = int(os.getenv("GALES", 2))
    PROTECTION = os.getenv("PROTECTION", 'True').lower() in ('true', '1', 't')
    CSV_PATH = os.getenv("CSV_PATH", "strategy.csv")
