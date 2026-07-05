# سیستم لاگ‌گیری درخواست‌ها (Request Logging Middleware)

این ماژول یک میان‌افزار (Middleware) برای پروژه‌ی Django است که تمام درخواست‌های HTTP ورودی به سرور را به‌صورت خودکار ثبت (log) می‌کند. ثبت لاگ‌ها به‌صورت **غیرهمزمان (async)** و از طریق **Celery** انجام می‌شود تا هیچ تأثیری روی سرعت پاسخ‌دهی API نداشته باشد.

---

## ویژگی‌ها

- ثبت خودکار تمام درخواست‌های `POST`, `PUT`, `PATCH`, `DELETE` همراه با بدنه‌ی درخواست (Body)
- پشتیبانی از فرمت‌های مختلف بدنه: JSON، فرم معمولی (`form-data`) و آپلود فایل (`multipart/form-data`)
- استخراج اطلاعات کاربر لاگین‌شده (نام کاربری، شماره تلفن، شناسه کاربر)
- تشخیص اطلاعات دستگاه و مرورگر کاربر (User-Agent Parsing) شامل نوع مرورگر، سیستم‌عامل و نوع دستگاه (موبایل/دسکتاپ/تبلت)
- ثبت آی‌پی واقعی کاربر (با در نظر گرفتن هدر `X-Forwarded-For` پشت پراکسی/لودبالانسر)
- ثبت وضعیت پاسخ (status code)، زمان پردازش درخواست (بر حسب میلی‌ثانیه) و پیام خطا در صورت بروز خطا (کد وضعیت ≥ 400)
- امکان ذخیره‌ی لاگ‌ها در سه بستر مختلف با اولویت مشخص:
  1. **MongoDB**
  2. **Object Storage (سازگار با S3)**
  3. **فایل محلی JSON** (fallback نهایی)
- استثنا کردن مسیرهای `/admin/`, `/static/`, `/media/` از فرآیند لاگ‌گیری
- تلاش مجدد خودکار (Retry) در صورت شکست عملیات ذخیره‌سازی، با استفاده از قابلیت `autoretry_for` سلری

---

## ساختار پروژه

```
core/
├── settings.py        # تنظیمات اصلی Django، دیتابیس، سلری و کش
├── db_router.py        # روتر دیتابیس برای هدایت مدل‌های لاگ به SQLite جداگانه
└── mongo.py            # اتصال به MongoDB با استفاده از pymongo

middleware/
├── middleware.py        # کلاس اصلی RequestLogMiddleware
└── tasks.py             # تسک سلری save_request_log برای ذخیره‌ی لاگ
```

---

## نحوه‌ی عملکرد

### ۱. جمع‌آوری اطلاعات درخواست (`middleware.py`)

به ازای هر درخواست:

1. اگر متد درخواست یکی از `POST/PUT/PATCH/DELETE` باشد، بدنه‌ی درخواست بر اساس نوع `Content-Type` استخراج می‌شود:
   - **multipart/form-data**: اطلاعات فرم و متادیتای فایل‌های آپلودی (نام، حجم، نوع فایل) بدون خواندن محتوای فایل استخراج می‌شود.
   - **form-data معمولی**: از `request.POST` خوانده می‌شود.
   - **JSON خام**: با `json.loads` پردازش می‌شود؛ در صورت شکست، به‌عنوان «داده خام یا فایل» علامت‌گذاری می‌شود.
2. زمان شروع و پایان پردازش درخواست اندازه‌گیری می‌شود تا `response_time_ms` محاسبه شود.
3. مسیرهای مربوط به ادمین، فایل‌های استاتیک و مدیا از لاگ‌گیری معاف می‌شوند.
4. اطلاعات کاربر (در صورت لاگین بودن)، آی‌پی، User-Agent و جزئیات دستگاه جمع‌آوری می‌شود.
5. در صورت خطا در پاسخ (کد وضعیت ≥ 400)، پیام خطا نیز استخراج و ذخیره می‌شود.
6. در نهایت، دیکشنری کامل لاگ (`log_data`) پس از عبور از تابع `serialize_for_celery` (برای تبدیل انواع داده‌ی غیرقابل‌سریالایز مانند `ObjectId` و `datetime`) به تسک سلری `save_request_log` ارسال می‌شود.

> توجه: در صورت بروز هرگونه خطا در ارسال به سلری، خطا صرفاً چاپ می‌شود و مانع از برگرداندن پاسخ اصلی به کاربر نمی‌شود.

### ۲. ذخیره‌سازی لاگ (`tasks.py`)

تسک `save_request_log` به‌صورت زیر عمل می‌کند و بر اساس تنظیمات، یکی از مسیرهای زیر را طی می‌کند:

| اولویت | شرط فعال‌سازی | مقصد ذخیره |
|---|---|---|
| ۱ | `MONGO_ACTIVATE=True` | Collection با نام `request_logs` در MongoDB |
| ۲ | `OBJECT_STORAGE_ACTIVE=True` | باکت S3 با مسیر `logs/YYYY-MM-DD/<path>_<timestamp>.json` |
| ۳ (پیش‌فرض) | در غیر این صورت | فایل محلی در مسیر `static/logs/YYYY-MM-DD.json` |

اگر تمام روش‌های ذخیره‌سازی با شکست مواجه شوند، یک `Exception` صریح («All logging backends failed.») صادر می‌شود که باعث فعال شدن مکانیزم Retry سلری (حداکثر ۳ بار، با backoff نمایی) می‌گردد.

---

## پیش‌نیازها و متغیرهای محیطی (Environment Variables)

### دیتابیس اصلی (PostgreSQL/PostGIS)

| متغیر | پیش‌فرض | توضیح |
|---|---|---|
| `PGDB_ENGINE` | `django.contrib.gis.db.backends.postgis` | درایور دیتابیس |
| `PGDB_NAME` | `postgres` | نام دیتابیس |
| `PGDB_USER` | `postgres` | نام کاربری |
| `PGDB_PASS` | `postgres` | رمز عبور |
| `PGDB_HOST` | `0.0.0.0` | آدرس هاست |
| `PGDB_PORT` | `5432` | پورت |

### MongoDB

| متغیر | پیش‌فرض | توضیح |
|---|---|---|
| `MONGO_ACTIVATE` | `False` | فعال/غیرفعال کردن ذخیره در Mongo |
| `MONGO_USER` | `mongouser` | نام کاربری |
| `MONGO_PASS` | `mongopass` | رمز عبور |
| `MONGO_HOST` | `mongo` | آدرس هاست |
| `MONGO_PORT` | `27017` | پورت |
| `MONGO_DB_NAME` | `sedo_logs` | نام دیتابیس |
| `MONGO_AUTH_SOURCE` | `admin` | دیتابیس احراز هویت |

### Object Storage (S3-Compatible)

| متغیر | پیش‌فرض | توضیح |
|---|---|---|
| `OBJECT_STORAGE_ACTIVE` | `False` | فعال/غیرفعال کردن ذخیره در Object Storage |
| `AWS_ACCESS_KEY_ID` | — | کلید دسترسی |
| `AWS_SECRET_ACCESS_KEY` | — | کلید مخفی |
| `AWS_S3_ENDPOINT_URL` | — | آدرس Endpoint سرویس S3 |
| `AWS_STORAGE_BUCKET_NAME` | — | نام باکت |

### سلری و کش (Redis)

| متغیر | پیش‌فرض | توضیح |
|---|---|---|
| `CELERY_REDIS` | `False` | فعال‌سازی بروکر Redis برای سلری |
| `CELERY_BROKER_URL` | `redis://redis:6379/1` | آدرس بروکر سلری |
| `REDIS_CACHE_URL` | `redis://redis:6379/0` | آدرس کش Redis |

### عمومی

| متغیر | پیش‌فرض | توضیح |
|---|---|---|
| `SECRET_KEY` | `test` | کلید امنیتی Django |
| `DEBUG` | `True` | حالت دیباگ |
| `ALLOWED_HOSTS` | `*` | هاست‌های مجاز (جدا شده با کاما) |

---

## نصب و راه‌اندازی

```bash
# نصب پکیج‌های موردنیاز
pip install django djangorestframework python-decouple celery django-redis \
            pymongo boto3 user-agents django-celery-beat

# اجرای مایگریشن‌ها
python manage.py migrate

# اجرای Worker سلری
celery -A core worker -l info

# اجرای Beat (برای تسک‌های زمان‌بندی‌شده مانند بررسی انقضای قرارداد)
celery -A core beat -l info
```

سپس `middleware.middleware.RequestLogMiddleware` باید در `MIDDLEWARE` تنظیمات Django (بعد از `CommonMiddleware` و قبل از `CsrfViewMiddleware`) اضافه شود — که در تنظیمات فعلی این کار انجام شده است.

---

## نمونه ساختار لاگ ذخیره‌شده

```json
{
  "method": "POST",
  "path": "/api/orders/",
  "user": "ali_reza / 09121234567",
  "user_id": "42",
  "ip_address": "185.23.45.12",
  "query_params": {},
  "body": {"product_id": "10", "quantity": "2"},
  "status_code": 201,
  "response_time_ms": 132.45,
  "error_message": null,
  "user_agent": "Mozilla/5.0 (...)",
  "device_info": {
    "browser": "Chrome",
    "browser_version": "125.0",
    "os": "Windows",
    "os_version": "10",
    "device": "Other",
    "is_mobile": false,
    "is_pc": true,
    "is_tablet": false
  },
  "created_at": 1751000000.123
}
```

---

## نکات مهم و پیشنهادات بهبود

- تابع `save_request_log` هرچند مقصد ذخیره‌سازی را به‌صورت اولویت‌دار امتحان می‌کند، اما در صورت موفقیت در MongoDB به‌درستی از تابع خارج (`return`) می‌شود؛ بنابراین ذخیره‌سازی موازی در چند بستر هم‌زمان انجام نمی‌شود، مگر اینکه منطق آن تغییر کند.
- مقدار `mode=777` در `os.makedirs` باید با احتیاط استفاده شود، چون مجوز دسترسی کامل به همه کاربران سیستم می‌دهد؛ برای محیط Production توصیه می‌شود این مقدار محدودتر شود (مثلاً `0o755`).
- توابع `safe_json` و `serialize_for_celery` وظیفه‌ی تبدیل داده‌های غیرقابل‌سریالایز (مانند `ObjectId`, `datetime`, `bytes`) را قبل از ارسال به Celery/Mongo/JSON بر عهده دارند تا از خطاهای سریالایزیشن جلوگیری شود.
- بدنه‌ی فایل‌های آپلودی هرگز به‌طور کامل در لاگ ذخیره نمی‌شود؛ فقط متادیتای فایل (نام، حجم، نوع) ثبت می‌شود تا از حجیم شدن لاگ‌ها و نشت اطلاعات حساس جلوگیری شود.
- توصیه می‌شود اطلاعات حساس (مانند رمز عبور، توکن‌ها) پیش از ثبت لاگ، از بدنه‌ی درخواست فیلتر (mask) شوند؛ در حال حاضر چنین فیلتری در کد پیاده‌سازی نشده است.