import asyncio
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app.db.init import init_db


if __name__ == "__main__":
    asyncio.run(init_db())
    print("Database initialized")
