import pytest
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password
from app.utils.enums import Role


@pytest.mark.asyncio
async def test_login(client):
    async with AsyncSessionLocal() as session:
        user = User(
            full_name="Test",
            phone="+10000000001",
            email="test@example.com",
            role=Role.ADMIN,
            hashed_password=hash_password("Password123!"),
            is_active=True,
        )
        session.add(user)
        await session.commit()

    resp = await client.post("/api/auth/login", json={"login": "+10000000001", "password": "Password123!"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"]
