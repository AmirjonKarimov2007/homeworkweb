#!/usr/bin/env python3
"""
Debug handlers functionality
"""

import asyncio
import os
from dotenv import load_dotenv
from database import db, Database
from models import User

load_dotenv()

async def debug_check_user_by_phone():
    # Initialize database
    await db.initialize()

    phone = '+998917897621'

    print(f"Testing check_user_by_phone with: {phone}")
    print("-" * 50)

    # Test 1: Direct database query
    print("1. Testing direct database query:")
    try:
        async with db.get_connection() as conn:
            query = """
                SELECT u.id, u.full_name, u.role, u.phone, COALESCE(tl.telegram_id, NULL) as telegram_id
                FROM users u
                LEFT JOIN telegram_links tl ON u.id = tl.user_id
                WHERE u.phone = $1
            """
            result = await conn.fetchrow(query, phone)
            if result:
                print(f"   Direct query FOUND: {result}")
            else:
                print("   Direct query NOT FOUND")
    except Exception as e:
        print(f"   Direct query ERROR: {e}")

    # Test 2: Through database function
    print("\n2. Testing through database.check_user_by_phone:")
    try:
        user = await db.check_user_by_phone(phone)
        print(f"   Function result: {user}")
        if user:
            print(f"   Type: {type(user)}")
            print(f"   ID: {user.id}")
            print(f"   Full Name: {user.full_name}")
            print(f"   Role: {user.role}")
            print(f"   Phone: {user.phone}")
            print(f"   Telegram ID: {user.telegram_id}")
        else:
            print("   Function returned None")
    except Exception as e:
        print(f"   Function ERROR: {e}")

    # Test 3: Boolean check
    print("\n3. Testing boolean check:")
    try:
        user = await db.check_user_by_phone(phone)
        print(f"   User object: {user}")
        print(f"   bool(user): {bool(user)}")
        print(f"   user is None: {user is None}")
        print(f"   not user: {not user}")
    except Exception as e:
        print(f"   Boolean check ERROR: {e}")

    await db.close()

if __name__ == "__main__":
    asyncio.run(debug_check_user_by_phone())