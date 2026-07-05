# ShadowLogger 🕵️‍♂️

![Python Version](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Django Version](https://img.shields.io/badge/Django-5.2+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Celery](https://img.shields.io/badge/Celery-Async%20Logging-orange)
![MongoDB](https://img.shields.io/badge/MongoDB-NoSQL%20Logs-47A248)

**سیستم ثبت لاگ پیشرفته و نامرئی برای جنگو**  
ShadowLogger تمام درخواست‌های ورودی به برنامه Django شما را بدون نیاز به تغییر در کد اصلی برنامه، به صورت کامل و با جزئیات ثبت می‌کند — هم در دیتابیس رابطه‌ای (SQL) و هم به صورت غیرهمزمان در MongoDB (از طریق Celery).

هدف: ردیابی ۱۰۰٪ ترافیک وب بدون تاثیر بر عملکرد و بدون دست‌کاری منطق برنامه.

---

## 🚀 ویژگی‌های کلیدی

| ویژگی                       | توضیحات                                                                 |
|----------------------------|-------------------------------------------------------------------------|
| **دوگانه ثبت لاگ**          | همزمان در SQL (ORM) و MongoDB (آسنکرون با Celery)                         |
| **بدون تغییر در کد برنامه**  | فقط با افزودن دو میدل‌ور به `settings.py` فعال می‌شود                     |
| **جزئیات کامل درخواست**   | متد، مسیر، کاربر، IP، Query Params، Body، زمان پاسخ، خطاها، User-Agent، دستگاه |
| **دیتابیس جداگانه برای لاگ** | تمام لاگ‌های SQL در دیتابیس `logs` ذخیره می‌شوند (با `LogsRouter`)       |
| **پنل ادمین کامل**          | جستجو، فیلتر، فقط‌خواندنی در Django Admin                               |
| **لاگ آسنکرون در MongoDB**  | با Celery + Retry خودکار در صورت قطعی MongoDB                           |
| **حذف خودکار مسیرهای غیرضروری**| به‌صورت پیش‌فرض `/admin`, `/static`, `/media` و health-check مستثنی هستند |
| **پشتیبانی کامل از Docker** | Docker Compose با PostgreSQL + Redis + MongoDB + Celery                   |

---

## 📁 ساختار پروژه
core/
├── middleware/
│   ├── init.py
│   ├── middleware.py      # دو میدل‌ور SQL و NoSQL
│   ├── tasks.py           # تسک Celery برای نوشتن در MongoDB
│   ├── models.py          # مدل RequestLog
│   └── admin.py           # تنظیمات Django Admin
├── core/
│   ├── db_router.py       # LogsRouter برای دیتابیس logs
│   ├── settings.py
│   └── celery.py
envs/
└── .env.dev               # متغیرهای محیطی نمونه
text---

## 🛠 نحوه استفاده در پروژه‌های دیگر (Plug & Play)

1. پوشه `core/middleware` را کپی کنید داخل پروژه‌تان
2. اپ `middleware` را به `INSTALLED_APPS` اضافه کنید
3. میدل‌ورها را به `MIDDLEWARE` اضافه کنید **(ترتیب مهم است!)**:

```python
MIDDLEWARE = [
    # ... سایر میدل‌ورهای جنگو
    'middleware.middleware.RequestLogNOSQLMiddleware',  # اول (برای اندازه‌گیری زمان پاسخ)
    'middleware.middleware.RequestLogSQLMiddleware',     # دوم (برای ذخیره در SQL)
    # ...
]

دیتابیس لاگ و روتر را اضافه کنید:

PythonDATABASES = {
    "default": { ... },
    "logs": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db_logs.sqlite3",
        # یا PostgreSQL/MySQL دلخواه
    },
}

DATABASE_ROUTERS = ['core.db_router.LogsRouter']

Celery + Redis + MongoDB را راه‌اندازی کنید (در ادامه توضیح داده شده)


⚙ پیکربندی محیط (env)
فایل نمونه: envs/.env.dev
env# PostgreSQL (default db)
PGDB_NAME=shadowlogger
PGDB_USER=postgres
PGDB_PASS=postgres
PGDB_HOST=db
PGDB_PORT=5432

# Redis for Celery
CELERY_REDIS=True
REDIS_URL=redis://redis:6379/0

# MongoDB
MONGO_URI=mongodb://mongouser:mongopass@mongo:27017/sedo_logs?authSource=admin

🐳 اجرای سریع با Docker (توصیه شده)
Bashgit clone https://github.com/Hamidrezamoradi1992/ShadowLogger.git
cd ShadowLogger
docker-compose up --build
سرویس‌های اجرا شده:

Django (0.0.0.0:8000)
PostgreSQL
Redis
MongoDB
Celery Worker
Celery Beat


▶ تست سریع
Bashcurl http://localhost:8000/middleware/test/
سپس بررسی کنید:

SQL Logs: http://localhost:8000/admin/middleware/requestlog/
MongoDB:Bashdocker exec -it shadowlogger-mongo-1 mongosh -u mongouser -p mongopass --authenticationDatabase admin sedo_logs
> db.request_logs.find().limit(5).pretty()


🔒 امنیت و حساس‌سازی داده‌ها
در middleware.py می‌توانید به راحتی فیلدهای حساس (مثل password، token، card_number) را ماسک کنید:
PythonSENSITIVE_KEYS = ['password', 'token', 'credit_card', 'ssn']

def mask_sensitive_data(data):
    if isinstance(data, dict):
        return {k: '***MASKED***' if k.lower() in SENSITIVE_KEYS else v for k, v in data.items()}
    return data

📊 مقایسه SQL vs NoSQL Logging






























موردSQL (PostgreSQL/SQLite)NoSQL (MongoDB)تحلیل‌های ساختاریافتهعالی (BI، گزارش‌گیری)متوسطحجم بالا و آرشیومحدود توسط IOPSبسیار بالا و ارزانجستجوی Full-Textبا افزونه‌ها ممکن استNative و سریعبازیابی خطاهاهمگام → بدون از دست رفتن لاگآسنکرون → ممکن است تاخیر داشته باشد

📜 لایسنس
MIT License – آزاد برای استفاده تجاری و شخصی

👤 نویسنده
حمیدرضا مرادی
GitHub: @Hamidrezamoradi1992
LinkedIn: hamidreza-moradi

اگر این پروژه براتون مفید بود، یک ⭐ ستاره فراموش نشه! 😄