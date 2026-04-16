import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
BOT_INTERNAL_TOKEN = os.getenv("BOT_INTERNAL_TOKEN", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
POLLING = os.getenv("POLLING", "true").lower() == "true"
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "")
