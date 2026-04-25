# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Monorepo for Arabic Center CRM/LMS with three primary services:
- `backend/` - FastAPI API with PostgreSQL database and APScheduler for cron jobs
- `frontend/` - Next.js 14 web application with Telegram WebApp integration
- `bot/` - Telegram bot (Aiogram 2.25.1) for direct user interaction via PostgreSQL database

## System Architecture

### Backend Architecture
- **Framework**: FastAPI with async support
- **Database**: PostgreSQL with asyncpg driver
- **ORM**: SQLAlchemy with async models
- **Authentication**: JWT-based auth with refresh tokens
- **Scheduling**: APScheduler for automated tasks
- **File Storage**: Local filesystem in `backend/uploads/`
- **Rate Limiting**: Optional slowapi integration

### Frontend Architecture
- **Framework**: Next.js 14 with App Router
- **UI Components**: Tailwind CSS + shadcn/ui components
- **State Management**: Client-side with React hooks
- **API Client**: Axios with interceptors for auth/401 handling
- **Telegram Integration**: Built-in WebApp support for admin panels

### Telegram Bot Architecture
- **Framework**: Aiogram 2.25.1
- **Database**: Direct PostgreSQL connection via asyncpg
- **Authentication**: Phone number based with automatic telegram_id assignment
- **Architecture**: Polling mode with database-first approach
- **Features**: Student homework submission, teacher homework creation, admin management
- **Error Handling**: Comprehensive retry mechanisms and logging

## Database Schema

### Core Entities
1. **Users** - Authentication and role management
   - **IMPORTANT**: The current schema uses `telegram_links` table for telegram_id mapping
   - Roles: SUPER_ADMIN, ADMIN, TEACHER, STUDENT
   - Profile information with phone authentication
   - **NO telegram_id column in users table** (this is the current issue)

2. **Courses** - Subject/course catalog
   - Course management with associated groups

3. **Groups** - Class/group management
   - Schedule times, student enrollments
   - Associated courses and teachers

4. **Lessons** - Individual session tracking
   - Lesson materials and attachments
   - Group association

5. **Attendance** - Student presence tracking
   - Multiple status types (PRESENT, ABSENT, LATE, EXCUSED)

6. **Homework** - Assignment management
   - Homework tasks with due dates
   - Student submissions with file uploads
   - Revision workflow (NOT_SUBMITTED → SUBMITTED → REVIEWED → ACCEPTED)

7. **Payments** - Financial tracking
   - Monthly payment generation
   - Receipt tracking and status management
   - Multiple payment methods

8. **Materials** - Educational resources
   - File type categorization (PDF, AUDIO, VIDEO, LINK, DOCUMENT)
   - Group-specific material distribution

9. **Notifications** - System messaging
   - Role and user-targeted notifications
   - Pending/Sent status tracking

10. **Audit Logs** - Activity tracking
    - System-wide activity logging

### Telegram Link System (Critical for Bot)
- **Table**: `telegram_links` (not `users.telegram_id`)
- **Schema**:
  - `id`: Primary key
  - `user_id`: Foreign key to users.id (unique)
  - `telegram_id`: Big integer (unique, indexed)
  - `username`: String (nullable)
  - `linked_at`: Timestamp with timezone
- **This is the core issue**: Bot code queries users table for telegram_id, but it should query telegram_links table

### Relationships
- Students enroll in groups via `StudentGroupEnrollment`
- Teachers can be assigned to groups via `GroupTeacher`
- Materials are linked to groups through `MaterialGroupLink`
- Users are linked to Telegram via `telegram_links` table

## Authentication & Authorization

### JWT Authentication
- Access tokens: 60-minute expiry
- Refresh tokens: 30-day expiry
- Password hashing with bcrypt

### Role-Based Access Control
- Use `require_roles()` from `app/core/permissions.py` as FastAPI dependency
- Each role has specific access to features and data

### Bot Authentication Flow
1. User sends phone number to bot
2. Bot normalizes phone to +998XXXXXXXXX format
3. Bot looks for user by phone in `users` table
4. IF user found: 
   - Check if already linked in `telegram_links` table
   - If NOT linked: create new record in `telegram_links`
   - If linked: proceed to menu
5. IF user not found: send "User not found" message

## API Structure

### Base Endpoints
- `/api/auth/*` - Authentication (login, refresh, register)
- `/api/users/*` - User management
- `/api/students/*` - Student-specific operations
- `/api/teachers/*` - Teacher-specific operations
- `/api/courses/*` - Course management
- `/api/groups/*` - Group management
- `/api/lessons/*` - Lesson operations
- `/api/attendance/*` - Attendance tracking
- `/api/homework/*` - Homework management
- `/api/payments/*` - Payment processing
- `/api/materials/*` - Material management
- `/api/reports/*` - System reports
- `/api/notifications/*` - Notification handling
- `/api/audit-logs/*` - Activity logs
- `/api/settings/*` - System settings
- `/api/files/*` - File upload/download
- `/api/health/*` - Health checks

### Bot API Endpoints
- `/api/bot/check-phone` - Verify user exists by phone
- `/api/bot/link-telegram` - Link user account to Telegram
- `/api/bot/get-menu` - Get user-specific menu based on role

## Scheduled Tasks

All jobs run in `Asia/Tashkent` timezone:
- **Day 1, 08:00**: Create monthly payments
- **Day 1, 09:00**: Payment reminders
- **Day 5, 09:00**: Debt reminders
- **Daily 08:00**: 24h homework due reminders (if `REMINDER_24H_ENABLED`)
- **Daily 12:00**: 3h homework due reminders (if `REMINDER_3H_ENABLED`)
- **Daily 18:00**: Check absence threshold

## Frontend Application Structure

### Pages
- `(auth)/login` - Authentication page
- `(app)/` - Protected application routes
  - `dashboard` - Overview and statistics
  - `my-groups` - User's groups
  - `groups/[id]` - Group details and management
  - `courses` - Course catalog
  - `lessons` - Lesson scheduling
  - `homework` - Homework assignments
  - `attendance` - Attendance tracking
  - `materials` - Educational materials
  - `payments` - Payment management
  - `students` - Student management
  - `teachers` - Teacher management
  - `reports` - System reports
  - `audit-logs` - Activity logs
  - `notifications` - System notifications
  - `profile` - User profile
  - `finance` - Financial reports
- `(app)/homework/[id]` - Individual homework details
- `(app)/my-groups/[id]` - Specific group details
- `(app)/lessons/[id]` - Individual lesson details
- `webapp` - Admin interface

### Key Components
- Modern UI with responsive design
- Mobile navigation components
- Authentication guard
- Toast notifications
- File upload handling

### Admin WebApp Integration
Built-in admin panel:
- Dashboard with real-time statistics
- Notification broadcasting
- Homework creation
- Group management
- Uses internal API authentication

## Configuration

### Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET` - JWT signing secret
- `UPLOAD_DIR` - File upload directory
- `SCHEDULER_TIMEZONE` - Timezone for scheduled jobs
- `REMINDER_24H_ENABLED` - Enable 24h homework reminders
- `REMINDER_3H_ENABLED` - Enable 3h homework reminders
- `BOT_TOKEN` - Telegram bot token (for bot service)
- `ADMIN_PHONE` - Admin phone number for bot
- `BOT_INTERNAL_TOKEN` - Internal bot API token (for webapp)

### Security
- CORS configured for frontend origins
- Optional rate limiting with slowapi
- File upload size limits
- JWT token validation
- Role-based access control
- Phone-based authentication for bot

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

## Development Notes

### File Uploads
- Files stored in `backend/uploads/`
- Max size: 10MB per file
- Subdirectories: `homework/`, `materials/`, `payments/`

### Database Migrations
- Alembic for database schema management
- Migration files in `backend/alembic/versions/`
- Run `alembic upgrade head` after schema changes

### Error Handling
- Consistent API response format via `app/utils/responses.py`
- Custom exception handlers
- Logging configuration in `app/core/logging.py`

### Performance
- Database connection pooling
- Async operations throughout
- Optional Redis caching (configured but not used)

## Seeded Users
Default credentials are in README.md. Phone format must be `+9989xxxxxxxxx`.

## Critical Database Issue (Telegram Bot)

### Current Problem
The bot code queries the `users` table for a `telegram_id` column, but the database schema stores this information in the `telegram_links` table. This causes authentication to fail.

### Affected Methods in bot/database.py:
1. `check_user_by_phone()` - Works correctly
2. `update_telegram_id()` - Tries to update users.telegram_id (doesn't exist)
3. `get_user_by_telegram_id()` - Queries users.telegram_id (doesn't exist)

### Two Possible Solutions:

#### Option 1: Modify Bot to Use telegram_links Table (Recommended)
Update bot/database.py methods:
- `check_user_by_phone()` - Query users table
- `update_telegram_id()` - Insert/update telegram_links table
- `get_user_by_telegram_id()` - Query telegram_links table

#### Option 2: Add telegram_id Column to Users Table
Run migration to add `telegram_id` column to users table.

### Example Fix for Option 1:
```python
# In database.py - update_telegram_id method
async def update_telegram_id(self, user_id: int, telegram_id: int) -> bool:
    """Update user's telegram_id"""
    try:
        async with self.get_connection() as conn:
            # Check if link already exists
            existing = await conn.fetchrow(
                "SELECT id FROM telegram_links WHERE user_id = $1", user_id
            )
            if existing:
                # Update existing link
                await conn.execute(
                    "UPDATE telegram_links SET telegram_id = $1 WHERE user_id = $2",
                    telegram_id, user_id
                )
            else:
                # Create new link
                await conn.execute(
                    "INSERT INTO telegram_links (user_id, telegram_id) VALUES ($1, $2)",
                    user_id, telegram_id
                )
            return True
    except Exception as e:
        logger.error(f"Error updating telegram_id for user {user_id}: {e}")
        return False
```

## Telegram Bot Features

### Authentication Flow
1. User starts bot with / command
2. Bot requests phone number
3. Phone number is validated and normalized
4. User is searched in users table by phone
5. If found:
   - Check if already linked in telegram_links table
   - If not linked, create new entry in telegram_links
   - Assign telegram_id to user record
   - Display role-based menu
6. If not found: Show "User not found" message

### Error Handling Patterns
```python
# Database connection with retry
@asynccontextmanager
async def get_connection(self):
    connection = None
    try:
        connection = await self.pool.acquire()
        yield connection
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        if connection:
            await self.pool.release(connection)

# Message sending with retry
async def send_with_retry(bot: Bot, chat_id: int, text: str, reply_markup=None):
    for attempt in range(settings.MAX_RETRIES):
        try:
            await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
            return
        except TelegramAPIError as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < settings.MAX_RETRIES - 1:
                await asyncio.sleep(settings.RETRY_DELAY)
            else:
                raise
```

### Database Operations
- Direct asyncpg queries (no ORM)
- Connection pooling for performance
- Automatic phone normalization
- Telegram ID management via telegram_links table
- The bot should be updated to use telegram_links table instead of users.telegram_id

### Bot Migration Issue
The bot expects a telegram_id column in the users table, but the actual schema uses a separate telegram_links table. This mismatch needs to be resolved by either:
1. Modifying the bot code to use telegram_links table (recommended)
2. Adding telegram_id column to users table via migration

### File Structure
```
bot/
├── main.py          # Main bot application
├── handlers.py      # All message handlers
├── database.py      # Database connection layer (NEEDS UPDATE)
├── models.py        # Data models
├── alembic/         # Database migrations
├── .env            # Configuration
├── requirements.txt # Dependencies
└── run_bot.py      # Startup script
```

## Current Status
- Bot runs successfully after fixing import issues
- Database connection works
- **CRITICAL ISSUE**: Bot authentication fails due to telegram_id column mismatch
- User +998917897621 exists but not linked to any Telegram account yet
- Fix required in bot/database.py to use telegram_links table instead of users.telegram_id
