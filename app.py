from flask import (
    Flask,
    request,
    redirect,
    url_for,
    flash,
    session,
    render_template_string
)

from email.message import EmailMessage
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from datetime import datetime
from urllib.parse import urlparse

import smtplib
import ssl
import os
import uuid
import hashlib
import re


# =========================================================
# SHOVIX — ALL-IN-ONE APP
# ملف واحد فقط: app.py
# =========================================================

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "CHANGE_THIS_SECRET_KEY_IN_ENV"
)

# =========================================================
# SECURITY / CONFIG
# =========================================================

app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# إذا كان الموقع يعمل HTTPS فعّلها من .env:
# SESSION_COOKIE_SECURE=true
app.config["SESSION_COOKIE_SECURE"] = (
    os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
)

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp",
    "pdf"
}

MAX_FILES = 8


# =========================================================
# EMAIL SETTINGS
# =========================================================

OWNER_EMAIL = os.getenv("OWNER_EMAIL", "").strip()

GMAIL_APP_PASSWORD = os.getenv(
    "GMAIL_APP_PASSWORD",
    ""
).strip()


# =========================================================
# HTML
# =========================================================

HTML = r"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<meta name="theme-color" content="#0b0e14">

<meta name="description"
      content="SHOVIX — استوديو تصميم البروفايلات الاحترافية. نصمم هويتك الرقمية بطريقة فاخرة ومميزة.">

<title>SHOVIX — Premium Profile Studio</title>

<style>

:root{
    --bg:#080a0f;
    --panel:#10141c;
    --panel2:#151a24;
    --line:#242b38;

    --gold:#c9a227;
    --gold2:#e8c766;

    --white:#f5f3ec;

    --text:#c8cdd6;
    --muted:#7d8695;
    --muted2:#596171;

    --green:#49b47f;
    --red:#e15d54;

    --radius:16px;
}

*{
    box-sizing:border-box;
    margin:0;
    padding:0;
}

html{
    scroll-behavior:smooth;
}

body{
    background:
        radial-gradient(
            circle at 80% -10%,
            rgba(201,162,39,.16),
            transparent 35%
        ),
        radial-gradient(
            circle at 0% 30%,
            rgba(201,162,39,.07),
            transparent 30%
        ),
        var(--bg);

    color:var(--white);

    font-family:
        Arial,
        "Segoe UI",
        Tahoma,
        sans-serif;

    line-height:1.7;

    overflow-x:hidden;
}

body::before{
    content:"";
    position:fixed;
    inset:0;

    pointer-events:none;

    opacity:.025;

    background-image:
        linear-gradient(
            rgba(255,255,255,.5) 1px,
            transparent 1px
        ),
        linear-gradient(
            90deg,
            rgba(255,255,255,.5) 1px,
            transparent 1px
        );

    background-size:45px 45px;
}

a{
    color:inherit;
    text-decoration:none;
}

button,
input,
select,
textarea{
    font:inherit;
}

button{
    border:0;
}

::selection{
    background:var(--gold);
    color:var(--bg);
}

.container{
    width:min(1120px, calc(100% - 40px));
    margin:auto;
}


/* =========================================================
   NAVBAR
========================================================= */

header{
    position:sticky;
    top:0;
    z-index:100;

    background:rgba(8,10,15,.86);

    backdrop-filter:blur(18px);
    -webkit-backdrop-filter:blur(18px);

    border-bottom:1px solid rgba(255,255,255,.07);
}

.navbar{
    min-height:76px;

    display:flex;
    align-items:center;
    justify-content:space-between;

    gap:20px;
}

.logo{
    display:flex;
    align-items:center;
    gap:10px;

    font-size:23px;
    font-weight:900;

    letter-spacing:1px;
}

.logo-mark{
    width:30px;
    height:30px;

    display:flex;
    align-items:center;
    justify-content:center;

    border-radius:50%;

    color:var(--bg);

    background:
        linear-gradient(
            135deg,
            var(--gold2),
            var(--gold)
        );

    font-size:15px;
    font-weight:900;
}

.nav-links{
    display:flex;
    align-items:center;
    gap:30px;

    color:var(--muted);

    font-size:14px;
}

.nav-links a{
    transition:.2s ease;
}

.nav-links a:hover{
    color:var(--white);
}

.nav-button{
    background:var(--gold);
    color:var(--bg);

    padding:10px 20px;

    border-radius:999px;

    font-weight:800;
    font-size:14px;

    transition:.2s ease;
}

.nav-button:hover{
    background:var(--gold2);
    transform:translateY(-2px);
}


/* =========================================================
   FLASH
========================================================= */

.flash-container{
    position:fixed;

    top:92px;
    left:50%;

    transform:translateX(-50%);

    width:min(
        calc(100% - 30px),
        560px
    );

    z-index:500;

    display:flex;
    flex-direction:column;
    gap:10px;
}

.flash{
    padding:15px 18px;

    border-radius:13px;

    border:1px solid;

    backdrop-filter:blur(14px);

    box-shadow:
        0 20px 60px rgba(0,0,0,.4);

    font-size:14px;
}

.flash.success{
    background:rgba(73,180,127,.12);
    border-color:rgba(73,180,127,.4);
    color:#bdebd2;
}

.flash.error{
    background:rgba(225,93,84,.12);
    border-color:rgba(225,93,84,.4);
    color:#ffd0cc;
}


/* =========================================================
   HERO
========================================================= */

.hero{
    min-height:calc(100vh - 76px);

    display:grid;
    grid-template-columns:
        minmax(0,1.05fr)
        minmax(360px,.95fr);

    align-items:center;

    gap:70px;

    padding:80px 0;
}

.badge{
    display:inline-flex;
    align-items:center;
    gap:9px;

    padding:7px 14px;

    border-radius:999px;

    border:1px solid
        rgba(201,162,39,.3);

    background:
        rgba(201,162,39,.07);

    color:var(--gold2);

    font-size:12px;
    letter-spacing:1px;
}

.badge-dot{
    width:7px;
    height:7px;

    border-radius:50%;

    background:var(--gold2);

    box-shadow:
        0 0 14px var(--gold2);
}

.hero h1{
    margin-top:22px;

    font-size:
        clamp(
            38px,
            6vw,
            66px
        );

    line-height:1.15;

    font-weight:900;
}

.hero h1 span{
    color:var(--gold2);
}

.hero-description{
    max-width:650px;

    margin-top:22px;

    color:var(--muted);

    font-size:17px;
}

.hero-buttons{
    display:flex;
    flex-wrap:wrap;

    gap:12px;

    margin-top:32px;
}

.btn{
    display:inline-flex;

    align-items:center;
    justify-content:center;

    gap:9px;

    min-height:50px;

    padding:0 24px;

    border-radius:999px;

    font-weight:800;

    cursor:pointer;

    transition:.22s ease;
}

.btn-primary{
    background:var(--gold);
    color:var(--bg);
}

.btn-primary:hover{
    background:var(--gold2);
    transform:translateY(-2px);

    box-shadow:
        0 15px 40px
        rgba(201,162,39,.2);
}

.btn-secondary{
    border:1px solid var(--line);
    color:var(--white);

    background:rgba(255,255,255,.02);
}

.btn-secondary:hover{
    border-color:var(--gold);
    background:rgba(201,162,39,.06);
}

.stats{
    display:flex;
    flex-wrap:wrap;

    gap:30px;

    margin-top:45px;

    padding-top:28px;

    border-top:1px solid var(--line);
}

.stat strong{
    display:block;

    color:var(--gold2);

    font-size:24px;
}

.stat span{
    color:var(--muted2);

    font-size:12px;
}


/* =========================================================
   HERO CARD
========================================================= */

.visual{
    position:relative;

    min-height:480px;

    display:flex;

    align-items:center;
    justify-content:center;
}

.profile-card{
    width:min(330px, 90%);

    padding:30px 25px;

    border-radius:25px;

    background:
        linear-gradient(
            150deg,
            #1a202b,
            #0e1219
        );

    border:1px solid var(--line);

    box-shadow:
        0 45px 100px
        rgba(0,0,0,.65);

    transform:
        perspective(1000px)
        rotateY(-9deg)
        rotateX(5deg);

    transition:transform .15s ease;
}

.card-top{
    display:flex;
    align-items:flex-start;
    justify-content:space-between;
}

.avatar{
    width:68px;
    height:68px;

    display:flex;
    align-items:center;
    justify-content:center;

    border-radius:50%;

    background:
        conic-gradient(
            var(--gold2),
            var(--gold),
            #555,
            var(--gold2)
        );
}

.avatar-inner{
    width:59px;
    height:59px;

    display:flex;
    align-items:center;
    justify-content:center;

    border-radius:50%;

    background:var(--panel);

    color:var(--gold2);

    font-size:20px;
    font-weight:900;
}

.verified{
    padding:6px 10px;

    border-radius:999px;

    color:#9de2bd;

    border:1px solid
        rgba(73,180,127,.35);

    background:
        rgba(73,180,127,.08);

    font-size:11px;
}

.card-name{
    margin-top:17px;

    font-size:21px;
    font-weight:900;
}

.card-handle{
    color:var(--muted);

    font-size:13px;
}

.card-lines{
    display:flex;
    flex-direction:column;
    gap:10px;

    margin-top:25px;
}

.card-lines i{
    display:block;

    height:8px;

    border-radius:99px;

    background:var(--line);
}

.card-lines i:nth-child(2){
    width:75%;
}

.card-lines i:nth-child(3){
    width:55%;

    background:
        linear-gradient(
            90deg,
            var(--gold),
            transparent
        );
}

.card-metrics{
    display:grid;
    grid-template-columns:repeat(3,1fr);

    gap:10px;

    margin-top:25px;

    padding-top:18px;

    border-top:1px solid var(--line);
}

.card-metrics strong{
    display:block;

    font-size:14px;
}

.card-metrics span{
    color:var(--muted2);

    font-size:10px;
}

.float{
    position:absolute;

    padding:10px 14px;

    border-radius:12px;

    background:var(--panel);

    border:1px solid var(--line);

    box-shadow:
        0 20px 50px
        rgba(0,0,0,.5);

    color:var(--muted);

    font-size:12px;

    animation:float 5s ease-in-out infinite;
}

.float b{
    color:var(--gold2);
}

.float.one{
    top:12%;
    right:2%;
}

.float.two{
    bottom:12%;
    left:2%;

    animation-delay:1.2s;
}

@keyframes float{
    0%,100%{
        transform:translateY(0);
    }

    50%{
        transform:translateY(-10px);
    }
}


/* =========================================================
   SECTIONS
========================================================= */

section{
    scroll-margin-top:90px;
}

.section{
    padding:85px 0;

    border-top:1px solid var(--line);
}

.section-title{
    max-width:650px;

    margin-bottom:42px;
}

.section-title h2{
    margin-top:15px;

    font-size:
        clamp(
            28px,
            4vw,
            42px
        );

    line-height:1.2;
}

.section-title p{
    margin-top:12px;

    color:var(--muted);

    font-size:15px;
}


/* =========================================================
   STEPS
========================================================= */

.steps{
    display:grid;

    grid-template-columns:
        repeat(3,1fr);

    gap:20px;
}

.step{
    padding:28px;

    background:var(--panel);

    border:1px solid var(--line);

    border-radius:var(--radius);

    transition:.25s ease;
}

.step:hover{
    transform:translateY(-5px);

    border-color:
        rgba(201,162,39,.4);
}

.step-number{
    width:38px;
    height:38px;

    display:flex;
    align-items:center;
    justify-content:center;

    border-radius:50%;

    border:1px solid
        rgba(201,162,39,.35);

    color:var(--gold2);

    font-size:12px;
}

.step h3{
    margin-top:20px;

    font-size:19px;
}

.step p{
    margin-top:8px;

    color:var(--muted);

    font-size:14px;
}


/* =========================================================
   FEATURES
========================================================= */

.features{
    display:grid;

    grid-template-columns:
        repeat(4,1fr);

    gap:1px;

    overflow:hidden;

    border:1px solid var(--line);

    border-radius:var(--radius);

    background:var(--line);
}

.feature{
    padding:26px 20px;

    background:var(--panel);
}

.feature strong{
    display:block;

    font-size:15px;
}

.feature span{
    display:block;

    margin-top:6px;

    color:var(--muted2);

    font-size:12px;
}


/* =========================================================
   ORDER
========================================================= */

.order{
    padding:90px 0 110px;

    border-top:1px solid var(--line);
}

.order-box{
    display:grid;

    grid-template-columns:
        .75fr
        1.25fr;

    gap:40px;

    padding:42px;

    background:var(--panel);

    border:1px solid var(--line);

    border-radius:22px;

    position:relative;

    overflow:hidden;
}

.order-box::before{
    content:"";

    position:absolute;

    width:400px;
    height:400px;

    right:-180px;
    top:-220px;

    background:
        radial-gradient(
            circle,
            rgba(201,162,39,.12),
            transparent 65%
        );

    pointer-events:none;
}

.order-info{
    position:relative;
    z-index:1;
}

.order-info h2{
    margin-top:17px;

    font-size:30px;
}

.order-info p{
    margin-top:12px;

    color:var(--muted);

    font-size:14px;
}

.check-list{
    display:flex;

    flex-direction:column;

    gap:13px;

    margin-top:27px;

    list-style:none;
}

.check-list li{
    display:flex;

    gap:9px;

    color:var(--muted);

    font-size:13px;
}

.check{
    color:var(--gold2);
}


/* =========================================================
   FORM
========================================================= */

.order-form{
    position:relative;

    z-index:2;

    display:flex;

    flex-direction:column;

    gap:17px;
}

.form-row{
    display:grid;

    grid-template-columns:
        repeat(2,1fr);

    gap:15px;
}

.field label{
    display:block;

    margin-bottom:7px;

    color:var(--muted);

    font-size:13px;
}

.required{
    color:var(--gold2);
}

.field input,
.field select,
.field textarea{
    width:100%;

    border:1px solid var(--line);

    border-radius:11px;

    background:var(--panel2);

    color:var(--white);

    padding:13px 14px;

    outline:none;

    font-size:14px;

    transition:.2s ease;
}

.field input::placeholder,
.field textarea::placeholder{
    color:var(--muted2);
}

.field input:focus,
.field select:focus,
.field textarea:focus{
    border-color:var(--gold);

    background:#171c25;

    box-shadow:
        0 0 0 3px
        rgba(201,162,39,.06);
}

.field textarea{
    min-height:130px;

    resize:vertical;
}

.field select{
    cursor:pointer;
}

.file-box{
    position:relative;

    border:1px dashed #343d4c;

    border-radius:13px;

    padding:24px;

    text-align:center;

    transition:.2s ease;
}

.file-box:hover{
    border-color:var(--gold);

    background:
        rgba(201,162,39,.04);
}

.file-box input{
    position:absolute;

    inset:0;

    opacity:0;

    cursor:pointer;
}

.file-icon{
    color:var(--gold2);

    font-size:25px;
}

.file-title{
    margin-top:7px;

    color:var(--text);

    font-size:13px;
}

.file-hint{
    margin-top:4px;

    color:var(--muted2);

    font-size:11px;
}

.file-list{
    display:flex;

    flex-direction:column;

    gap:6px;

    margin-top:8px;
}

.file-item{
    display:flex;

    align-items:center;

    justify-content:space-between;

    gap:10px;

    padding:8px 10px;

    border:1px solid var(--line);

    border-radius:8px;

    background:var(--panel2);

    color:var(--muted);

    font-size:11px;
}

.submit{
    width:100%;

    min-height:52px;

    background:var(--gold);

    color:var(--bg);

    border-radius:11px;

    font-weight:900;

    cursor:pointer;

    transition:.2s ease;
}

.submit:hover{
    background:var(--gold2);

    transform:translateY(-1px);
}

.submit:disabled{
    opacity:.55;

    cursor:not-allowed;

    transform:none;
}


/* =========================================================
   FOOTER
========================================================= */

footer{
    border-top:1px solid var(--line);

    padding:30px 0;
}

.footer{
    display:flex;

    align-items:center;

    justify-content:space-between;

    gap:20px;

    flex-wrap:wrap;
}

.footer-text{
    color:var(--muted2);

    font-size:12px;
}


/* =========================================================
   MOBILE
========================================================= */

@media(max-width:900px){

    .hero{
        grid-template-columns:1fr;

        padding:
            60px 0
            70px;

        gap:30px;
    }

    .visual{
        min-height:400px;
    }

    .steps{
        grid-template-columns:1fr;
    }

    .features{
        grid-template-columns:
            repeat(2,1fr);
    }

    .order-box{
        grid-template-columns:1fr;

        padding:28px;
    }

}

@media(max-width:650px){

    .container{
        width:
            min(
                100% - 28px,
                1120px
            );
    }

    .navbar{
        min-height:68px;
    }

    .nav-links{
        display:none;
    }

    .nav-button{
        padding:9px 14px;

        font-size:12px;
    }

    .hero{
        padding-top:45px;
    }

    .hero h1{
        font-size:38px;
    }

    .hero-description{
        font-size:15px;
    }

    .hero-buttons{
        flex-direction:column;
    }

    .btn{
        width:100%;
    }

    .stats{
        gap:20px;
    }

    .visual{
        min-height:350px;
    }

    .profile-card{
        width:290px;

        transform:
            perspective(1000px)
            rotateY(-4deg)
            rotateX(2deg);
    }

    .float.one{
        right:-2px;
    }

    .float.two{
        left:-2px;
    }

    .section{
        padding:65px 0;
    }

    .features{
        grid-template-columns:1fr;
    }

    .form-row{
        grid-template-columns:1fr;
    }

    .order{
        padding:
            65px 0
            80px;
    }

    .order-box{
        padding:21px;

        border-radius:17px;
    }

    .order-info h2{
        font-size:25px;
    }

    .footer{
        flex-direction:column;

        align-items:flex-start;
    }

}

@media(max-width:400px){

    .hero h1{
        font-size:34px;
    }

    .profile-card{
        width:270px;
    }

    .float{
        font-size:10px;

        padding:8px 10px;
    }

}


/* =========================================================
   ACCESSIBILITY
========================================================= */

:focus-visible{
    outline:2px solid var(--gold2);

    outline-offset:3px;
}

</style>

</head>


<body>


<!-- =======================================================
     FLASH MESSAGES
======================================================== -->

{% with messages = get_flashed_messages(with_categories=true) %}

{% if messages %}

<div class="flash-container">

{% for category, message in messages %}

<div class="flash {{ category }}">
    {{ message }}
</div>

{% endfor %}

</div>

{% endif %}

{% endwith %}


<!-- =======================================================
     NAVBAR
======================================================== -->

<header>

<div class="navbar container">

<a href="#home" class="logo">

<span class="logo-mark">✓</span>

SHOVIX

</a>


<nav class="nav-links">

<a href="#home">الرئيسية</a>

<a href="#process">كيف نعمل</a>

<a href="#features">المميزات</a>

<a href="#order">اطلب الآن</a>

</nav>


<a href="#order" class="nav-button">
ابدأ مشروعك
</a>

</div>

</header>


<main>


<!-- =======================================================
     HERO
======================================================== -->

<section id="home">

<div class="hero container">


<div>

<div class="badge">

<span class="badge-dot"></span>

PREMIUM PROFILE STUDIO

</div>


<h1>

هويتك الرقمية

<span>
تستاهل الأفضل.
</span>

</h1>


<p class="hero-description">

SHOVIX يصمم لك صفحة بروفايل احترافية
تعكس هويتك وتجمع روابطك ومعلوماتك
في تجربة رقمية أنيقة وسريعة ومتجاوبة
مع الهاتف والكمبيوتر.

</p>


<div class="hero-buttons">

<a href="#order"
   class="btn btn-primary">

ابدأ طلبك الآن
↗

</a>


<a href="#process"
   class="btn btn-secondary">

كيف نعمل؟

</a>

</div>


<div class="stats">

<div class="stat">

<strong>01</strong>

<span>
هوية مخصصة
</span>

</div>


<div class="stat">

<strong>02</strong>

<span>
تصميم احترافي
</span>

</div>


<div class="stat">

<strong>03</strong>

<span>
متجاوب مع الهاتف
</span>

</div>

</div>

</div>


<!-- CARD -->

<div class="visual"
     id="visual">

<div class="float one">

✓ تصميم
<b>احترافي</b>

</div>


<div class="float two">

تجربة
<b>Mobile</b>

</div>


<div class="profile-card"
     id="profileCard">


<div class="card-top">

<div class="avatar">

<div class="avatar-inner">
SX
</div>

</div>


<div class="verified">

✓ موثّق

</div>

</div>


<div class="card-name">

بروفايل العميل

</div>


<div class="card-handle">

@your.profile

</div>


<div class="card-lines">

<i></i>
<i></i>
<i></i>

</div>


<div class="card-metrics">

<div>

<strong>
12.4K
</strong>

<span>
متابع
</span>

</div>


<div>

<strong>
98%
</strong>

<span>
تفاعل
</span>

</div>


<div>

<strong>
SX-01
</strong>

<span>
تصميم
</span>

</div>

</div>


</div>

</div>

</div>

</section>


<!-- =======================================================
     PROCESS
======================================================== -->

<section id="process"
         class="section">

<div class="container">


<div class="section-title">

<div class="badge">

<span class="badge-dot"></span>

آلية العمل

</div>


<h2>
من الطلب إلى التصميم
في 3 خطوات بسيطة
</h2>


<p>

عملية واضحة وسريعة.
أرسل التفاصيل، نجهز التصميم،
ثم نرسل لك النتيجة.

</p>

</div>


<div class="steps">


<div class="step">

<div class="step-number">
01
</div>

<h3>
أرسل التفاصيل
</h3>

<p>

اكتب معلوماتك وفكرة الصفحة
وأرفق الصور أو الملفات التي تريدها.

</p>

</div>


<div class="step">

<div class="step-number">
02
</div>

<h3>
نصمم صفحتك
</h3>

<p>

نحوّل فكرتك إلى تصميم احترافي
متناسب مع هويتك.

</p>

</div>


<div class="step">

<div class="step-number">
03
</div>

<h3>
تستلم النتيجة
</h3>

<p>

بعد مراجعة الطلب والتصميم،
نتواصل معك لإكمال المشروع.

</p>

</div>


</div>

</div>

</section>


<!-- =======================================================
     FEATURES
======================================================== -->

<section id="features"
         class="section">

<div class="container">


<div class="features">


<div class="feature">

<strong>
هوية مخصصة
</strong>

<span>
تصميم يناسبك وليس قالبًا عشوائيًا.
</span>

</div>


<div class="feature">

<strong>
متجاوب
</strong>

<span>
يعمل بشكل ممتاز على الهاتف والكمبيوتر.
</span>

</div>


<div class="feature">

<strong>
تصميم فاخر
</strong>

<span>
واجهة عصرية ومرتبة وسريعة.
</span>

</div>


<div class="feature">

<strong>
طلب مباشر
</strong>

<span>
أرسل طلبك من الموقع مباشرة.
</span>

</div>


</div>

</div>

</section>


<!-- =======================================================
     ORDER
======================================================== -->

<section id="order"
         class="order">

<div class="container">


<div class="order-box">


<div class="order-info">


<div class="badge">

<span class="badge-dot"></span>

طلب تصميم جديد

</div>


<h2>
جهّز بياناتك
ونبدأ مشروعك
</h2>


<p>

املأ النموذج وسيتلقى فريق SHOVIX
طلبك مباشرة لمراجعته والتواصل معك.

</p>


<ul class="check-list">

<li>

<span class="check">✓</span>

بياناتك تستخدم لمعالجة الطلب فقط.

</li>


<li>

<span class="check">✓</span>

يمكنك إرفاق صور وملفات مرجعية.

</li>


<li>

<span class="check">✓</span>

يتم إنشاء رقم طلب خاص بك.

</li>


<li>

<span class="check">✓</span>

الحد الأقصى لحجم الملفات 15MB.

</li>

</ul>

</div>


<!-- =====================================================
     FORM
===================================================== -->

<form
    class="order-form"
    id="orderForm"
    action="{{ url_for('order') }}"
    method="POST"
    enctype="multipart/form-data"
>


<div class="form-row">


<div class="field">

<label for="name">

الاسم الكامل

<span class="required">*</span>

</label>


<input
    id="name"
    name="name"
    type="text"
    maxlength="80"
    autocomplete="name"
    placeholder="اسمك الكامل"
    required
>

</div>


<div class="field">

<label for="phone">

رقم الهاتف

<span class="required">*</span>

</label>


<input
    id="phone"
    name="phone"
    type="tel"
    maxlength="30"
    autocomplete="tel"
    placeholder="+972..."
    required
>

</div>

</div>


<div class="form-row">


<div class="field">

<label for="email">
البريد الإلكتروني
</label>


<input
    id="email"
    name="email"
    type="email"
    maxlength="120"
    autocomplete="email"
    placeholder="example@gmail.com"
>

</div>


<div class="field">

<label for="client_type">
نوع الحساب
</label>


<select
    id="client_type"
    name="client_type"
>

<option value="مشهور">
مشهور / صانع محتوى
</option>

<option value="تجاري">
حساب تجاري
</option>

<option value="شخصي">
حساب شخصي
</option>

<option value="علامة شخصية">
علامة شخصية
</option>

<option value="أخرى">
أخرى
</option>

</select>

</div>

</div>


<div class="form-row">


<div class="field">

<label for="profile_name">
اسم الشهرة / البروفايل
</label>


<input
    id="profile_name"
    name="profile_name"
    type="text"
    maxlength="100"
    placeholder="اسم البروفايل"
>

</div>


<div class="field">

<label for="profile_link">
رابط الحساب
</label>


<input
    id="profile_link"
    name="profile_link"
    type="url"
    maxlength="300"
    placeholder="https://..."
>

</div>

</div>


<div class="field">

<label for="description">

تفاصيل المشروع

<span class="required">*</span>

</label>


<textarea
    id="description"
    name="description"
    maxlength="5000"
    placeholder="اكتب فكرتك، الألوان المفضلة، الروابط التي تريد إضافتها وأي تفاصيل مهمة..."
    required
></textarea>

</div>


<div class="field">

<label>
الصور والملفات — اختياري
</label>


<div class="file-box"
     id="dropzone">


<input
    id="files"
    name="files"
    type="file"
    multiple
    accept=".png,.jpg,.jpeg,.webp,.pdf"
>


<div class="file-icon">
↑
</div>


<div class="file-title">

اضغط لاختيار الملفات
أو اسحبها هنا

</div>


<div class="file-hint">

PNG / JPG / WEBP / PDF
— حتى 15MB إجمالًا

</div>

</div>


<div
    class="file-list"
    id="fileList"
></div>

</div>


<button
    class="submit"
    id="submitBtn"
    type="submit"
>

✦ إرسال طلب التصميم

</button>


</form>


</div>

</div>

</section>


</main>


<!-- =======================================================
     FOOTER
======================================================== -->

<footer>

<div class="footer container">


<div class="logo">

<span class="logo-mark">
✓
</span>

SHOVIX

</div>


<div class="footer-text">

© <span id="year"></span>
SHOVIX — جميع الحقوق محفوظة.

</div>

</div>

</footer>


<script>


/* =========================================================
   YEAR
========================================================= */

document.getElementById("year").textContent =
    new Date().getFullYear();


/* =========================================================
   PROFILE CARD EFFECT
========================================================= */

(function(){

    const visual =
        document.getElementById("visual");

    const card =
        document.getElementById("profileCard");

    if(!visual || !card){
        return;
    }

    const reduceMotion =
        window.matchMedia(
            "(prefers-reduced-motion: reduce)"
        ).matches;

    if(reduceMotion){
        return;
    }

    visual.addEventListener(
        "mousemove",
        function(event){

            const rect =
                visual.getBoundingClientRect();

            const x =
                (event.clientX - rect.left)
                / rect.width - 0.5;

            const y =
                (event.clientY - rect.top)
                / rect.height - 0.5;

            card.style.transform =
                "perspective(1000px)" +
                " rotateY(" +
                (-9 - x * 12) +
                "deg)" +
                " rotateX(" +
                (5 + y * 8) +
                "deg)";

        }
    );

    visual.addEventListener(
        "mouseleave",
        function(){

            card.style.transform =
                "perspective(1000px)" +
                " rotateY(-9deg)" +
                " rotateX(5deg)";

        }
    );

})();


/* =========================================================
   FILE VALIDATION / DISPLAY
========================================================= */

(function(){

    const input =
        document.getElementById("files");

    const list =
        document.getElementById("fileList");

    const dropzone =
        document.getElementById("dropzone");

    if(!input || !list){
        return;
    }

    const allowed = [
        "png",
        "jpg",
        "jpeg",
        "webp",
        "pdf"
    ];

    const maxTotal =
        15 * 1024 * 1024;

    function render(){

        list.innerHTML = "";

        let total = 0;

        const files =
            Array.from(input.files || []);

        files.forEach(function(file){

            total += file.size;

            const item =
                document.createElement("div");

            item.className =
                "file-item";

            const size =
                file.size < 1024 * 1024
                ? (file.size / 1024).toFixed(0) + " KB"
                : (file.size / 1024 / 1024).toFixed(2) + " MB";

            item.innerHTML =
                "<span>" +
                escapeHTML(file.name) +
                "</span>" +
                "<span>" +
                size +
                "</span>";

            list.appendChild(item);

        });

        if(files.length > 8){

            list.innerHTML +=
                '<div class="file-item">' +
                '<span>الحد الأقصى 8 ملفات</span>' +
                '</div>';

        }

        if(total > maxTotal){

            list.innerHTML +=
                '<div class="file-item">' +
                '<span>حجم الملفات يتجاوز 15MB</span>' +
                '</div>';

        }

    }


    function escapeHTML(text){

        return String(text)
            .replace(/&/g,"&amp;")
            .replace(/</g,"&lt;")
            .replace(/>/g,"&gt;")
            .replace(/"/g,"&quot;")
            .replace(/'/g,"&#039;");

    }


    input.addEventListener(
        "change",
        render
    );


    if(dropzone){

        ["dragenter","dragover"]
        .forEach(function(eventName){

            dropzone.addEventListener(
                eventName,
                function(event){

                    event.preventDefault();

                    dropzone.style.borderColor =
                        "var(--gold)";

                }
            );

        });


        ["dragleave","drop"]
        .forEach(function(eventName){

            dropzone.addEventListener(
                eventName,
                function(event){

                    event.preventDefault();

                    dropzone.style.borderColor =
                        "#343d4c";

                }
            );

        });


        dropzone.addEventListener(
            "drop",
            function(event){

                if(
                    event.dataTransfer &&
                    event.dataTransfer.files.length
                ){

                    input.files =
                        event.dataTransfer.files;

                    render();

                }

            }
        );

    }

})();


/* =========================================================
   FORM SUBMIT UX
========================================================= */

(function(){

    const form =
        document.getElementById("orderForm");

    const button =
        document.getElementById("submitBtn");

    if(!form || !button){
        return;
    }

    form.addEventListener(
        "submit",
        function(){

            if(!form.checkValidity()){
                return;
            }

            button.disabled = true;

            button.textContent =
                "جاري إرسال الطلب...";

        }
    );

})();


/* =========================================================
   FLASH AUTO HIDE
========================================================= */

setTimeout(
    function(){

        const flashes =
            document.querySelectorAll(".flash");

        flashes.forEach(
            function(element){

                element.style.transition =
                    "opacity .5s ease";

                element.style.opacity = "0";

                setTimeout(
                    function(){
                        element.remove();
                    },
                    500
                );

            }
        );

    },
    7000
);


</script>

</body>
</html>
"""


# =========================================================
# HELPERS
# =========================================================

def allowed_file(filename):
    """
    التأكد من امتداد الملف.
    """

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return extension in ALLOWED_EXTENSIONS


def valid_email(email):
    """
    فحص بسيط للبريد الإلكتروني.
    """

    if not email:
        return True

    pattern = (
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )

    return bool(
        re.match(
            pattern,
            email
        )
    )


def valid_url(value):
    """
    يسمح بروابط HTTP/HTTPS فقط.
    """

    if not value:
        return True

    try:

        parsed = urlparse(value)

        return parsed.scheme in (
            "http",
            "https"
        ) and bool(parsed.netloc)

    except Exception:
        return False


def create_request_hash(
    name,
    phone,
    description
):
    """
    إنشاء بصمة للطلب لمنع التكرار
    داخل نفس Session.
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

def send_order_email(
    data,
    files
):

    if not OWNER_EMAIL:

        raise RuntimeError(
            "OWNER_EMAIL غير موجود."
        )

    if not GMAIL_APP_PASSWORD:

        raise RuntimeError(
            "GMAIL_APP_PASSWORD غير موجود."
        )


    order_id = (
        str(uuid.uuid4())
        .replace("-", "")
        [:8]
        .upper()
    )


    message = EmailMessage()


    message["Subject"] = (
        f"SHOVIX | طلب #{order_id} | "
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

طلب تصميم جديد

رقم الطلب:
#{order_id}

وقت الطلب:
{now}

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
{data.get("client_type") or "غير محدد"}

اسم البروفايل:
{data.get("profile_name") or "غير محدد"}

رابط الحساب:
{data.get("profile_link") or "غير محدد"}

----------------------------------------
تفاصيل المشروع
----------------------------------------

{data["description"]}

========================================
SHOVIX
Professional Profile Studio
"""


    message.set_content(body)


    # =====================================================
    # ATTACHMENTS
    # =====================================================

    attachment_count = 0

    for file in files:

        if not file:
            continue

        if not file.filename:
            continue

        if attachment_count >= MAX_FILES:
            break

        if not allowed_file(
            file.filename
        ):
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

            "png":
                ("image", "png"),

            "jpg":
                ("image", "jpeg"),

            "jpeg":
                ("image", "jpeg"),

            "webp":
                ("image", "webp"),

            "pdf":
                ("application", "pdf")
        }


        maintype, subtype = (
            mime_types.get(
                extension,
                (
                    "application",
                    "octet-stream"
                )
            )
        )


        message.add_attachment(
            file_data,
            maintype=maintype,
            subtype=subtype,
            filename=filename
        )


        attachment_count += 1


    # =====================================================
    # GMAIL SMTP
    # =====================================================

    context = ssl.create_default_context()


    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465,
        context=context,
        timeout=30
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

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return render_template_string(
        HTML
    )


# =========================================================
# ORDER
#
# GET  -> redirect
# POST -> process
#
# هذا يمنع مشكلة 405 عند فتح /order مباشرة.
# =========================================================

@app.route(
    "/order",
    methods=["GET", "POST"]
)
def order():

    if request.method == "GET":

        return redirect(
            url_for("home")
        )


    # =====================================================
    # FORM DATA
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
    # BASIC VALIDATION
    # =====================================================

    if not name:

        flash(
            "يرجى كتابة الاسم.",
            "error"
        )

        return redirect(
            url_for("home")
        )


    if len(name) > 80:

        flash(
            "الاسم طويل جدًا.",
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


    if len(phone) > 30:

        flash(
            "رقم الهاتف غير صالح.",
            "error"
        )

        return redirect(
            url_for("home")
        )


    if email and not valid_email(
        email
    ):

        flash(
            "البريد الإلكتروني غير صالح.",
            "error"
        )

        return redirect(
            url_for("home")
        )


    if profile_link and not valid_url(
        profile_link
    ):

        flash(
            "رابط الحساب يجب أن يبدأ بـ http أو https.",
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


    if len(description) > 5000:

        flash(
            "تفاصيل المشروع طويلة جدًا.",
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


    if len(files) > MAX_FILES:

        flash(
            f"يمكنك إرفاق {MAX_FILES} ملفات كحد أقصى.",
            "error"
        )

        return redirect(
            url_for("home")
        )


    total_size = 0


    for file in files:

        if not file:
            continue

        if not file.filename:
            continue


        if not allowed_file(
            file.filename
        ):

            flash(
                "يوجد ملف غير مسموح به. المسموح: PNG, JPG, WEBP, PDF.",
                "error"
            )

            return redirect(
                url_for("home")
            )


        # لا نقرأ الملف هنا.
        # Flask سيطبق MAX_CONTENT_LENGTH
        # على الطلب بالكامل.


    # =====================================================
    # SEND
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


        session[
            "last_request_hash"
        ] = request_hash


        flash(
            f"تم إرسال طلبك بنجاح ✓ رقم الطلب: #{order_id}",
            "success"
        )


    except smtplib.SMTPAuthenticationError:

        print(
            "SHOVIX ERROR: Gmail authentication failed."
        )

        flash(
            "تعذر الاتصال بالبريد. تحقق من Gmail App Password.",
            "error"
        )


    except smtplib.SMTPException as error:

        print(
            "SHOVIX SMTP ERROR:",
            error
        )

        flash(
            "حدث خطأ في اتصال البريد. حاول مرة أخرى.",
            "error"
        )


    except Exception as error:

        print(
            "SHOVIX ORDER ERROR:",
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
# 413 — FILE TOO LARGE
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
# 404
# =========================================================

@app.errorhandler(404)
def not_found(error):

    return redirect(
        url_for("home")
    )


# =========================================================
# 405
# =========================================================

@app.errorhandler(405)
def method_not_allowed(error):

    flash(
        "طريقة الطلب غير مسموحة.",
        "error"
    )

    return redirect(
        url_for("home")
    )


# =========================================================
# 500
# =========================================================

@app.errorhandler(500)
def internal_error(error):

    print(
        "SHOVIX SERVER ERROR:",
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
            "5000"
        )
    )


    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
