import asyncio
import sys
from pathlib import Path

# Add bot directory to path
bot_dir = Path(__file__).parent.parent / "bot"
sys.path.append(str(bot_dir))

from bot.services.database import db_service

async def test_bot_database():
    """Test bot database connection"""
    print("Testing bot database connection...")

    try:
        # Test finding a user by phone
        user = await db_service.find_user_by_phone("998900000001")
        if user:
            print(f"User found: {user.full_name} ({user.role})")
        else:
            print("User 998900000001 not found (normal, this is a test number)")

        # Test getting all groups
        groups = await db_service.get_all_groups()
        print(f"Groups count: {len(groups)}")

        if groups:
            print(f"Groups: {[g.name for g in groups]}")

        print("Bot database connection successful!")
        return True

    except Exception as e:
        print(f"Error connecting to database: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_bot_database())
    sys.exit(0 if success else 1)