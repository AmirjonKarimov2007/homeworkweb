from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.user import User
from app.core.security import verify_password, hash_password, needs_rehash


async def authenticate_user(session: AsyncSession, login: str, password: str) -> User | None:
    login = login.strip()
    if "@" in login:
        stmt = select(User).where(User.email == login)
    else:
        stmt = select(User).where(User.phone == login)
    result = await session.execute(stmt.order_by(User.id.desc()))
    user = result.scalars().first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    if needs_rehash(user.hashed_password):
        user.hashed_password = hash_password(password)
    user.last_login_at = datetime.utcnow()
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
