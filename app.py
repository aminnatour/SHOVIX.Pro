# ============================================================
# SHOVIX - Professional Profile Studio
# Complete Flask Backend - Single File
# ============================================================

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    send_from_directory
)

from email.message import EmailMessage
from werkzeug.utils import secure_filename
from datetime import datetime
from functools import wraps

import smtplib
import ssl
import os
import uuid
import hashlib
import sqlite3
import re
import secrets
import html


# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "SHOVIX"

# ------------------------------------------------------------
# ضع إيميل SHOVIX هنا
# ------------------------------------------------------------

OWNER_EMAIL = "YOUR_EMAIL@gmail.com"

# ------------------------------------------------------------
# ضع Gmail App Password هنا
#
# مثال:
# "abcd efgh ijkl mnop"
#
# لا تستخدم كلمة مرور Gmail العادية.
# ------------------------------------------------------------

GMAIL_APP_PASSWORD = "YOUR_GMAIL_APP_PASSWORD"

# ------------------------------------------------------------
# كلمة مرور لوحة الإدارة
# ------------------------------------------------------------

ADMIN_PASSWORD = "CHANGE_THIS_ADMIN_PASSWORD"

# ------------------------------------------------------------
# بيانات التطبيق
# ------------------------------------------------------------

SECRET_KEY = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET_KEY"

DATABASE = "shovix.db"

UPLOAD_FOLDER = "shovix_uploads"

MAX_FILE_SIZE = 15 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp",
    "pdf"
}

ALLOWED_MIME_TYPES = {
    "image/png",
    "image/jpeg",
    "image/webp",
    "application/pdf"
}

ORDER_STATUSES = {
    "new": "جديد",
    "processing": "قيد التنفيذ",
    "completed": "مكتمل",
    "cancelled": "ملغي"
}


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)

app.secret_key = SECRET_KEY

app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["SESSION_COOKIE_HTTPONLY"] = True

app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# في الإنتاج مع HTTPS يمكنك تفعيلها:
# app.config["SESSION_COOKIE_SECURE"] = True


# ============================================================
# CREATE UPLOAD DIRECTORY
# ============================================================

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ============================================================
# DATABASE
# ============================================================

def get_db():

    connection = sqlite3.connect(
        DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection


def init_database():

    connection = get_db()

    cursor = connection.cursor()

    # --------------------------------------------------------
    # Orders
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            order_id TEXT UNIQUE NOT NULL,

            name TEXT NOT NULL,

            phone TEXT NOT NULL,

            email TEXT,

            client_type TEXT,

            profile_name TEXT,

            profile_link TEXT,

            description TEXT NOT NULL,

            status TEXT DEFAULT 'new',

            request_hash TEXT,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL

        )
    """)

    # --------------------------------------------------------
    # Files
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_files (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            order_id TEXT NOT NULL,

            original_name TEXT NOT NULL,

            stored_name TEXT NOT NULL,

            file_size INTEGER DEFAULT 0,

            mime_type TEXT,

            created_at TEXT NOT NULL

        )
    """)

    # --------------------------------------------------------
    # Indexes
    # --------------------------------------------------------

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_orders_order_id
        ON orders(order_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_orders_created_at
        ON orders(created_at)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_orders_request_hash
        ON orders(request_hash)
    """)

    connection.commit()

    connection.close()


# ============================================================
# HELPERS
# ============================================================

def now_string():

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def allowed_file(filename):

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return extension in ALLOWED_EXTENSIONS


def clean_text(value, max_length=5000):

    if value is None:
        return ""

    value = str(value).strip()

    return value[:max_length]


def valid_email(email):

    if not email:
        return True

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return re.match(
        pattern,
        email
    ) is not None


def valid_phone(phone):

    if not phone:
        return False

    # يسمح بالأرقام + المسافات والشرطة والأقواس
    pattern = r"^[0-9+\-\s()]{7,25}$"

    return re.match(
        pattern,
        phone
    ) is not None


def valid_url(url):

    if not url:
        return True

    pattern = r"^https?://"

    return re.match(
        pattern,
        url,
        re.IGNORECASE
    ) is not None


def create_request_hash(
    name,
    phone,
    description
):

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


def generate_order_id():

    date_part = datetime.now().strftime(
        "%Y%m%d"
    )

    random_part = secrets.token_hex(
        3
    ).upper()

    return f"SHX-{date_part}-{random_part}"


def generate_stored_filename(
    original_filename
):

    extension = ""

    if "." in original_filename:

        extension = (
            "."
            + original_filename.rsplit(
                ".",
                1
            )[1].lower()
        )

    return (
        uuid.uuid4().hex
        + extension
    )


# ============================================================
# ADMIN AUTHENTICATION
# ============================================================

def admin_required(function):

    @wraps(function)
    def decorated(*args, **kwargs):

        if not session.get(
            "admin_logged_in"
        ):

            return redirect(
                url_for(
                    "admin_login"
                )
            )

        return function(
            *args,
            **kwargs
        )

    return decorated


# ============================================================
# EMAIL
# ============================================================

def send_order_email(
    order,
    files
):

    if (
        not OWNER_EMAIL
        or OWNER_EMAIL == "YOUR_EMAIL@gmail.com"
    ):

        raise RuntimeError(
            "قم بتعديل OWNER_EMAIL داخل shovix.py"
        )

    if (
        not GMAIL_APP_PASSWORD
        or GMAIL_APP_PASSWORD
        == "YOUR_GMAIL_APP_PASSWORD"
    ):

        raise RuntimeError(
            "قم بتعديل GMAIL_APP_PASSWORD داخل shovix.py"
        )

    message = EmailMessage()

    message["Subject"] = (
        f"SHOVIX | طلب جديد "
        f"#{order['order_id']} | "
        f"{order['name']}"
    )

    message["From"] = OWNER_EMAIL

    message["To"] = OWNER_EMAIL

    if order.get("email"):

        message["Reply-To"] = order["email"]

    body = f"""
============================================================
                         SHOVIX
                 Professional Profile Studio
============================================================

تم استلام طلب تصميم جديد.

رقم الطلب:
{order["order_id"]}

------------------------------------------------------------
معلومات العميل
------------------------------------------------------------

الاسم:
{order["name"]}

رقم الهاتف:
{order["phone"]}

البريد الإلكتروني:
{order.get("email") or "غير محدد"}

نوع العميل:
{order.get("client_type") or "غير محدد"}

اسم البروفايل:
{order.get("profile_name") or "غير محدد"}

رابط الحساب:
{order.get("profile_link") or "غير محدد"}

------------------------------------------------------------
الخدمة
------------------------------------------------------------

تصميم صفحة بروفايل احترافية

------------------------------------------------------------
تفاصيل المشروع
------------------------------------------------------------

{order["description"]}

------------------------------------------------------------
وقت الطلب
------------------------------------------------------------

{order["created_at"]}

------------------------------------------------------------
الحالة
------------------------------------------------------------

جديد

============================================================
SHOVIX
Professional Profile Studio
============================================================
"""

    message.set_content(
        body
    )

    # --------------------------------------------------------
    # Attachments
    # --------------------------------------------------------

    for file_info in files:

        file_path = file_info["path"]

        if not os.path.exists(
            file_path
        ):
            continue

        with open(
            file_path,
            "rb"
        ) as file:

            file_data = file.read()

        mime_type = (
            file_info["mime_type"]
            or "application/octet-stream"
        )

        if "/" in mime_type:

            maintype, subtype = (
                mime_type.split(
                    "/",
                    1
                )
            )

        else:

            maintype = "application"

            subtype = "octet-stream"

        message.add_attachment(
            file_data,
            maintype=maintype,
            subtype=subtype,
            filename=file_info[
                "original_name"
            ]
        )

    # --------------------------------------------------------
    # Gmail SMTP
    # --------------------------------------------------------

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


# ============================================================
# SAVE FILES
# ============================================================

def save_uploaded_files(
    order_id,
    uploaded_files
):

    saved_files = []

    order_folder = os.path.join(
        UPLOAD_FOLDER,
        order_id
    )

    os.makedirs(
        order_folder,
        exist_ok=True
    )

    try:

        for uploaded_file in uploaded_files:

            if not uploaded_file:
                continue

            original_name = (
                uploaded_file.filename
                or ""
            ).strip()

            if not original_name:
                continue

            if not allowed_file(
                original_name
            ):

                raise ValueError(
                    f"نوع الملف غير مسموح: "
                    f"{original_name}"
                )

            safe_original_name = (
                secure_filename(
                    original_name
                )
            )

            if not safe_original_name:

                raise ValueError(
                    "اسم الملف غير صالح."
                )

            stored_name = (
                generate_stored_filename(
                    safe_original_name
                )
            )

            file_path = os.path.join(
                order_folder,
                stored_name
            )

            uploaded_file.save(
                file_path
            )

            file_size = os.path.getsize(
                file_path
            )

            if file_size > MAX_FILE_SIZE:

                os.remove(
                    file_path
                )

                raise ValueError(
                    "حجم أحد الملفات كبير جدًا."
                )

            mime_type = (
                uploaded_file.mimetype
                or "application/octet-stream"
            )

            saved_files.append(
                {
                    "original_name":
                        safe_original_name,

                    "stored_name":
                        stored_name,

                    "file_size":
                        file_size,

                    "mime_type":
                        mime_type,

                    "path":
                        file_path
                }
            )

        return saved_files

    except Exception:

        # حذف الملفات في حال فشل الحفظ
        if os.path.exists(
            order_folder
        ):

            for filename in os.listdir(
                order_folder
            ):

                file_path = os.path.join(
                    order_folder,
                    filename
                )

                try:

                    os.remove(
                        file_path
                    )

                except Exception:
                    pass

            try:

                os.rmdir(
                    order_folder
                )

            except Exception:
                pass

        raise


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# CREATE ORDER
# ============================================================

@app.route(
    "/order",
    methods=["POST"]
)
def order():

    # --------------------------------------------------------
    # Honeypot anti-bot
    # --------------------------------------------------------

    if request.form.get(
        "website",
        ""
    ).strip():

        return redirect(
            url_for("home")
        )

    # --------------------------------------------------------
    # Get form data
    # --------------------------------------------------------

    name = clean_text(
        request.form.get(
            "name"
        ),
        100
    )

    phone = clean_text(
        request.form.get(
            "phone"
        ),
        30
    )

    email = clean_text(
        request.form.get(
            "email"
        ),
        150
    )

    client_type = clean_text(
        request.form.get(
            "client_type",
            "مشهور"
        ),
        100
    )

    profile_name = clean_text(
        request.form.get(
            "profile_name"
        ),
        150
    )

    profile_link = clean_text(
        request.form.get(
            "profile_link"
        ),
        500
    )

    description = clean_text(
        request.form.get(
            "description"
        ),
        5000
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if not name:

        flash(
            "يرجى كتابة الاسم.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    if len(name) < 2:

        flash(
            "الاسم قصير جدًا.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    if not valid_phone(
        phone
    ):

        flash(
            "يرجى إدخال رقم هاتف صحيح.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    if email and not valid_email(
        email
    ):

        flash(
            "البريد الإلكتروني غير صحيح.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    if profile_link and not valid_url(
        profile_link
    ):

        flash(
            "رابط الحساب يجب أن يبدأ بـ https:// أو http://",
            "error"
        )

        return redirect(
            url_for("home")
        )

    if not description:

        flash(
            "يرجى كتابة تفاصيل المشروع.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    if len(description) < 10:

        flash(
            "يرجى كتابة تفاصيل أكثر عن المشروع.",
            "error"
        )

        return redirect(
            url_for("home")
        )

    # --------------------------------------------------------
    # Duplicate protection
    # --------------------------------------------------------

    request_hash = create_request_hash(
        name,
        phone,
        description
    )

    connection = get_db()

    existing = connection.execute(
        """
        SELECT order_id
        FROM orders
        WHERE request_hash = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (
            request_hash,
        )
    ).fetchone()

    connection.close()

    if existing:

        flash(
            f"هذا الطلب موجود مسبقًا. "
            f"رقم الطلب: #{existing['order_id']}",
            "error"
        )

        return redirect(
            url_for("home")
        )

    # --------------------------------------------------------
    # Files
    # --------------------------------------------------------

    uploaded_files = request.files.getlist(
        "files"
    )

    # --------------------------------------------------------
    # Generate order ID
    # --------------------------------------------------------

    order_id = generate_order_id()

    created_at = now_string()

    order_data = {

        "order_id":
            order_id,

        "name":
            name,

        "phone":
            phone,

        "email":
            email,

        "client_type":
            client_type,

        "profile_name":
            profile_name,

        "profile_link":
            profile_link,

        "description":
            description,

        "created_at":
            created_at
    }

    saved_files = []

    try:

        # ----------------------------------------------------
        # Save uploaded files
        # ----------------------------------------------------

        saved_files = save_uploaded_files(
            order_id,
            uploaded_files
        )

        # ----------------------------------------------------
        # Send email first
        # ----------------------------------------------------

        send_order_email(
            order_data,
            saved_files
        )

        # ----------------------------------------------------
        # Save order in database
        # ----------------------------------------------------

        connection = get_db()

        connection.execute(
            """
            INSERT INTO orders (
                order_id,
                name,
                phone,
                email,
                client_type,
                profile_name,
                profile_link,
                description,
                status,
                request_hash,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                order_id,
                name,
                phone,
                email,
                client_type,
                profile_name,
                profile_link,
                description,
                "new",
                request_hash,
                created_at,
                created_at
            )
        )

        # ----------------------------------------------------
        # Save file records
        # ----------------------------------------------------

        for file_info in saved_files:

            connection.execute(
                """
                INSERT INTO order_files (
                    order_id,
                    original_name,
                    stored_name,
                    file_size,
                    mime_type,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,

                    file_info[
                        "original_name"
                    ],

                    file_info[
                        "stored_name"
                    ],

                    file_info[
                        "file_size"
                    ],

                    file_info[
                        "mime_type"
                    ],

                    created_at
                )
            )

        connection.commit()

        connection.close()

        # ----------------------------------------------------
        # Save session hash
        # ----------------------------------------------------

        session[
            "last_request_hash"
        ] = request_hash

        flash(
            f"تم إرسال طلبك بنجاح ✓ "
            f"رقم الطلب: #{order_id}",
            "success"
        )

        return redirect(
            url_for("order_success")
        )

    except smtplib.SMTPAuthenticationError:

        print(
            "GMAIL ERROR: Authentication failed."
        )

        flash(
            "تعذر تسجيل الدخول إلى Gmail. "
            "تأكد من Gmail App Password.",
            "error"
        )

    except smtplib.SMTPException as error:

        print(
            "SMTP ERROR:",
            error
        )

        flash(
            "حدث خطأ أثناء إرسال البريد الإلكتروني.",
            "error"
        )

    except ValueError as error:

        print(
            "VALIDATION ERROR:",
            error
        )

        flash(
            str(error),
            "error"
        )

    except Exception as error:

        print(
            "ORDER ERROR:",
            error
        )

        flash(
            "حدث خطأ أثناء إرسال الطلب. حاول مرة أخرى.",
            "error"
        )

    return redirect(
        url_for("home")
    )


# ============================================================
# SUCCESS PAGE
# ============================================================

@app.route(
    "/order-success"
)
def order_success():

    return render_template(
        "success.html"
    )


# ============================================================
# ADMIN LOGIN
# ============================================================

@app.route(
    "/admin",
    methods=["GET", "POST"]
)
def admin_login():

    if session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for(
                "admin_dashboard"
            )
        )

    if request.method == "POST":

        password = request.form.get(
            "password",
            ""
        )

        if (
            password
            and password == ADMIN_PASSWORD
        ):

            session[
                "admin_logged_in"
            ] = True

            session.permanent = True

            return redirect(
                url_for(
                    "admin_dashboard"
                )
            )

        flash(
            "كلمة المرور غير صحيحة.",
            "error"
        )

    return render_template(
        "admin_login.html"
    )


# ============================================================
# ADMIN LOGOUT
# ============================================================

@app.route(
    "/admin/logout"
)
def admin_logout():

    session.pop(
        "admin_logged_in",
        None
    )

    return redirect(
        url_for(
            "admin_login"
        )
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route(
    "/admin/dashboard"
)
@admin_required
def admin_dashboard():

    search = clean_text(
        request.args.get(
            "search",
            ""
        ),
        100
    )

    status = clean_text(
        request.args.get(
            "status",
            ""
        ),
        50
    )

    connection = get_db()

    query = """
        SELECT *
        FROM orders
        WHERE 1=1
    """

    params = []

    if search:

        query += """
            AND (
                order_id LIKE ?
                OR name LIKE ?
                OR phone LIKE ?
                OR email LIKE ?
            )
        """

        search_value = (
            "%"
            + search
            + "%"
        )

        params.extend(
            [
                search_value,
                search_value,
                search_value,
                search_value
            ]
        )

    if status in ORDER_STATUSES:

        query += """
            AND status = ?
        """

        params.append(
            status
        )

    query += """
        ORDER BY id DESC
    """

    orders = connection.execute(
        query,
        params
    ).fetchall()

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    total_orders = connection.execute(
        """
        SELECT COUNT(*)
        FROM orders
        """
    ).fetchone()[0]

    new_orders = connection.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE status = 'new'
        """
    ).fetchone()[0]

    processing_orders = connection.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE status = 'processing'
        """
    ).fetchone()[0]

    completed_orders = connection.execute(
        """
        SELECT COUNT(*)
        FROM orders
        WHERE status = 'completed'
        """
    ).fetchone()[0]

    connection.close()

    return render_template(
        "admin_dashboard.html",

        orders=orders,

        search=search,

        status=status,

        statuses=ORDER_STATUSES,

        total_orders=total_orders,

        new_orders=new_orders,

        processing_orders=processing_orders,

        completed_orders=completed_orders
    )


# ============================================================
# ADMIN ORDER DETAILS
# ============================================================

@app.route(
    "/admin/order/<order_id>"
)
@admin_required
def admin_order(
    order_id
):

    connection = get_db()

    order_data = connection.execute(
        """
        SELECT *
        FROM orders
        WHERE order_id = ?
        """,
        (
            order_id,
        )
    ).fetchone()

    files = connection.execute(
        """
        SELECT *
        FROM order_files
        WHERE order_id = ?
        ORDER BY id ASC
        """,
        (
            order_id,
        )
    ).fetchall()

    connection.close()

    if not order_data:

        flash(
            "الطلب غير موجود.",
            "error"
        )

        return redirect(
            url_for(
                "admin_dashboard"
            )
        )

    return render_template(
        "admin_order.html",

        order=order_data,

        files=files,

        statuses=ORDER_STATUSES
    )


# ============================================================
# UPDATE ORDER STATUS
# ============================================================

@app.route(
    "/admin/order/<order_id>/status",
    methods=["POST"]
)
@admin_required
def update_order_status(
    order_id
):

    status = request.form.get(
        "status",
        ""
    ).strip()

    if status not in ORDER_STATUSES:

        flash(
            "حالة الطلب غير صحيحة.",
            "error"
        )

        return redirect(
            url_for(
                "admin_order",
                order_id=order_id
            )
        )

    connection = get_db()

    cursor = connection.execute(
        """
        UPDATE orders
        SET status = ?,
            updated_at = ?
        WHERE order_id = ?
        """,
        (
            status,
            now_string(),
            order_id
        )
    )

    connection.commit()

    connection.close()

    if cursor.rowcount == 0:

        flash(
            "الطلب غير موجود.",
            "error"
        )

    else:

        flash(
            "تم تحديث حالة الطلب ✓",
            "success"
        )

    return redirect(
        url_for(
            "admin_order",
            order_id=order_id
        )
    )


# ============================================================
# DOWNLOAD ORDER FILE
# ============================================================

@app.route(
    "/admin/file/<order_id>/<filename>"
)
@admin_required
def download_file(
    order_id,
    filename
):

    connection = get_db()

    file_record = connection.execute(
        """
        SELECT *
        FROM order_files
        WHERE order_id = ?
        AND stored_name = ?
        """,
        (
            order_id,
            filename
        )
    ).fetchone()

    connection.close()

    if not file_record:

        flash(
            "الملف غير موجود.",
            "error"
        )

        return redirect(
            url_for(
                "admin_dashboard"
            )
        )

    folder = os.path.join(
        UPLOAD_FOLDER,
        order_id
    )

    return send_from_directory(
        folder,
        filename,
        as_attachment=True,
        download_name=file_record[
            "original_name"
        ]
    )


# ============================================================
# DELETE ORDER
# ============================================================

@app.route(
    "/admin/order/<order_id>/delete",
    methods=["POST"]
)
@admin_required
def delete_order(
    order_id
):

    connection = get_db()

    files = connection.execute(
        """
        SELECT stored_name
        FROM order_files
        WHERE order_id = ?
        """,
        (
            order_id,
        )
    ).fetchall()

    order_exists = connection.execute(
        """
        SELECT id
        FROM orders
        WHERE order_id = ?
        """,
        (
            order_id,
        )
    ).fetchone()

    if not order_exists:

        connection.close()

        flash(
            "الطلب غير موجود.",
            "error"
        )

        return redirect(
            url_for(
                "admin_dashboard"
            )
        )

    # --------------------------------------------------------
    # Delete database records
    # --------------------------------------------------------

    connection.execute(
        """
        DELETE FROM order_files
        WHERE order_id = ?
        """,
        (
            order_id,
        )
    )

    connection.execute(
        """
        DELETE FROM orders
        WHERE order_id = ?
        """,
        (
            order_id,
        )
    )

    connection.commit()

    connection.close()

    # --------------------------------------------------------
    # Delete physical files
    # --------------------------------------------------------

    order_folder = os.path.join(
        UPLOAD_FOLDER,
        order_id
    )

    if os.path.exists(
        order_folder
    ):

        for file in files:

            stored_name = file[
                "stored_name"
            ]

            file_path = os.path.join(
                order_folder,
                stored_name
            )

            try:

                if os.path.exists(
                    file_path
                ):

                    os.remove(
                        file_path
                    )

            except Exception as error:

                print(
                    "FILE DELETE ERROR:",
                    error
                )

        try:

            os.rmdir(
                order_folder
            )

        except Exception:
            pass

    flash(
        f"تم حذف الطلب #{order_id}.",
        "success"
    )

    return redirect(
        url_for(
            "admin_dashboard"
        )
    )


# ============================================================
# SECURITY HEADERS
# ============================================================

@app.after_request
def security_headers(response):

    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    response.headers[
        "X-Frame-Options"
    ] = "SAMEORIGIN"

    response.headers[
        "Referrer-Policy"
    ] = "strict-origin-when-cross-origin"

    return response


# ============================================================
# FILE TOO LARGE
# ============================================================

@app.errorhandler(413)
def file_too_large(error):

    flash(
        "حجم الطلب كبير جدًا. الحد الأقصى 15MB.",
        "error"
    )

    return redirect(
        url_for("home")
    )


# ============================================================
# GENERAL ERROR
# ============================================================

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


# ============================================================
# INITIALIZE DATABASE
# ============================================================

init_database()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "5000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
