import asyncio
from typing import Dict, Any
import json
import os

class HomeworkState:
    """Simple in-memory storage for homework submission states"""
    def __init__(self):
        self._storage: Dict[int, Dict[str, Any]] = {}

    async def save_state(self, user_id: int, homework_id: int):
        """Save homework submission state for user"""
        self._storage[user_id] = {
            "homework_id": homework_id,
            "timestamp": asyncio.get_event_loop().time()
        }

    async def get_state(self, user_id: int) -> Dict[str, Any]:
        """Get homework submission state for user"""
        return self._storage.get(user_id, {})

    async def clear_state(self, user_id: int):
        """Clear homework submission state for user"""
        if user_id in self._storage:
            del self._storage[user_id]

# Global state instance
homework_state = HomeworkState()

async def save_homework_state(user_id: int, homework_id: int):
    """Save homework state"""
    await homework_state.save_state(user_id, homework_id)

async def get_homework_state(user_id: int) -> Dict[str, Any]:
    """Get homework state"""
    return await homework_state.get_state(user_id)

async def clear_homework_state(user_id: int):
    """Clear homework state"""
    await homework_state.clear_state(user_id)