# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Monorepo for Arabic Center CRM/LMS with three services:
- `backend/` - FastAPI API with PostgreSQL database and APScheduler for cron jobs
- `frontend/` - Next.js 14 web application
- `bot/` - Telegram bot (aiogram) that connects to backend API

## Running the Services

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts/init_db.py
python scripts/seed.py
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

### Telegram Bot
```bash
cd bot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python main.py
```

## Testing

```bash
cd backend
pytest                          # Run all tests
pytest tests/test_auth.py       # Run specific test file
pytest -k test_login            # Run tests matching pattern
```

Tests use in-memory SQLite (set via conftest.py) and automatically create/drop tables.

## Architecture Notes

### Bot-Backend Integration

The bot accesses backend via `/api/bot/*` endpoints using `BOT_INTERNAL_TOKEN` as `X-Bot-Token` header. See `bot/services/api.py` for the API client wrapper and `backend/app/core/deps.py:verify_bot_token()` for authentication.

### Scheduler (APScheduler)

Backend runs cron jobs via `app/tasks/scheduler.py`:
- Day 1, 08:00: Create monthly payments
- Day 1, 09:00: Payment reminders
- Day 5, 09:00: Debt reminders
- Daily 08:00: 24h homework due reminders (if `REMINDER_24H_ENABLED`)
- Daily 12:00: 3h homework due reminders (if `REMINDER_3H_ENABLED`)
- Daily 18:00: Check absence threshold

All jobs run in `Asia/Tashkent` timezone by default.

### Role-Based Access Control

Roles are defined in `app/utils/enums.py`: `SUPER_ADMIN`, `ADMIN`, `TEACHER`, `STUDENT`. Use `require_roles()` from `app/core/permissions.py` as a FastAPI dependency.

### Database

Uses async SQLAlchemy with asyncpg. Models are in `app/models/`, base import from `app/models/__init__.py`. File uploads go to `backend/uploads/`.

### Bot Configuration

Bot can run in polling (`POLLING=true`) or webhook mode. Webhook runs on port 8080, path `/webhook`. Admins defined via `ADMIN_IDS` (comma-separated).

### Seeded Users

Default credentials are in README.md. Phone format must be `+9989xxxxxxxxx`.
