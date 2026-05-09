#!/usr/bin/env python3
"""
Test script to debug phone number authentication
"""

import asyncio
import os
from dotenv import load_dotenv
from database import db, Database

load_dotenv()

async def test_phone_lookup():
    # Initialize database
    await db.initialize()

    # Test phone numbers
    test_phones = [
        '+998917897621',
        '998917897621',
        '917897621',
        '+998917897621 ',
        '998917897621 '
    ]

    print("Testing phone number lookup:")
    print("=" * 50)

    for phone in test_phones:
        print(f"\nTesting input: '{phone}'")

        # Normalize phone
        normalized = Database.normalize_phone(phone)
        print(f"Normalized: '{normalized}'")

        # Try to find user
        try:
            user = await db.check_user_by_phone(phone)
            if user:
                print(f"[FOUND] User found!")
                print(f"  ID: {user.id}")
                print(f"  Name: {user.full_name}")
                print(f"  Role: {user.role}")
                print(f"  Phone: {user.phone}")
            else:
                print("✗ User not found")
        except Exception as e:
            print(f"[ERROR] Error: {e}")

    await db.close()

if __name__ == "__main__":
    asyncio.run(test_phone_lookup())