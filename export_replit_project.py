print("==> إنشاء ZIP (متوافق مع حدّ 1980 لوقت الملفات)")

zip_path = ROOT / "portable_bundle.zip"
if zip_path.exists():
  zip_path.unlink()


def add_file_with_safe_time(zf, file_path: Path, arcname: Path):
  st = file_path.stat()
  # تاريخ 1/1/1980 00:00:00
  SAFE_DT = (1980, 1, 1, 0, 0, 0)

  # جهّز ZipInfo يدويًا عشان نتحكّم في التاريخ
  zinfo = zipfile.ZipInfo(str(arcname))
  # لو mtime أقدم من 1980، ثبّت التاريخ الآمن
  if int(st.st_mtime) < 315532800:  # 1980-01-01 (epoch)
    zinfo.date_time = SAFE_DT
  else:
    # حوّل mtime الفعلي إلى tuple بالشكل اللي zipfile عايزه
    dt = list(__import__("time").localtime(st.st_mtime))[:6]
    # zipfile يرفض سنوات < 1980؛ نضمن الحد الأدنى
    if dt[0] < 1980:
      zinfo.date_time = SAFE_DT
    else:
      zinfo.date_time = tuple(dt)

  # حافظ على صلاحيات الملف داخل الأرشيف (تنفع على لينكس/ماك)
  zinfo.external_attr = (st.st_mode & 0xFFFF) << 16

  # Binary read ثم writestr
  with file_path.open("rb") as f:
    data = f.read()
  zf.writestr(zinfo, data, compress_type=zipfile.ZIP_DEFLATED)


with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
  # نخزن الملفات داخل الأرشيف بمسار نسبي لـ OUT بحيث المحتوى يظهر تحت _portable_bundle/
  for p in OUT.rglob("*"):
    if p.is_dir():
      continue
    arc = p.relative_to(OUT.parent)  # يحافظ على مجلد _portable_bundle في الجذر
    add_file_with_safe_time(z, p, arc)

print(f"تم إنشاء الحزمة: {zip_path}")
print("كل شيء جاهز ✅")
