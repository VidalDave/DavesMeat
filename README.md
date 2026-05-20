# חנות הזמנות מוצרים

אפליקציית FastAPI לניהול מכירת מוצרים והזמנות, עם ממשק עברי RTL, PostgreSQL, SQLAlchemy, Alembic ופריסה ל-Render.

## הרצה מקומית

1. צרו סביבת Python והתקינו תלויות:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. צרו קובץ `.env` לפי `.env.example`:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/product_orders
SECRET_KEY=replace-with-a-long-random-secret
APP_ENV=development
PORT=10000
```

3. ודאו ש-PostgreSQL רץ ושמסד הנתונים קיים.

4. הריצו מיגרציות:

```bash
alembic upgrade head
```

5. הפעילו את השרת:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 10000 --reload
```

האתר הציבורי: `http://localhost:10000`  
ממשק ניהול: `http://localhost:10000/ddavedata`

## התחברות ראשונית

המערכת יוצרת משתמש מנהל כברירת מחדל אם אין משתמשים:

- username: `admin`
- password: `admin123!`

לאחר התחברות ראשונה מומלץ להחליף סיסמה דרך מסך משתמשים.

## פריסה ל-Render

1. העלו את הפרויקט ל-GitHub.
2. ב-Render צרו Blueprint מתוך `render.yaml`, או צרו ידנית Web Service ו-PostgreSQL.
3. ודאו שהמשתנים הבאים קיימים בשירות:
   - `DATABASE_URL` מתוך PostgreSQL של Render
   - `SECRET_KEY` ערך אקראי ארוך
   - `APP_ENV=production`
4. ה-Dockerfile מריץ:

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
```

Render מספק את `PORT`, והאפליקציה מאזינה על `0.0.0.0`.

### אחסון תמונות מוצר

תמונות שמועלות דרך ניהול מוצרים נשמרות תחת `storage/static/uploads/products`.
ב-Render מערכת הקבצים של השירות אינה קבועה בין deploy/restart אלא אם מחברים Persistent Disk.
כדי לשמור תמונות שהועלו לאורך זמן, צרו Persistent Disk והגדירו אותו לנתיב:

```txt
/app/storage
```

### התראות אימייל להזמנה חדשה

כדי לשלוח אימייל אחרי יצירת הזמנה, הגדירו ב-Render:

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-user
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=orders@example.com
ORDER_NOTIFICATION_EMAIL=store@example.com
SMTP_USE_TLS=true
```

אפשר לעדכן את כתובת יעד ההתראות גם במסך הגדרות האספקה בממשק הניהול. אם השדה ריק, המערכת משתמשת ב-`ORDER_NOTIFICATION_EMAIL`.

## ניהול

בממשק הניהול אפשר לנהל:

- הזמנות וסטטוסים
- מוצרים, תמונות, משקל, מחיר ומצב פעיל
- מיקומים לתיבת הבחירה
- משתמשים ותפקידים
- הגדרות תאריכי אספקה
- סיכום מוצרים לתאריך אספקה

## אבטחה

- סיסמאות נשמרות עם bcrypt דרך passlib.
- נתיבי הניהול מוגנים בסשן.
- `SECRET_KEY` חייב להגיע ממשתני סביבה.
- `.env` נמצא ב-`.gitignore` ואין להעלות אותו לגיט.
