from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession


async def paginate(session: AsyncSession, stmt, page: int = 1, size: int = 20):
    total = await session.scalar(select(func.count()).select_from(stmt.subquery()))
    result = await session.execute(stmt.limit(size).offset((page - 1) * size))
    items = result.scalars().all()
    return {"items": items, "total": total or 0, "page": page, "size": size}
