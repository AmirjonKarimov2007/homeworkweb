# Arabic Center CRM/LMS Database Schema Analysis

## Database Overview

Arabic Center uchun CRM (Customer Relationship Management) va LMS (Learning Management System) sifatida ishlaydigan to'liq database tizimi PostgreSQL asosida qurilgan. Tizim foydalanuvchilar, kurslar, guruhlar, darslar, topshiriqlar, to'lovlar va boshqa ma'lumotlarni boshqarish imkoniyatlarini taqdim etadi.

## Arxitektura

- **Database Engine**: PostgreSQL 14+
- **ORM**: SQLAlchemy 2.0 (async versiyasi)
- **Migration System**: Alembic
- **Connection Pooling**: 20 asosiy + 10 overflow
- **Driver**: asyncpg

## Jadvallar (Tables) va Tarkibi (Columns)

### 1. Users - Foydalanuvchilar
`users` jadvali tizimdagi barcha foydalanuvchilarni saqlaydi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| role | Enum | Foydalanuvchi roli | SUPER_ADMIN, ADMIN, TEACHER, STUDENT |
| phone | String(32) | Telefon raqami | Unique, Indexed |
| email | String(255) | Email manzili | Unique, Nullable |
| full_name | String(255) | To'liq ism | Not null |
| hashed_password | String(255) | Hashlangan parol | Not null |
| is_active | Boolean | Aktiv holati | Default: true |
| avatar_path | String(255) | Avatar fayl yo'li | Nullable |
| last_login_at | DateTime | Oxirgi kirish vaqti | Nullable, Timezone |
| created_at | DateTime | Yaratilgan vaqti | Server default: now() |
| updated_at | DateTime | Yangilangan vaqti | Server default: now(), onupdate |

**Relationships:**
- One-to-One: `telegram_links` (user_id)
- One-to-Many: `lessons`, `homework_tasks`, `payments`, `materials`, `notifications`

### 2. Courses - Kurslar
`courses` jadvali mavjud kurslarni va ularning ma'lumotlarini saqlaydi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| name | String(255) | Kurs nomi | Indexed |
| monthly_fee | Integer | Oylik narxi | Not null |
| duration_months | Integer | Davomiylik (oy) | Nullable |
| description | String(500) | Kurs tavsifi | Nullable |
| is_active | Boolean | Aktiv holati | Default: true |
| created_at | DateTime | Yaratilgan vaqti | Server default: now() |
| updated_at | DateTime | Yangilangan vaqti | Server default: now(), onupdate |

**Relationships:**
- One-to-Many: `groups` (course_id)

### 3. Groups - Guruhlar
`groups` jadvali o'quv guruhlarini boshqaradi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| name | String(255) | Guruh nomi | Indexed |
| goal_type | String(128) | Maqsad turi | Nullable |
| level_label | String(128) | Darajasi | Nullable |
| schedule_time | String(128) | Dars vaqti | Nullable |
| start_date | Date | Boshlanish sanasi | Nullable |
| end_date | Date | Tugash sanasi | Nullable |
| duration_months | Integer | Davomiylik (oy) | Nullable |
| capacity | Integer | Sig'imi | Nullable |
| is_active | Boolean | Aktiv holati | Default: true |
| primary_teacher_id | Integer | Asosiy o'qituvchi | FK: users.id, Nullable |
| curator_id | Integer | Kurator | FK: users.id, Nullable |
| course_id | Integer | Kurs ID | FK: courses.id, Not null |
| monthly_fee | Integer | Oylik narx | Nullable |
| payment_day | Integer | To'lov kuni | Default: 5 |
| grace_days | Integer | Kechikish kunlari | Default: 0 |
| is_payment_required | Boolean | To'lov talab etiladimi | Default: true |
| created_at | DateTime | Yaratilgan vaqti | Server default: now() |
| updated_at | DateTime | Yangilangan vaqti | Server default: now(), onupdate |

**Relationships:**
- Many-to-One: `courses` (course_id)
- Many-to-One: `users` (primary_teacher_id, curator_id)
- One-to-Many: `lessons`, `attendance_records`, `homework_tasks`, `payments`, `materials`

### 4. GroupTeachers - Guruh O'qituvchilari
`group_teachers` jadvali guruhlar bilan bog'langan o'qituvchilarni saqlaydi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| group_id | Integer | Guruh ID | FK: groups.id, Not null |
| teacher_id | Integer | O'qituvchi ID | FK: users.id, Not null |
| created_at | DateTime | Yaratilgan vaqti | Server default: now() |

### 5. StudentGroupEnrollments - Talabalar Guruhi
`student_group_enrollments` jadvali talabalarning guruhlarga qabul qilinishini boshqaradi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| student_id | Integer | Talaba ID | FK: users.id, Not null |
| group_id | Integer | Guruh ID | FK: groups.id, Not null |
| monthly_fee | Integer | Oylik narx | Nullable |
| status | Enum | Holati | ACTIVE, INACTIVE |
| enrolled_at | DateTime | Qabul qilingan vaqti | Server default: now() |

### 6. Lessons - Darslar
`lessons` jadvali har bir dars sessiyalarini saqlaydi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| group_id | Integer | Guruh ID | FK: groups.id, Not null |
| title | String(255) | Dars nomi | Not null |
| date | Date | Dars sanasi | Not null |
| description | Text | Dars tavsifi | Nullable |
| status | String | Holati | Default: "YANGI" |
| created_by | Integer | Yaratuvchi ID | FK: users.id, Not null |
| visible_to_students | Boolean | Talabalarga ko'rinadimi | Default: true |
| created_at | DateTime | Yaratilgan vaqti | Server default: now() |

**Relationships:**
- Many-to-One: `groups` (group_id)
- Many-to-One: `users` (created_by)
- One-to-Many: `lesson_attachments`, `attendance_records`, `homework_tasks`

### 7. LessonAttachments - Dars materiallari
`lesson_attachments` jadvali darslar bilan bog'liq fayllarni saqlaydi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| lesson_id | Integer | Dars ID | FK: lessons.id, Not null |
| file_path | String(255) | Fayl yo'li | Not null |
| file_name | String(255) | Fayl nomi | Not null |
| created_at | DateTime | Yaratilgan vaqti | Server default: now() |

**Relationships:**
- Many-to-One: `lessons` (lesson_id)

### 8. AttendanceRecords - Katilish
`attendance_records` jadvali talabalarning darslardagi katilish holatini kuzatadi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| lesson_id | Integer | Dars ID | FK: lessons.id, Not null |
| student_id | Integer | Talaba ID | FK: users.id, Not null |
| status | Enum | Holati | PRESENT, ABSENT, LATE, EXCUSED |
| note | String(255) | Izoh | Nullable |
| marked_by | Integer | Kim belgilagan | FK: users.id, Not null |
| created_at | DateTime | Yaratilgan vaqti | Server default: now() |

**Relationships:**
- Many-to-One: `lessons` (lesson_id)
- Many-to-One: `users` (student_id, marked_by)

### 9. HomeworkTasks - Topshiriqlar
`homework_tasks` jadvali o'quv topshiriqlarini saqlaydi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| lesson_id | Integer | Dars ID | FK: lessons.id, Not null |
| title | String(255) | Topshiriq nomi | Not null |
| instructions | Text | Tavsiflar | Nullable |
| due_date | DateTime | Topshirish muddati | Nullable |
| allow_late_submission | Boolean | Kechikishga ruxsat | Default: true |
| max_revision_attempts | Integer | Maksimal tuzatish | Default: 2 |
| created_by | Integer | Yaratuvchi ID | FK: users.id, Not null |
| created_at | DateTime | Yaratilgan vaqti | Server default: now() |

**Relationships:**
- Many-to-One: `lessons` (lesson_id)
- Many-to-One: `users` (created_by)
- One-to-Many: `homework_attachments`, `homework_submissions`

### 10. HomeworkAttachments - Topshiriq materiallari
`homework_attachments` jadvali topshiriqlar bilan bog'liq fayllarni saqlaydi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| homework_id | Integer | Topshiriq ID | FK: homework_tasks.id, Not null |
| file_path | String(255) | Fayl yo'li | Not null |
| file_name | String(255) | Fayl nomi | Not null |
| created_at | DateTime | Yaratilgan vaqti | Server default: now() |

**Relationships:**
- Many-to-One: `homework_tasks` (homework_id)

### 11. HomeworkSubmissions - Topshirilgan topshiriqlar
`homework_submissions` jadvali talabalarning topshirilgan topshiriqlarini saqlaydi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| homework_id | Integer | Topshiriq ID | FK: homework_tasks.id, Not null |
| student_id | Integer | Talaba ID | FK: users.id, Not null |
| status | Enum | Holati | NOT_SUBMITTED, SUBMITTED, LATE, REVIEWED, REVISION_REQUESTED, ACCEPTED |
| text | Text | Matn javob | Nullable |
| submitted_at | DateTime | Topshirilgan vaqti | Server default: now() |
| reviewed_by | Integer | Ko'rgan ID | FK: users.id, Nullable |
| reviewed_at | DateTime | Ko'rilgan vaqti | Nullable |
| revision_count | Integer | Tuzatish soni | Default: 0 |

**Relationships:**
- Many-to-One: `homework_tasks` (homework_id)
- Many-to-One: `users` (student_id, reviewed_by)
- One-to-Many: `submission_attachments`

### 12. SubmissionAttachments - Topshirilgan fayllar
`submission_attachments` jadvali talabalar tomonidan yuborilgan fayllarni saqlaydi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| submission_id | Integer | Topshiriq ID | FK: homework_submissions.id, Not null |
| file_path | String(255) | Fayl yo'li | Not null |
| file_name | String(255) | Fayl nomi | Not null |
| created_at | DateTime | Yaratilgan vaqti | Server default: now() |

**Relationships:**
- Many-to-One: `homework_submissions` (submission_id)

### 13. Payments - To'lovlar
`payments` jadvali talabalarning oylik to'lovlarini (fakturalarini) boshqaradi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| student_id | Integer | Talaba ID | FK: users.id, Not null |
| group_id | Integer | Guruh ID | FK: groups.id, Nullable |
| month | String(7) | Oy (YYYY-MM) | Not null |
| billing_year | Integer | Yil | Not null |
| billing_month | Integer | Oy | Not null |
| amount_due | Integer | Muddatli summa | Default: 0 |
| amount_paid | Integer | To'langan summa | Default: 0 |
| status | Enum | Holati | UNPAID, PENDING, PARTIAL, PAID, OVERDUE |
| due_date | Date | To'lov muddati | Not null |
| created_at | DateTime | Yaratilgan vaqti | Server default: now() |
| updated_at | DateTime | Yangilangan vaqti | Server default: now(), onupdate |

**Constraints:**
- Unique constraint: student_id + group_id + billing_year + billing_month

**Relationships:**
- Many-to-One: `users` (student_id)
- Many-to-One: `groups` (group_id)
- One-to-Many: `payment_receipts`, `payment_transactions`

### 14. PaymentReceipts - To'lov hujjatlari
`payment_receipts` jadvali to'lov hujjatlarini saqlaydi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| payment_id | Integer | To'lov ID | FK: payments.id, Not null |
| student_id | Integer | Talaba ID | FK: users.id, Not null |
| amount | Integer | Summa | Nullable |
| status | Enum | Holati | PENDING_REVIEW, CONFIRMED, REJECTED |
| receipt_path | String(255) | Hujjat yo'li | Not null |
| note | String(255) | Izoh | Nullable |
| uploaded_at | DateTime | Yuklangan vaqti | Server default: now() |
| reviewed_by | Integer | Ko'rgan ID | FK: users.id, Nullable |
| reviewed_at | DateTime | Ko'rilgan vaqti | Nullable |

**Relationships:**
- Many-to-One: `payments` (payment_id)
- Many-to-One: `users` (student_id, reviewed_by)

### 15. PaymentTransactions - To'lov tranzaksiyalari
`payment_transactions` jadvali to'lov tranzaksiyalarini saqlaydi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| invoice_id | Integer | Invoice ID | FK: payments.id, Not null |
| student_id | Integer | Talaba ID | FK: users.id, Not null |
| group_id | Integer | Guruh ID | FK: groups.id, Nullable |
| amount | Integer | Summa | Not null |
| payment_method | Enum | Usuli | cash, card, transfer |
| confirmed_by_admin_id | Integer | Tasdiqlagan admin | FK: users.id, Nullable |
| note | String(255) | Izoh | Nullable |
| created_at | DateTime | Yaratilgan vaqti | Server default: now() |

**Relationships:**
- Many-to-One: `payments` (invoice_id)
- Many-to-One: `users` (student_id, confirmed_by_admin_id)

### 16. Materials - Ta'lim materiallari
`materials` jadvali ta'lim materiallarini saqlaydi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| title | String(255) | Nomi | Not null |
| description | Text | Tavsif | Nullable |
| type | Enum | Turu | PDF, AUDIO, VIDEO, LINK, DOCUMENT |
| file_path | String(255) | Fayl yo'li | Nullable |
| link_url | String(512) | Link URL | Nullable |
| created_by | Integer | Yaratuvchi ID | FK: users.id, Not null |
| is_visible | Boolean | Ko'rinadimi | Default: true |
| created_at | DateTime | Yaratilgan vaqti | Server default: now() |

**Relationships:**
- Many-to-One: `users` (created_by)
- One-to-Many: `material_group_links`

### 17. MaterialGroupLinks - Material-guruh bog'lanishi
`material_group_links` jadvali materiallarni guruhlar bilan bog'laydi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| material_id | Integer | Material ID | FK: materials.id, Not null |
| group_id | Integer | Guruh ID | FK: groups.id, Not null |
| created_at | DateTime | Yaratilgan vaqti | Server default: now() |

**Relationships:**
- Many-to-One: `materials` (material_id)
- Many-to-One: `groups` (group_id)

### 18. Notifications - Bildirishnomalar
`notifications` jadvali tizim bildirishnomalarini boshqaradi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| user_id | Integer | Foydalanuvchi ID | FK: users.id, Nullable |
| role_target | String(32) | Rol maqsadi | Nullable |
| title | String(255) | Sarlavha | Not null |
| body | Text | Matn | Nullable |
| channel | Enum | Kanal | TELEGRAM, WEB |
| status | Enum | Holati | PENDING, SENT |
| created_at | DateTime | Yaratilgan vaqti | Server default: now() |
| sent_at | DateTime | Yuborilgan vaqti | Nullable |

**Relationships:**
- Many-to-One: `users` (user_id)

### 19. TelegramLinks - Telegram bog'lanishi
`telegram_links` jadvali foydalanuvchilar va Telegram accountlarini bog'laydi.

**MUHIM:** Bu jadval bot uchun asosiydir. Bot foydalanuvchilarni telefon orqali topadi va ushbu jadvalda telegram_id saqlaydi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| user_id | Integer | Foydalanuvchi ID | FK: users.id, Unique |
| telegram_id | BigInt | Telegram ID | Unique, Indexed |
| username | String(255) | Telegram username | Nullable |
| linked_at | DateTime | Bog'langan vaqti | Server default: now() |

**Relationships:**
- Many-to-One: `users` (user_id)

### 20. AuditLogs - Audit jurnali
`audit_logs` jadvali barcha sistemal harakatlarini yozib boradi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| user_id | Integer | Foydalanuvchi ID | FK: users.id, Nullable |
| action | String(255) | Amal | Not null |
| entity_type | String(128) | Entitet turi | Nullable |
| entity_id | Integer | Entitet ID | Nullable |
| meta | JSON | Qo'shimcha ma'lumot | Nullable |
| created_at | DateTime | Yaratilgan vaqti | Server default: now() |

**Relationships:**
- Many-to-One: `users` (user_id)

### 21. SystemSettings - Tizim sozlamalari
`system_settings` jadvali tizim sozlamalarini saqlaydi.

| Column | Type | Description | Constraints |
|--------|------|-------------|------------|
| id | Integer | Primary key | PK, Auto-increment |
| key | String(128) | Kalit | Unique |
| value | String(512) | Qiymat | Nullable |
| created_at | DateTime | Yaratilgan vaqti | Server default: now() |
| updated_at | DateTime | Yangilangan vaqti | Server default: now(), onupdate |

## Enumlar (Status va Turlar)

### User Roles
- SUPER_ADMIN - Super administrator
- ADMIN - Administrator
- TEACHER - O'qituvchi
- STUDENT - Talaba

### Attendance Status
- PRESENT - Qatnashdi
- ABSENT - Qatnashmadi
- LATE - Kechikkan
- EXCUSED - Sababli qatnashmagan

### Homework Submission Status
- NOT_SUBMITTED - Topshirilmagan
- SUBMITTED - Topshirilgan
- LATE - Kechikkan holda
- REVIEWED - Ko'rib chiqilgan
- REVISION_REQUESTED - Tuzatish so'ralgan
- ACCEPTED - Qabul qilingan

### Payment Status
- UNPAID - To'lanmagan
- PENDING - Kutilayotgan
- PARTIAL - Qisman to'langan
- PAID - To'langan
- OVERDUE - Muddat o'tgan

### Payment Method
- cash - Naqd pul
- card - Karta
- transfer - O'tkazma

### Payment Receipt Status
- PENDING_REVIEW - Ko'rib chiqilmoqda
- CONFIRMED - Tasdiqlangan
- REJECTED - Rad etilgan

### Material Types
- PDF - PDF fayl
- AUDIO - Audio fayl
- VIDEO - Video fayl
- LINK - Havola
- DOCUMENT - Document fayl

### Notification Channels
- TELEGRAM - Telegram kanali
- WEB - Web ilovasi

### Notification Status
- PENDING - Kutilayotgan
- SENT - Yuborilgan

### Enrollment Status
- ACTIVE - Aktiv
- INACTIVE - Nofarl

## Migratsiya Tarixi

1. **0001_init** (2026-03-26) - Asosiy jadvallar yaratildi
2. **0002_billing_module** (2026-04-02) - To'lov moduli qo'shildi
3. **0003_add_courses** (2026-04-08) - Kurslar moduli qo'shildi

## Ma'noli Indekslar

- `users.phone` - Tezkor telefon qidiruv uchun
- `users.email` - Email orqali autentifikatsiya
- `users.role` - Rol bo'yicha filtrlash
- `courses.name` - Kurs nomi bo'yicha qidiruv
- `groups.name` - Guruh nomi bo'yicha qidiruv
- `groups.course_id` - Kurs bo'yicha guruhlarni filtrlash
- `groups.is_active` - Aktiv guruhlarni tezkor olish
- `lessons.group_id` - Guruh darslarini olish
- `lessons.date` - Vaqti bo'yicha darslarni tartibga solish
- `attendance_records.student_id` - Talaba katilish tarixi
- `attendance_records.lesson_id` - Dars katilish tarixi
- `homework_tasks.lesson_id` - Dars topshiriqlari
- `homework_tasks.due_date` - Muddatli topshiriqlarni eslatish
- `homework_submissions.student_id` - Talaba topshiriqlari
- `homework_submissions.homework_id` - Topshiriq bo'yicha filtrlash
- `payments.student_id` - Talaba to'lovlari
- `payments.billing_year` - Yil bo'yicha to'lovlar
- `payments.billing_month` - Oy bo'yicha to'lovlar
- `payments.month` - YYYY-MM formatdagi oy bo'yicha qidiruv
- `materials.type` - Material turlari bo'yicha filtrlash
- `telegram_links.telegram_id` - Bot uchun tezkor qidiruv
- `telegram_links.user_id` - Foydalanuvchi bog'lanishi

## Tizim Arxitekturasi Tahlili

### Data Flow (Ma'lumot oqimi)

1. **User Management:**
   - Foydalanuvchi telefon orqali ro'yxatdan o'tadi
   - Telegram bot foydalanuvchini telefon orqali topadi
   - Rol asosida foydalanuvchi funksiyalari belgilanadi

2. **Academic Workflow:**
   - Kurslar yaratiladi
   - Guruhlar kurs asosida tashkil etiladi
   - Darslar guruhlarga tayinlanadi
   - Topshiriqlar darslar yaratiladi
   - Talabalar topshiriqlarni topshiradi va ko'rib chiqiladi

3. **Payment System:**
   - Oylik to'lovlar avtomatik yaratiladi
   - To'lov hujjatlari yuklanadi va ko'rib chiqiladi
   - Tranzaksiyalar kuzatib boriladi

4. **Notifications:**
   - Muddatli topshiriqlar eslatiladi
   - To'lov eslatmalari yuboriladi
   - Boshqa muhim voqealar haqida bildirishnomalar

### Performance Considerations (Samaradorlik)

1. **Connection Pooling:**
   - 20 asosiy + 10 overflow ulanish
   - Async operatsiyalar tezlikni oshiradi

2. **Indexing Strategy:**
   - Ko'p qidiriladigan maydonlar indekslangan
   - Foreign key indekslari tezlikni oshiradi

3. **Data Partitioning:**
   - Vaqti asosiy jadvallar partition qilinishi mumkin
   - Katta ma'lumotlar to'plamlari uchun optimizatsiya qilingan

### Security (Xavfsizlik)

1. **Authentication:**
   - JWT tokenlari bilan autentifikatsiya
   - Parollar bcrypt orqali hashlangan

2. **Authorization:**
   - Role-based access control (RBAC)
   - Foydalanuvchi harakatlari audit jurnaliga yoziladi

3. **Data Protection:**
   - Personal ma'lumotlar maxfiyligi
   - Telegram bog'lanishlari alohida jadvalda saqlanadi

### Scalability (Miqyoslanuvchanlik)

1. **Database Design:**
   - Normalizatsiya qilingan schema
   - Foreign key bilan bog'langan jadvallar

2. **Future Considerations:**
   - Redis caching uchun tayyorlangan
   - Micro-service arxitekturasi uchun moslashtirilgan

## Xulosa

Bu database schema Arabic Center uchun to'liq CRM/LMS tizimini taqdim etadi. U foydalanuvchilar boshqaruvi, akademik jarayonlar, moliyaviy operatsiyalar va tizim boshqaruvi uchun zarur barcha funktsiyalarga ega. Schema SQLAlchemy ORM va PostgreSQL asosida ishlab chiqilgan, bu esa uning samaradorligi va kengaytirilish imkoniyatlarini ta'minlaydi.