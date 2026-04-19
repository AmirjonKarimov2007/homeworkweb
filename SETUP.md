# Arabic Center CRM/LMS - Setup & Configuration

## 🌐 Server URLs

| Service | Local | Cloudflare Tunnel |
|----------|--------|------------------|
| **Frontend** | `http://localhost:3000` | `https://tall-cartoon-bond-searched.trycloudflare.com/` |
| **Backend** | `http://localhost:8000` | `https://manitoba-cam-notification-divisions.trycloudflare.com/` |
| **Telegram Bot** | Polling | - |

## 🔧 Configuration Files

### Frontend (`frontend/.env`)
```env
NEXT_PUBLIC_API_URL=https://manitoba-cam-notification-divisions.trycloudflare.com/api
NEXT_PUBLIC_BOT_INTERNAL_TOKEN=secret_bot_internal_token_change_me_in_production
```

### Backend (`backend/.env`)
```env
DATABASE_URL=postgresql+asyncpg://postgres:12345678@localhost:5432/homeworkweb
BACKEND_URL=https://manitoba-cam-notification-divisions.trycloudflare.com/
FRONTEND_URL=https://tall-cartoon-bond-searched.trycloudflare.com/
CORS_ORIGINS=https://tall-cartoon-bond-searched.trycloudflare.com,http://localhost:3000
JWT_SECRET=CHANGE_ME_STRONG_SECRET
JWT_REFRESH_SECRET=CHANGE_ME_STRONG_REFRESH_SECRET
```

### Bot (`bot/.env`)
```env
BOT_TOKEN=6679509079:AAEayui5NsCWJchnDXhagdZiBpDoGa5pOHk
BOT_INTERNAL_TOKEN=secret_bot_internal_token_change_me_in_production
BACKEND_URL=https://manitoba-cam-notification-divisions.trycloudflare.com/
ADMIN_IDS=1612270615
POLLING=true
WEBHOOK_URL=
WEBAPP_URL=https://tall-cartoon-bond-searched.trycloudflare.com/login?login=%2B998900000001&password=Admin123%21%40%23
```

## 🚀 How to Start

### 1. Backend
```bash
cd backend
python -m venv/Scripts/activate
uvicorn app.main:app --reload
```

### 2. Frontend
```bash
cd frontend
npm run dev
```

### 3. Cloudflare Tunnels

#### Frontend Tunnel (you're already running this)
```bash
cloudflared tunnel --url http://localhost:3000
# Output: https://tall-cartoon-bond-searched.trycloudflare.com/
```

#### Backend Tunnel (run in new terminal)
```bash
cloudflared tunnel --url http://localhost:8000
# Output: https://manitoba-cam-notification-divisions.trycloudflare.com/
```

### 4. Telegram Bot
```bash
cd bot
python main.py
# Bot will use polling mode
```

## 📱 Test URLs

### Login Page (with auto-login)
```
https://tall-cartoon-bond-searched.trycloudflare.com/login?login=%2B998900000001&password=Admin123%21%40%23
```

### Backend Health
```
https://manitoba-cam-notification-divisions.trycloudflare.com/api/health
```

### WebApp
```
https://tall-cartoon-bond-searched.trycloudflare.com/
```

## 🔑 Demo Credentials

| Role | Phone | Password |
|-------|-------|----------|
| Super Admin | `+998900000001` | `Admin123!@#` |
| Admin | `+998900000002` | `Admin123!@#` |
| Teacher | `+998900000003` | `Teacher123!@#` |

## 📝 Notes

1. **CORS**: Backend `.env` da `CORS_ORIGINS` ni yangiladingiz - frontend URL ni qo'shingiz
2. **Auto-login**: Frontend login sahifa URL parametrlar bilan ishlashadi
3. **Tunnels**: Har bir tunnel uchun yangi terminal ochishingiz kerak
