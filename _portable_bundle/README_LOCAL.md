
# Portable Bundle (Exported from Replit)

## Quick start (Windows)
1) ثبت بايثون 3.10+ (أو النسخة المطابقة لمشروعك).
2) افتح PowerShell داخل المجلد:
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
3) انسخ/عدّل ملف .env بقيمك الصحيحة (توكن البوت، مفاتيح API، ...).
4) شغّل:
   run.sh
   أو نفّذ الأمر التالي مباشرة:
   python main.py

## Quick start (Linux/Mac)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)  # أو استخدم python-dotenv داخل الكود
python main.py

## Notes
- إن وجدت replit_db_export.json فهي نسخة من بيانات Replit DB.
- لو كنت تستخدم Webhook (تيليجرام مثلًا)، استخدم ngrok وأعد ضبط WEBHOOK_URL.
- ملف .replit/run.sh يوضح أمر التشغيل الأصلي.
