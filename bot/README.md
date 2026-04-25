# Telegram Bot - Arabic Center

Bu Arab Markazi uchun Telegram boti. Foydalanuvchilarga qulay xizmat ko'rsatish, uy ishlarni boshqarish va o'qituvchilar bilan aloqa qilish imkoniyatini beradi.

## Arxitektura

- **Python 3.8+** - Asosiy til
- **Aiogram 2.25.1** - Telegram bot framework
- **asyncpg** - PostgreSQL bilan asinxron bog'lanish
- **PostgreSQL** - Ma'lumotlar bazasi
- **Alembic** - Database migratsiyalari

## Qo'llanish

### 1. O'rnatish

```bash
# Bot papkasiga o'ting
cd bot

# Virtual environment yaratish
python -m venv .venv
.venv\Scripts\activate

# Kutubxonalarni o'rnatish
pip install -r requirements.txt
```

### 2. Konfiguratsiya

`.env` faylini quyidagicha sozlang:

```env
BOT_TOKEN=6679509079:AAEayui5NsCWJchnDXhagdZiBpDoGa5pOHk
ADMIN_PHONE=+998978920967
DATABASE_URL=postgresql+asyncpg://postgres:12345678@localhost:5432/homeworkweb
LOG_LEVEL=INFO
```

### 3. Database ni tayyorlash

```bash
python alembic upgrade head
```

### 4. Botni ishga tushirish

```bash
# Botni ishga tushiring
python run_bot.py
```

## Foydalanuvchi ro'llari

### 1. Talaba
- Telefon raqami orqali identifikatsiya qilinadi
- O'z guruhlarini ko'radi
- Uy ishlarni tekshiradi
- Uy ishlarini topshiradi

### 2. O'qituvchi
- Telefon raqami orqali identifikatsiya qilinadi
- O'z guruhlarini boshqaradi
- Yangi uy ishi yaratadi
- Talabalar uy ishlarini tekshiradi

### 3. Admin
- Barcha funksiyalarga ega
- Foydalanuvchilarni boshqaradi
- Statistikani ko'radi
- Tizim sozlamalarini o'zgartiradi

## Xatolarni boshqarish

Barcha funksiyalarda to'liq error handling qo'llanilgan:

1. **Telegram API xatolari** - Auto retry mehanizmi
2. **Database xatolari** - Connection pool bilan ishlash
3. **Input validation** - Telefon raqami formatini tekshirish
4. **Permission checks** - Rolga mos kirish imkoniyati

## Kod tuzilishi

```
bot/
├── main.py          # Asosiy bot fayli
├── handlers.py      # Barcha handlerslar
├── database.py      # Database bilan ishlash
├── models.py        # Model interfeyslari
├── alembic/         # Database migratsiyalar
│   ├── env.py
│   └── versions/
├── .env            # Konfiguratsiya
├── requirements.txt # Kutubxonalar
└── run_bot.py      # Botni ishga tushirish
```

## Rivojlantirish

### Yangi funksiy qo'shish

1. `handlers.py` da yangi handler qo'shing
2. `models.py` da kerakli model yozing
3. `database.py` da query qo'shing
4. Error handling qo'shishni unutmang

### Testing

```bash
# Bot testini boshlang
python -m pytest tests/
```

## Muhim funksiyalar

### Telefon raqamini normalizatsiya qilish
```python
def normalize_phone(phone: str) -> str:
    """Normalize phone number to +998XXXXXXXXX format"""
    digits = re.sub(r'[^\d]', '', phone)
    if digits.startswith('998'):
        digits = digits[3:]
    elif digits.startswith('998998'):
        digits = digits[6:]
    if len(digits) == 9 and digits.startswith('9'):
        return "+998" + digits
    return phone if phone.startswith('+') else '+' + phone
```

### Database connection management
```python
@asynccontextmanager
async def get_connection(self):
    """Get database connection with error handling"""
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
```

### Message sending with retry
```python
async def send_with_retry(bot: Bot, chat_id: int, text: str, reply_markup=None):
    """Send message with retry mechanism"""
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

## Izohlar

- Bot polling rejimida ishlaydi
- Ma'lumotlar bazasi backend bilan umumiy
- Telegram ID ni avtomatik saqlaydi
- Barcha xatolar logga yoziladi

## Muammolarni hal qilish

1. **Database bog'lanish xatosi** - `.env` faylidagi DATABASE_URL tekshiring
2. **Bot token noto'g'ri** - BOT_TOKEN ni tekshiring
3. **Migratsiya xatosi** - `alembic upgrade head` qaytadan urinib ko'ring
4. **Permission denied** - Foydalanuvchi roliga mos funksiyani tekshiring