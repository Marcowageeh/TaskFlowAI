import os, re, json, shutil, sys, subprocess, zipfile
from pathlib import Path

ROOT = Path(".").resolve()
OUT = ROOT / "_portable_bundle"
OUT.mkdir(exist_ok=True)


def run(cmd):
  print("$", " ".join(cmd))
  return subprocess.run(cmd, check=True, text=True,
                        capture_output=True).stdout.strip()


def copy_tree(src: Path, dst: Path, ignore_patterns=None):
  if not src.exists(): return
  if ignore_patterns is None: ignore_patterns = []
  for p in src.rglob("*"):
    rel = p.relative_to(src)
    target = dst / rel
    # تجاهل مجلدات/ملفات لا نريدها
    if any(re.search(pat, str(rel)) for pat in ignore_patterns):
      continue
    if p.is_dir():
      target.mkdir(parents=True, exist_ok=True)
    else:
      target.parent.mkdir(parents=True, exist_ok=True)
      shutil.copy2(p, target)


print("==> جمع الاعتماديات (Python)")
try:
  req = run([sys.executable, "-m", "pip", "freeze"])
  (OUT / "requirements.txt").write_text(req, encoding="utf-8")
except Exception as e:
  print("تحذير: لم أستطع توليد requirements.txt:", e)

print("==> حفظ نسخة من .replit و replit.nix إن وُجدت")
for fname in [".replit", "replit.nix"]:
  p = ROOT / fname
  if p.exists():
    shutil.copy2(p, OUT / fname)

print("==> استخراج أمر التشغيل من .replit (إن وُجد)")
run_cmd = None
replit_file = ROOT / ".replit"
if replit_file.exists():
  text = replit_file.read_text(encoding="utf-8", errors="ignore")
  m = re.search(r"^\s*run\s*=\s*\"(.+?)\"\s*$", text, flags=re.M)
  if m: run_cmd = m.group(1)
if run_cmd is None:
  # تخمين أمر تشغيل شائع
  for cand in [
      "python main.py", "python app.py", "uvicorn app:app --port 8000",
      "python -m bot"
  ]:
    if any(
        (ROOT / n).exists() for n in ["main.py", "app.py", "bot/__init__.py"]):
      run_cmd = cand
      break
if run_cmd:
  (OUT / "run.sh").write_text(f"@echo off\n{run_cmd}\n" if os.name == "nt" else
                              f"#!/usr/bin/env bash\nset -e\n{run_cmd}\n",
                              encoding="utf-8")
  if os.name != "nt":
    os.chmod(OUT / "run.sh", 0o755)

print("==> تجميع المتغيرات السرّية إلى ملف .env")
# قواعد لاستبعاد متغيرات النظام الشائعة
SKIP_PREFIXES = [
    "REPL_",
    "REPLIT_",
    "NIX_",
    "TERM",
    "SHELL",
    "HOME",
    "PATH",
    "LANG",
    "PWD",
    "SHLVL",
    "PYTHON",
    "PIP_",
    "VIRTUAL_ENV",
    "COLORTERM",
    "GIT_",
    "SSH_",
    "XDG_",
]
LIKELY_SECRET_WORDS = [
    "TOKEN", "KEY", "SECRET", "PASS", "PWD", "WEBHOOK", "DSN", "URL", "ID",
    "API", "BEARER", "AUTH", "DB"
]
env_lines = []
for k, v in os.environ.items():
  if any(k.startswith(prefix) for prefix in SKIP_PREFIXES):
    continue
  if len(v) == 0:
    continue
  # ضمّن فقط ما يبدو "سريًا" أو مفيدًا للتشغيل
  if any(w in k.upper() for w in LIKELY_SECRET_WORDS):
    env_lines.append(f'{k}="{v}"')
# أيضًا، لو تعرف أسماء متغيراتك، أضفها يدويًا هنا:
# for name in ["BOT_TOKEN","DATABASE_URL","OPENAI_API_KEY"]:
#     if name in os.environ and f'{name}="' not in "\n".join(env_lines):
#         env_lines.append(f'{name}="{os.environ[name]}"')

if env_lines:
  (OUT / ".env").write_text("\n".join(env_lines) + "\n", encoding="utf-8")
else:
  (OUT / ".env").write_text(
      "# لم أتعرف تلقائيًا على أسرار.\n# أضف قيمك يدويًا هنا بصيغة NAME=VALUE\n",
      encoding="utf-8")

print("==> محاولة تصدير Replit DB إن وُجدت")
replit_db_dump = {}
try:
  # ستنجح لو مكتبة replit مثبّتة والمشروع يستخدم Replit DB
  import importlib
  replit_mod = importlib.import_module("replit")
  db = replit_mod.db
  keys = list(db.keys())
  for k in keys:
    try:
      replit_db_dump[k] = db[k]
    except Exception:
      replit_db_dump[k] = None
  (OUT / "replit_db_export.json").write_text(json.dumps(replit_db_dump,
                                                        ensure_ascii=False,
                                                        indent=2),
                                             encoding="utf-8")
  print(f"تم تصدير {len(keys)} مفاتيح من Replit DB")
except Exception as e:
  # لو فيه متغير REPLIT_DB_URL فقط، نسجّله للمعلومية
  if os.getenv("REPLIT_DB_URL"):
    (OUT / "REPLIT_DB_URL.txt").write_text(os.getenv("REPLIT_DB_URL"),
                                           encoding="utf-8")
  print("ملاحظة: لم أستطع تصدير Replit DB (قد لا تكون مستخدمة).", e)

print("==> نسخ ملفات المشروع إلى مجلد bundle (مع تجاهل مجلدات التطوير)")
IGNORE = [
    r"^\.git(/|$)",
    r"^__pycache__(/|$)",
    r"^\.mypy_cache(/|$)",
    r"^\.pytest_cache(/|$)",
    r"^node_modules(/|$)",
    r"^\.venv(/|$)",
    r"^env(/|$)",
    r"^\.pythonlibs(/|$)",
    r"^_portable_bundle(/|$)",
]
copy_tree(ROOT, OUT, ignore_patterns=IGNORE)

print("==> إضافة README للتشغيل محليًا")
readme = f"""
# Portable Bundle (Exported from Replit)

## Quick start (Windows)
1) ثبت بايثون 3.10+ (أو النسخة المطابقة لمشروعك).
2) افتح PowerShell داخل المجلد:
   python -m venv .venv
   .\\.venv\\Scripts\\Activate.ps1
   pip install -r requirements.txt
3) انسخ/عدّل ملف .env بقيمك الصحيحة (توكن البوت، مفاتيح API، ...).
4) شغّل:
   {"run.sh" if os.name!="nt" else "run.bat أو run.sh"}
   أو نفّذ الأمر التالي مباشرة:
   {run_cmd or "python main.py"}

## Quick start (Linux/Mac)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)  # أو استخدم python-dotenv داخل الكود
{run_cmd or "python main.py"}

## Notes
- إن وجدت replit_db_export.json فهي نسخة من بيانات Replit DB.
- لو كنت تستخدم Webhook (تيليجرام مثلًا)، استخدم ngrok وأعد ضبط WEBHOOK_URL.
- ملف .replit/run.sh يوضح أمر التشغيل الأصلي.
"""
(OUT / "README_LOCAL.md").write_text(readme, encoding="utf-8")

print("==> إنشاء ZIP")
zip_path = ROOT / "portable_bundle.zip"
if zip_path.exists(): zip_path.unlink()
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
  for p in OUT.rglob("*"):
    z.write(p, p.relative_to(OUT.parent))
print(f"تم إنشاء الحزمة: {zip_path}")
print("كل شيء جاهز ✅")
