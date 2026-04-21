import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration for Direct Connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:12345678@localhost:5432/homeworkbot")

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

# Backend Configuration (for fallback)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")