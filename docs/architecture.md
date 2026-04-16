# Architecture Overview

This monorepo contains a minimal yet production-ready CRM/LMS for an Arabic language center with a FastAPI backend, Next.js frontend, and aiogram Telegram bot.

## Services
- **backend**: FastAPI (async) + SQLAlchemy + PostgreSQL, JWT auth, role-based access, file uploads, APScheduler jobs.
- **frontend**: Next.js 14 App Router, Tailwind, shadcn/ui components, React Query for data fetching.
- **bot**: aiogram 3.x bot that calls backend bot endpoints.

## Key Design Choices
- Single shared backend API used by web and bot
- JWT access/refresh tokens for web authentication
- Bot uses internal token for secure bot endpoints
- Local file storage for MVP (`backend/uploads`)
- APScheduler for reminders and monthly notifications
