from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.rate_limit import limiter
from app.api.routers import (
    auth,
    users,
    students,
    teachers,
    groups,
    courses,
    lessons,
    attendance,
    homework,
    payments,
    materials,
    reports,
    notifications,
    audit_logs,
    settings as settings_router,
    bot,
    files,
    health,
)
from app.tasks.scheduler import start_scheduler
from app.db.init import init_db
from app.utils.enums import Role
from app.core.security import hash_password


setup_logging()

app = FastAPI(title="Arabic Center CRM/LMS", version="1.0.0", root_path="/api")

if settings.RATE_LIMIT_ENABLED and limiter:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(students.router, prefix="/api")
app.include_router(teachers.router, prefix="/api")
app.include_router(courses.router, prefix="/api")
app.include_router(groups.router, prefix="/api")
app.include_router(lessons.router, prefix="/api")
app.include_router(attendance.router, prefix="/api")
app.include_router(homework.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(materials.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(audit_logs.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")
app.include_router(bot.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(health.router, prefix="/api")


async def ensure_admin_exists():
    """Create admin user if not exists"""
    from app.db.session import AsyncSessionLocal
    from app.models.user import User
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.phone == "+998917897621")
        )
        existing = result.first()

        if not existing:
            admin = User(
                full_name="Amirjon Karimov",
                phone="+998917897621",
                email="amirjon@example.com",
                role=Role.SUPER_ADMIN,
                hashed_password=hash_password("Karimoff2007"),
                is_active=True,
            )
            session.add(admin)
            await session.commit()
            print("✅ Admin created: +998917897621 / Karimoff2007")


@app.on_event("startup")
async def on_startup():
    if settings.INIT_DB_ON_STARTUP:
        await init_db()
        await ensure_admin_exists()
    start_scheduler()
