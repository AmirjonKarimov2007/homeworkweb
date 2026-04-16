# Arabic Center CRM/LMS + Telegram Bot

Production-ready minimal CRM/LMS for an Arabic language center. Includes FastAPI backend, Next.js frontend, and aiogram bot.

## Monorepo Structure
- `backend/` FastAPI API + DB + scheduler
- `frontend/` Next.js 14 app
- `bot/` Telegram bot service
- `docs/` Architecture + API docs

## Local Setup (Recommended)

### 1) Backend
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

### 2) Frontend
```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

### 3) Telegram Bot
```bash
cd bot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python main.py
```

## Notes
- Swagger docs: `http://localhost:8000/docs`
- Uploads stored in `backend/uploads/`
- Bot uses internal token to access `/api/bot/*` endpoints
- For production, configure proper environment variables

## Default Login Credentials (Seeded)
SUPER ADMIN:
- Phone: +998900000001
- Password: Admin123!@#

ADMIN:
- Phone: +998900000002
- Password: Admin123!@#

TEACHER:
- Phone: +998900000003
- Password: Teacher123!@#

STUDENT 1:
- Phone: +998900000004
- Password: Student123!@#
