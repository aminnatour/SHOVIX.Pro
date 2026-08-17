from flask import Flask, render_template, request, redirect, url_for, flash, session
from email.message import EmailMessage
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime
import smtplib
import ssl
import os
import uuid
import hashlib


# =========================================================
# SHOVIX - Professional Profile Studio
# =========================================================

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "shovix-secret-key-change-this"
)


# =========================================================
# EMAIL SETTINGS
# =========================================================

OWNER_EMAIL = os.getenv("OWNER_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


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


# =========================================================
# HELPERS
# =========================================================

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def create_request_hash(name, phone, description):
    """
    إنشاء بصمة للطلب لمنع إرسال نفس الطلب
    عدة مرات خلال نفس جلسة المستخدم.
    """

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

    # رقم خاص بالطلب
    order_id = str(uuid.uuid4())[:8].upper()

    message = EmailMessage()

    message["Subject"] = (
        f"SHOVIX | طلب #{order_id} | صفحة بروفايل | "
        f"{data['name']}"
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

نوع العميل:
{data["client_type"]}

اسم الشهرة / البروفايل:
{data.get("profile_name") or "غير محدد"}

رابط الحساب:
{data.get("profile_link") or "غير محدد"}

----------------------------------------
الخدمة
----------------------------------------

تصميم صفحة بروفايل احترافية

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
    methods=["POST"]
)
def order():

    # =====================================================
    # GET FORM DATA
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

        # حفظ بصمة الطلب بعد نجاح الإرسال فقط
        session["last_request_hash"] = request_hash

        flash(
            f"تم إرسال طلبك بنجاح ✓ رقم الطلب: #{order_id}",
            "success"
        )


    except smtplib.SMTPAuthenticationError:

        print(
            "EMAIL ERROR: Gmail authentication failed"
        )

        flash(
            "تعذر الاتصال بـ Gmail. تأكد من Gmail App Password.",
            "error"
        )


    except smtplib.SMTPException as error:

        print(
            "SMTP ERROR:",
            error
        )

        flash(
            "حدث خطأ في اتصال Gmail. حاول مرة أخرى.",
            "error"
        )


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
# GENERAL ERRORS
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
# RUN
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