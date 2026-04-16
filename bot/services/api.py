import httpx
from bot.config import BACKEND_URL, BOT_INTERNAL_TOKEN


class APIClient:
    def __init__(self):
        self._client = httpx.AsyncClient(base_url=BACKEND_URL, timeout=20)

    async def close(self):
        await self._client.aclose()

    def _headers(self):
        return {"X-Bot-Token": BOT_INTERNAL_TOKEN}

    # ==================== LINK & AUTH ====================

    async def link_telegram(self, telegram_id: int, phone: str, username: str | None):
        data = {"telegram_id": str(telegram_id), "phone": phone}
        if username:
            data["username"] = username
        resp = await self._client.post("/api/bot/link", data=data, headers=self._headers())
        return resp.json()

    async def me(self, telegram_id: int):
        resp = await self._client.get("/api/bot/me", params={"telegram_id": telegram_id}, headers=self._headers())
        return resp.json()

    async def webapp_data(self, telegram_id: int):
        resp = await self._client.get("/api/bot/webapp-data", params={"telegram_id": telegram_id}, headers=self._headers())
        return resp.json()

    # ==================== GROUPS ====================

    async def groups(self, telegram_id: int):
        resp = await self._client.get("/api/bot/groups", params={"telegram_id": telegram_id}, headers=self._headers())
        return resp.json()

    async def groups_for_admin(self):
        resp = await self._client.get("/api/bot/groups-for-admin", headers=self._headers())
        return resp.json()

    async def users_by_group(self, group_id: int):
        resp = await self._client.get("/api/bot/users-by-group", params={"group_id": group_id}, headers=self._headers())
        return resp.json()

    # ==================== HOMEWORK ====================

    async def homework_list(self, telegram_id: int):
        resp = await self._client.get("/api/bot/homework", params={"telegram_id": telegram_id}, headers=self._headers())
        return resp.json()

    async def create_homework(self, sent_by: int, title: str, description: str, due_date: str, group_id: int, lesson_id: int | None = None):
        data = {
            "sent_by": sent_by,
            "title": title,
            "description": description,
            "due_date": due_date,
            "group_id": group_id
        }
        if lesson_id:
            data["lesson_id"] = lesson_id
        resp = await self._client.post("/api/bot/homework/create", json=data, headers=self._headers())
        return resp.json()

    async def submit_homework(self, homework_id: int, telegram_id: int, text: str | None, file_path: str | None):
        data = {"telegram_id": str(telegram_id)}
        if text:
            data["text"] = text
        files = None
        if file_path:
            files = {"file": open(file_path, "rb")}
        resp = await self._client.post(f"/api/bot/homework/{homework_id}/submit", data=data, files=files, headers=self._headers())
        if files:
            files["file"].close()
        return resp.json()

    # ==================== PAYMENTS ====================

    async def payments(self, telegram_id: int):
        resp = await self._client.get("/api/bot/payments", params={"telegram_id": telegram_id}, headers=self._headers())
        return resp.json()

    async def upload_receipt(self, telegram_id: int, payment_id: int | None, amount: int | None, note: str | None, file_path: str):
        data = {"telegram_id": str(telegram_id)}
        if payment_id:
            data["payment_id"] = str(payment_id)
        if amount:
            data["amount"] = str(amount)
        if note:
            data["note"] = note
        files = {"file": open(file_path, "rb")}
        resp = await self._client.post("/api/bot/payments/receipt", data=data, files=files, headers=self._headers())
        files["file"].close()
        return resp.json()

    # ==================== MATERIALS ====================

    async def materials(self, telegram_id: int):
        resp = await self._client.get("/api/bot/materials", params={"telegram_id": telegram_id}, headers=self._headers())
        return resp.json()

    # ==================== NOTIFICATIONS ====================

    async def notifications(self, telegram_id: int):
        resp = await self._client.get("/api/bot/notifications", params={"telegram_id": telegram_id}, headers=self._headers())
        return resp.json()

    async def admin_notifications(self):
        resp = await self._client.get("/api/bot/admin-notifications", headers=self._headers())
        return resp.json()

    async def mark_notification_sent(self, notification_id: int):
        resp = await self._client.post(f"/api/bot/notifications/{notification_id}/sent", headers=self._headers())
        return resp.json()

    async def send_notification(self, sent_by: int, target_type: str, target_id: int | None, title: str, body: str, notification_type: str = "announcement"):
        data = {
            "sent_by": sent_by,
            "target_type": target_type,
            "title": title,
            "body": body,
            "notification_type": notification_type
        }
        if target_id:
            data["target_id"] = target_id
        resp = await self._client.post("/api/bot/send-notification", json=data, headers=self._headers())
        return resp.json()

    # ==================== STATS ====================

    async def admin_stats(self):
        resp = await self._client.get("/api/bot/stats", headers=self._headers())
        return resp.json()


api_client = APIClient()
