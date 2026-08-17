from flask import Flask, render_template, request, redirect, url_for, flash, session
from email.message import EmailMessage
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime
import smtplib
import ssl
import os
import re
import uuid
import hashlib


# =========================================================
# SHOVIX - Professional Profile Studio
# =========================================================

load_dotenv()

app = Flask(__name__)

# ---------------------------------------------------------
# SECRET_KEY: إجباري من .env — لا نسمح بقيمة افتراضية
# لأن أي قيمة ثابتة في الكود المصدري تضعف تشفير الـ session
# ---------------------------------------------------------
app.secret_key = os.getenv("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError(
        "SECRET_KEY غير موجود في ملف .env — أضِفه قبل تشغيل السيرفر."
    )


# =========================================================
# EMAIL SETTINGS
# =========================================================

OWNER_EMAIL = os.getenv("OWNER_EMAIL")

# Gmail App Password أحيانًا بييجي بمسافات بين كل 4 أحرف
# (مثال: "abcd efgh ijkl mnop") — لازم نشيلها عشان الـ login ينجح
GMAIL_APP_PASSWORD = (os.getenv("GMAIL_APP_PASSWORD") or "").replace(" ", "").strip()


# =========================================================
# UPLOAD SETTINGS
# =========================================================

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp",
    "pdf"
}

app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# =========================================================
# HELPERS
# =========================================================

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def is_valid_email(value):
    return bool(EMAIL_REGEX.match(value))


def create_request_hash(name, phone, description):

    raw = (
        name.strip().lower()
        + "|"
        + phone.strip()
        + "|"
        + description.strip().lower()
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


# =========================================================
# SEND EMAIL
# =========================================================

def send_order_email(data, files):

    if not OWNER_EMAIL:
        raise RuntimeError(
            "OWNER_EMAIL غير موجود في ملف .env"
        )

    if not GMAIL_APP_PASSWORD:
        raise RuntimeError(
            "GMAIL_APP_PASSWORD غير موجود في ملف .env"
        )

    order_id = str(uuid.uuid4())[:8].upper()

    message = EmailMessage()

    message["Subject"] = (
        f"SHOVIX | طلب #{order_id} | {data['name']}"
    )

    message["From"] = OWNER_EMAIL
    message["To"] = OWNER_EMAIL

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    body = f"""
SHOVIX
Professional Profile Studio
========================================

طلب تصميم صفحة بروفايل جديد

رقم الطلب:
#{order_id}

----------------------------------------
معلومات العميل
----------------------------------------

الاسم:
{data["name"]}

رقم الهاتف:
{data["phone"]}

البريد الإلكتروني:
{data.get("email") or "غير محدد"}

نوع الحساب:
{data["client_type"]}

اسم الشهرة / البروفايل:
{data.get("profile_name") or "غير محدد"}

رابط الحساب:
{data.get("profile_link") or "غير محدد"}

----------------------------------------
تفاصيل المشروع
----------------------------------------

{data["description"]}

----------------------------------------
وقت إرسال الطلب
----------------------------------------

{now}

========================================
SHOVIX
Professional Profile Studio
"""

    message.set_content(body)

    # =====================================================
    # ATTACHMENTS
    # =====================================================

    for file in files:

        if not file:
            continue

        if not file.filename:
            continue

        if not allowed_file(file.filename):
            continue

        filename = secure_filename(
            file.filename
        )

        if not filename:
            continue

        file_data = file.read()

        if not file_data:
            continue

        extension = filename.rsplit(
            ".",
            1
        )[1].lower()

        mime_types = {
            "png": ("image", "png"),
            "jpg": ("image", "jpeg"),
            "jpeg": ("image", "jpeg"),
            "webp": ("image", "webp"),
            "pdf": ("application", "pdf")
        }

        maintype, subtype = mime_types.get(
            extension,
            ("application", "octet-stream")
        )

        message.add_attachment(
            file_data,
            maintype=maintype,
            subtype=subtype,
            filename=filename
        )

    # =====================================================
    # GMAIL SMTP
    # =====================================================

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465,
        context=context
    ) as server:

        server.login(
            OWNER_EMAIL,
            GMAIL_APP_PASSWORD
        )

        server.send_message(
            message
        )

    return order_id


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# ORDER
# =========================================================

@app.route(
    "/order",
    methods=["GET", "POST"]
)
def order():

    # =====================================================
    # GET
    # =====================================================

    # إذا قام شخص بفتح /order مباشرة
    # لن يظهر 405
    if request.method == "GET":

        return redirect(
            url_for("home")
        )

    # =====================================================
    # POST
    # =====================================================

    name = request.form.get(
        "name",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    client_type = request.form.get(
        "client_type",
        "مشهور"
    ).strip()

    profile_name = request.form.get(
        "profile_name",
        ""
    ).strip()

    profile_link = request.form.get(
        "profile_link",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    # =====================================================
    # VALIDATION
    # =====================================================

    if not name:

        flash(
            "يرجى كتابة الاسم.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    if not phone:

        flash(
            "يرجى كتابة رقم الهاتف.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    if not description:

        flash(
            "يرجى كتابة تفاصيل صفحة البروفايل.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    # البريد الإلكتروني اختياري، لكن لو اتكتب لازم يكون بصيغة صحيحة
    if email and not is_valid_email(email):

        flash(
            "صيغة البريد الإلكتروني غير صحيحة.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    # =====================================================
    # DUPLICATE PROTECTION
    # =====================================================

    request_hash = create_request_hash(
        name,
        phone,
        description
    )

    previous_hash = session.get(
        "last_request_hash"
    )

    if previous_hash == request_hash:

        flash(
            "تم إرسال هذا الطلب بالفعل.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    # =====================================================
    # FILES
    # =====================================================

    files = request.files.getlist(
        "files"
    )

    # نتحقق من صيغة كل ملف قبل الإرسال، ونبلّغ المستخدم
    # بدل ما نتجاهل الملف المرفوض بصمت
    for f in files:

        if f and f.filename and not allowed_file(f.filename):

            flash(
                f"الملف \"{f.filename}\" بصيغة غير مدعومة. الصيغ المسموحة: PNG, JPG, JPEG, WEBP, PDF.",
                "error"
            )

            return redirect(
                url_for("home")
            )

    # =====================================================
    # SEND EMAIL
    # =====================================================

    try:

        order_id = send_order_email(

            {
                "name": name,
                "phone": phone,
                "email": email,
                "client_type": client_type,
                "profile_name": profile_name,
                "profile_link": profile_link,
                "description": description
            },

            files
        )

        # حفظ الطلب بعد نجاح الإرسال
        session["last_request_hash"] = request_hash

        flash(
            f"تم إرسال طلبك بنجاح ✓ رقم الطلب: #{order_id}",
            "success"
        )

    # =====================================================
    # GMAIL AUTH ERROR
    # =====================================================

    except smtplib.SMTPAuthenticationError:

        print(
            "EMAIL ERROR: Gmail authentication failed"
        )

        flash(
            "تعذر الاتصال بـ Gmail. تأكد من Gmail App Password.",
            "error"
        )

    # =====================================================
    # SMTP ERROR
    # =====================================================

    except smtplib.SMTPException as error:

        print(
            "SMTP ERROR:",
            error
        )

        flash(
            "حدث خطأ في اتصال Gmail. حاول مرة أخرى.",
            "error"
        )

    # =====================================================
    # GENERAL ERROR
    # =====================================================

    except Exception as error:

        print(
            "EMAIL ERROR:",
            error
        )

        flash(
            "حدث خطأ أثناء إرسال الطلب. حاول مرة أخرى.",
            "error"
        )

    return redirect(
        url_for("home")
    )


# =========================================================
# FILE TOO LARGE
# =========================================================

@app.errorhandler(413)
def file_too_large(error):

    flash(
        "حجم الملفات كبير جدًا. الحد الأقصى 15MB.",
        "error"
    )

    return redirect(
        url_for("home")
    )


# =========================================================
# GENERAL SERVER ERROR
# =========================================================

@app.errorhandler(500)
def internal_error(error):

    print(
        "SERVER ERROR:",
        error
    )

    flash(
        "حدث خطأ في الخادم. حاول مرة أخرى.",
        "error"
    )

    return redirect(
        url_for("home")
    )


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
