#!/usr/bin/env python3
"""
Database connection and check script
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_database():
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        print("Database connection successful!")

        # Check if user exists
        phone = '+998917897621'
        print(f"\nChecking for phone: {phone}")

        # Get all users first
        users = await conn.fetch("SELECT id, phone, full_name FROM users")
        print(f"\nTotal users: {len(users)}")

        # Check each user
        found = False
        for user in users:
            if phone in user['phone']:
                print(f"[FOUND] Matching user:")
                print(f"  ID: {user['id']}")
                print(f"  Phone: {user['phone']}")
                print(f"  Name: {user['full_name']}")
                found = True

        if not found:
            print("[NOT FOUND] No matching user found")

        # Try direct query with LIKE
        print(f"\nTrying direct query with LIKE:")
        user = await conn.fetchrow("SELECT * FROM users WHERE phone LIKE $1", f'%998917897621%')
        if user:
            print(f"[FOUND] User found with LIKE: {user['full_name']}")
        else:
            print("[NOT FOUND] User not found with LIKE")

        await conn.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_database())