# Arabic Center CRM/LMS Loyiha Tavfsifi

## Umumiy ma'lumot

**Arabic Center CRM/LMS** - bu arab tili markazi uchun ishlab chiqilgan birlashtirilgan (monorepo) dasturiy ta'minot tizimi bo'lib, u CRM (mijozlar boshqaruvi) va LMS (elektron o'qitish tizimi) funktsiyalarini bitta yechimda taqdim etadi. Loyiha uchta asosiy xizmatdan iborat:

1. **Backend** - FastAPI API
2. **Frontend** - Next.js 14 veb-ilovasi
3. **Bot** - Telegram bot (aiogram)

## Tizimning asosiy funktsiyalari

### 1. O'qituvchilar uchun
- **Dars jadvallari** - Darslarni rejalashtirish va boshqarish
- **Guruhlar** - O'quvchilar guruhlarini yaratish va boshqarish
- **Topshiriqlar** - Topshiriqlar berish, tekshirish va baholash
- **Materiallar** - O'quv materiallari (PDF, video, audio) yuklash
- **Baho kiritish** - O'quvchilarga ball berish

### 2. O'quvchilar uchun
- **Darslar** - O'z guruhlari darslarini ko'rish
- **Topshiriqlar** - Topshiriqlarni ko'rish va topshirish
- **Baho ko'rish** - O'z baholarini ko'rish
- **Notificationlar** - Darslar, topshiriqlar haqida ogohlantirishlar

### 3. Adminlar uchun
- **Foydalanuvchilar boshqaruvi** - O'qituvchilar va o'quvchilar qo'shish/ta'mirlash
- **To'lovlar** - O'quvchilar to'lovlarini kuzatish
- **Statistika** - Tizim faoliyati statistikasi
- **Telegram bot orqali boshqaruv** - Bot orqali guruhlarga xabar yuborish

### 4. Bot funktsiyalari
- **Guruhlar bilan ishlash** - Yangi o'quvchilar qabul qilish, o'quvchilarni guruhdan chiqarish
- **Topshiriqlar** - Topshiriqlarni tekshirish va baholash
- **Notificationlar** - Darslar, to'lovlar haqida eslatib turish
- **Materiallar** - Dars materiallarini yuborish
- **Ma'lumotlar** - O'quvchilar haqida ma'lumot olish

## Texnik tarkib

### Backend (FastAPI)
- **Framework**: FastAPI
- **Database**: PostgreSQL + asyncpg
- **Scheduler**: APScheduler (cron joblar uchun)
- **Auth**: JWT tokens
- **Async**: Starlette/uvicorn
- **Role-based access**: SUPER_ADMIN, ADMIN, TEACHER, STUDENT

### Frontend (Next.js 14)
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **API integration**: Fetch API
- **TypeScript**: TypeScript
- **Mobile responsive**: Responsive design

### Bot (aiogram)
- **Framework**: aiogram (Telegram bot)
- **Database**: Backend API orqali
- **States**: Finite state machine
- **Webhook/Polling**: Ikkalasi ham qo'llab-quvvatlanadi

### Ma'lumotlar bazasi
- **Schema**: Async SQLAlchemy
- **Pool**: Asyncpg connection pooling
- **Transactions**: Async transaction support
- **Models**: User, Group, Lesson, Homework, Payment, Notification

## Arxitektura tuzilishi

### Backend-Aloqalar
- Bot-backend o'rtasida `/api/bot/*` endpointlar orqali aloqa
- `BOT_INTERNAL_TOKEN` bilan autentifikatsiya
- Frontend-backend orqali `/api/*` endpointlar

### Scheduler (APScheduler)
Backend-da quyidagi cron joblar ishlaydi:
- **1-kun, 08:00** - Oylik to'lovlar yaratish
- **1-kun, 09:00** - To'lov eslatmalari
- **5-kun, 09:00** - Qarzdorlik eslatmalari
- **Har kuni 08:00** - 24 soatlik topshiriq tugash eslatmalari
- **Har kuni 12:00** - 3 soatlik topshiriq tugash eslatmalari
- **Har kuni 18:00** - Qatnashmaganlik chegarasi tekshiruvi

## Foydalanuvchilar va Rollar

### Rollar:
1. **SUPER_ADMIN** - Barcha huquqlar
2. **ADMIN** - Administrator huquqlari
3. **TEACHER** - O'qituvchi huquqlari
4. **STUDENT** - O'quvchi huquqlari

### Mijozlar:
- **Phone format**: +9989xxxxxxxxx (O'zbekiston formati)
- **Default credentials** - README.md da ko'rsatilgan

## Xavfsizlik
- JWT tokenlar (access va refresh)
- Role-based access control
- CORS konfiguratsiyasi
- Bot tokenlari bilan autentifikatsiya
- SQL injection himoyasi

## Rivojlantirish va Deploy

### Loka ishlash uchun:
```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts/init_db.py
python scripts/seed.py
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
copy .env.example .env
npm run dev

# Bot
cd bot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python main.py
```

### Testlar:
```bash
cd backend
pytest
pytest tests/test_auth.py
pytest -k test_login
```

## Fayl tuzilimi

```
homeworkweb/
├── backend/           # FastAPI backend
│   ├── app/          # Application code
│   ├── scripts/      # DB init & seed
│   └── uploads/      # Uploaded files
├── frontend/         # Next.js frontend
│   ├── app/          # App Router
│   └── components/   # React components
├── bot/             # Telegram bot (oldin)
└── .env files       # Environment configurations
```

## Qo'shimcha funktsiyalar

### Fayl yuklash
- **Maksimal hajm**: 10MB
- **Joy**: `/backend/uploads/`
- **Formatlar**: PDF, video, audio

### Notificationlar
- Push notificationlar
- Bot orqali eslatmalar
- SMS/Email (ko'rsatilgan)

### To'lov tizimi
- Oylik to'lovlar
- Qarzdorlik tracking
- Tarixiy ma'lumotlar

## Asosiy texnologiyalar
- **Backend**: Python, FastAPI, PostgreSQL, APScheduler
- **Frontend**: Next.js, TypeScript, Tailwind CSS
- **Bot**: Python, aiogram
- **Database**: PostgreSQL, asyncpg
- **DevOps**: Docker, GitHub Actions (ixtiyoriy)

## Muallif
**Amirjon Karimov** - 2026-yilda ishlab chiqilgan