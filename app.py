from flask import Flask, request, redirect, url_for, flash, session, render_template_string
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
# SHOVIX — PREMIUM PROFILE STUDIO
# Single File Version — Hardened
# =========================================================

load_dotenv()

app = Flask(__name__)

# ---------------------------------------------------------
# SECRET_KEY: إجباري من .env — بدون قيمة افتراضية
# لأن أي مفتاح ثابت مكتوب في الكود المصدري نفسه يضعف
# تشفير الـ session بشكل خطير لو الكود بقى معروف/عام.
# ---------------------------------------------------------
app.secret_key = os.getenv("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError(
        "SECRET_KEY غير موجود في ملف .env — أضِفه قبل تشغيل السيرفر.\n"
        "ولّده بالأمر: python3 -c \"import secrets; print(secrets.token_hex(32))\""
    )

# =========================================================
# EMAIL
# =========================================================

OWNER_EMAIL = os.getenv("OWNER_EMAIL", "").strip()

# Gmail App Password أحيانًا بييجي بمسافات (abcd efgh ijkl mnop)
# لازم نشيلها عشان الـ SMTP login ينجح مهما كانت الطريقة اللي
# المستخدم لصق بيها الباسورد في .env
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "").strip()

if not OWNER_EMAIL:
    print("⚠️  تحذير: OWNER_EMAIL غير موجود في .env — الإرسال هيفشل عند أول طلب.")

if not GMAIL_APP_PASSWORD:
    print("⚠️  تحذير: GMAIL_APP_PASSWORD غير موجود في .env — الإرسال هيفشل عند أول طلب.")

# =========================================================
# UPLOAD
# =========================================================

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp",
    "pdf"
}

MAX_FILE_SIZE = 15 * 1024 * 1024

app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


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

<title>SHOVIX — استوديو تصميم البروفايلات الاحترافية</title>

<meta name="description"
      content="SHOVIX — تصميم صفحات بروفايل احترافية ومميزة تعكس هويتك الرقمية.">

<link rel="preconnect"
      href="https://fonts.googleapis.com">

<link rel="preconnect"
      href="https://fonts.gstatic.com"
      crossorigin>

<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@500;600;700;800;900&family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap"
      rel="stylesheet">

<style>

:root{

    --bg:#080a0f;
    --panel:#10141c;
    --panel2:#151a23;
    --line:#242b38;

    --gold:#c9a227;
    --gold2:#e8c766;

    --white:#f5f3ec;

    --muted:#8c95a5;
    --muted2:#5e6777;

    --success:#4caf7d;
    --danger:#df5b51;

    --display:'Cairo',sans-serif;
    --body:'IBM Plex Sans Arabic',sans-serif;
    --mono:'JetBrains Mono',monospace;

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

    min-height:100vh;

    background:

        radial-gradient(
            circle at 85% -10%,
            rgba(201,162,39,.16),
            transparent 42%
        ),

        radial-gradient(
            circle at 0% 35%,
            rgba(201,162,39,.07),
            transparent 38%
        ),

        var(--bg);

    color:var(--white);

    font-family:var(--body);

    line-height:1.7;

    overflow-x:hidden;
}

body::before{

    content:"";

    position:fixed;

    inset:0;

    pointer-events:none;

    opacity:.22;

    background-image:

        linear-gradient(
            rgba(255,255,255,.025) 1px,
            transparent 1px
        ),

        linear-gradient(
            90deg,
            rgba(255,255,255,.025) 1px,
            transparent 1px
        );

    background-size:50px 50px;

    mask-image:linear-gradient(
        to bottom,
        black,
        transparent 85%
    );
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

::selection{
    background:var(--gold);
    color:var(--bg);
}

.wrap{

    width:min(1120px, calc(100% - 40px));

    margin:auto;
}

/* focus visibility */
a:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible{
    outline:2px solid var(--gold2);
    outline-offset:3px;
}


/* =========================================================
   NAVBAR
========================================================= */

header{

    position:sticky;

    top:0;

    z-index:100;

    background:rgba(8,10,15,.84);

    backdrop-filter:blur(18px);

    border-bottom:1px solid var(--line);
}

.nav{

    min-height:74px;

    display:flex;

    align-items:center;

    justify-content:space-between;

    gap:25px;
}

.brand{

    display:flex;

    align-items:center;

    gap:10px;

    font-family:var(--display);

    font-weight:900;

    font-size:21px;

    letter-spacing:.5px;
}

.badge{

    width:30px;

    height:30px;

    display:grid;

    place-items:center;

    border-radius:50%;

    background:
        linear-gradient(
            135deg,
            var(--gold2),
            var(--gold)
        );

    box-shadow:
        0 0 30px rgba(201,162,39,.2);
}

.badge svg{
    width:15px;
}

.nav-links{

    display:flex;

    gap:30px;

    color:var(--muted);

    font-size:14px;
}

.nav-links a{

    transition:.2s;
}

.nav-links a:hover{
    color:var(--white);
}

.nav-cta{

    padding:10px 20px;

    border-radius:999px;

    background:var(--gold);

    color:var(--bg);

    font-weight:800;

    font-size:14px;

    transition:.2s;
}

.nav-cta:hover{

    background:var(--gold2);

    transform:translateY(-2px);
}

@media(max-width:760px){

    .nav-links{
        display:none;
    }

    .nav{
        padding:0 5px;
    }
}


/* =========================================================
   HERO
========================================================= */

.hero{

    min-height:650px;

    display:grid;

    grid-template-columns:1.05fr .95fr;

    align-items:center;

    gap:70px;

    padding-top:70px;

    padding-bottom:80px;
}

.eyebrow{

    display:inline-flex;

    align-items:center;

    gap:9px;

    padding:7px 14px;

    border-radius:999px;

    border:1px solid rgba(201,162,39,.3);

    background:rgba(201,162,39,.07);

    color:var(--gold2);

    font-family:var(--mono);

    font-size:11px;

    letter-spacing:1px;
}

.dot{

    width:7px;

    height:7px;

    border-radius:50%;

    background:var(--gold2);

    box-shadow:
        0 0 12px var(--gold);
}

.hero h1{

    margin-top:23px;

    max-width:700px;

    font-family:var(--display);

    font-size:clamp(38px,5.5vw,64px);

    line-height:1.16;

    font-weight:900;
}

.hero h1 span{
    color:var(--gold2);
}

.lead{

    max-width:590px;

    margin-top:22px;

    color:var(--muted);

    font-size:17px;
}

.actions{

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

    padding:14px 25px;

    border-radius:999px;

    cursor:pointer;

    font-weight:800;

    transition:.2s;
}

.btn-primary{

    background:var(--gold);

    color:var(--bg);

    border:1px solid var(--gold);
}

.btn-primary:hover{

    background:var(--gold2);

    transform:translateY(-2px);

    box-shadow:
        0 15px 40px rgba(201,162,39,.2);
}

.btn-secondary{

    border:1px solid var(--line);

    color:var(--white);

    background:rgba(255,255,255,.02);
}

.btn-secondary:hover{

    border-color:var(--gold);

    background:rgba(201,162,39,.05);
}

.stats{

    display:flex;

    gap:35px;

    margin-top:45px;

    padding-top:25px;

    border-top:1px solid var(--line);
}

.stat strong{

    display:block;

    font-family:var(--mono);

    color:var(--gold2);

    font-size:20px;
}

.stat span{

    display:block;

    color:var(--muted2);

    font-size:12px;

    margin-top:3px;
}


/* =========================================================
   PROFILE CARD
========================================================= */

.stage{

    min-height:460px;

    position:relative;

    display:grid;

    place-items:center;

    perspective:1200px;
}

.profile-card{

    width:310px;

    padding:28px;

    border-radius:24px;

    border:1px solid var(--line);

    background:
        linear-gradient(
            155deg,
            #191f2a,
            #10141c
        );

    box-shadow:
        0 50px 100px rgba(0,0,0,.55);

    transform:
        rotateY(-10deg)
        rotateX(6deg);

    transition:
        transform .2s ease;
}

.card-top{

    display:flex;

    justify-content:space-between;

    align-items:flex-start;
}

.avatar{

    width:65px;

    height:65px;

    border-radius:50%;

    padding:4px;

    background:
        conic-gradient(
            var(--gold2),
            var(--gold),
            #687080,
            var(--gold2)
        );
}

.avatar-inner{

    width:100%;

    height:100%;

    display:grid;

    place-items:center;

    border-radius:50%;

    background:var(--panel);

    color:var(--gold2);

    font-family:var(--display);

    font-weight:900;

    font-size:19px;
}

.verified{

    display:flex;

    align-items:center;

    gap:6px;

    padding:5px 9px;

    border-radius:999px;

    border:1px solid rgba(76,174,125,.35);

    background:rgba(76,174,125,.08);

    color:#8bd8b0;

    font-family:var(--mono);

    font-size:9px;
}

.profile-name{

    margin-top:18px;

    font-family:var(--display);

    font-size:20px;

    font-weight:900;
}

.handle{

    color:var(--muted);

    font-size:13px;
}

.lines{

    margin-top:25px;

    display:grid;

    gap:9px;
}

.lines i{

    height:8px;

    border-radius:20px;

    background:var(--line);
}

.lines i:nth-child(1){
    width:100%;
}

.lines i:nth-child(2){
    width:78%;
}

.lines i:nth-child(3){

    width:54%;

    background:
        linear-gradient(
            90deg,
            var(--gold),
            transparent
        );
}

.metrics{

    display:grid;

    grid-template-columns:repeat(3,1fr);

    gap:10px;

    margin-top:25px;

    padding-top:18px;

    border-top:1px solid var(--line);
}

.metrics b{

    display:block;

    font-family:var(--mono);

    font-size:13px;
}

.metrics span{

    color:var(--muted2);

    font-size:10px;
}

.float{

    position:absolute;

    padding:10px 14px;

    border-radius:12px;

    border:1px solid var(--line);

    background:var(--panel2);

    color:var(--muted);

    font-size:12px;

    box-shadow:0 20px 50px rgba(0,0,0,.4);

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

    bottom:10%;

    left:0;

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

@media(prefers-reduced-motion: reduce){
    .float{ animation:none; }
    html{ scroll-behavior:auto; }
}

@media(max-width:900px){

    .hero{

        grid-template-columns:1fr;

        gap:20px;

        padding-top:50px;
    }

    .stage{
        min-height:430px;
    }
}


/* =========================================================
   SECTIONS
========================================================= */

.section{

    padding:80px 0;

    border-top:1px solid var(--line);
}

.section-head{

    max-width:600px;

    margin-bottom:42px;
}

.section-head h2{

    margin-top:15px;

    font-family:var(--display);

    font-weight:900;

    font-size:clamp(28px,4vw,40px);

    line-height:1.3;
}

.section-head p{

    margin-top:10px;

    color:var(--muted);

    font-size:15px;
}


/* =========================================================
   STEPS
========================================================= */

.steps{

    display:grid;

    grid-template-columns:repeat(3,1fr);

    gap:18px;
}

.step{

    position:relative;

    overflow:hidden;

    padding:28px;

    border:1px solid var(--line);

    border-radius:var(--radius);

    background:var(--panel);

    transition:.25s;
}

.step:hover{

    transform:translateY(-5px);

    border-color:rgba(201,162,39,.4);
}

.number{

    width:36px;

    height:36px;

    display:grid;

    place-items:center;

    margin-bottom:18px;

    border:1px solid rgba(201,162,39,.4);

    border-radius:50%;

    color:var(--gold2);

    font-family:var(--mono);

    font-size:12px;
}

.step h3{

    font-family:var(--display);

    font-size:19px;

    margin-bottom:8px;
}

.step p{

    color:var(--muted);

    font-size:14px;
}

@media(max-width:800px){

    .steps{
        grid-template-columns:1fr;
    }
}


/* =========================================================
   FEATURES
========================================================= */

.features{

    display:grid;

    grid-template-columns:repeat(4,1fr);

    gap:1px;

    background:var(--line);

    border:1px solid var(--line);

    border-radius:var(--radius);

    overflow:hidden;
}

.feature{

    padding:25px;

    background:var(--panel);
}

.feature strong{

    display:block;

    font-family:var(--display);

    font-size:15px;

    margin-bottom:5px;
}

.feature span{

    color:var(--muted2);

    font-size:12.5px;
}

@media(max-width:850px){

    .features{
        grid-template-columns:repeat(2,1fr);
    }
}

@media(max-width:500px){

    .features{
        grid-template-columns:1fr;
    }
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

    grid-template-columns:.8fr 1.2fr;

    gap:45px;

    padding:45px;

    border-radius:22px;

    border:1px solid var(--line);

    background:var(--panel);

    position:relative;

    overflow:hidden;
}

.order-box::before{

    content:"";

    position:absolute;

    width:500px;

    height:500px;

    top:-300px;

    right:-200px;

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

    margin-top:16px;

    font-family:var(--display);

    font-weight:900;

    font-size:30px;
}

.order-info p{

    margin-top:13px;

    color:var(--muted);

    font-size:14px;
}

.checks{

    display:grid;

    gap:14px;

    margin-top:28px;

    list-style:none;
}

.checks li{

    display:flex;

    align-items:flex-start;

    gap:10px;

    color:var(--muted);

    font-size:13.5px;
}

.check{

    flex-shrink:0;

    color:var(--gold2);
}


/* =========================================================
   FORM
========================================================= */

.order-form{

    position:relative;

    z-index:2;

    display:grid;

    gap:17px;
}

.form-row{

    display:grid;

    grid-template-columns:1fr 1fr;

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

    padding:13px 14px;

    border:1px solid var(--line);

    border-radius:10px;

    background:var(--panel2);

    color:var(--white);

    outline:none;

    transition:.2s;
}

.field textarea{

    min-height:130px;

    resize:vertical;
}

.field input::placeholder,
.field textarea::placeholder{

    color:var(--muted2);
}

.field input:focus,
.field select:focus,
.field textarea:focus{

    border-color:var(--gold);

    background:#181d27;

    box-shadow:
        0 0 0 3px rgba(201,162,39,.06);
}

.dropzone{

    position:relative;

    padding:25px;

    text-align:center;

    border:1.5px dashed var(--line);

    border-radius:12px;

    cursor:pointer;

    background:rgba(255,255,255,.01);

    transition:.2s;
}

.dropzone:hover,
.dropzone.drag{

    border-color:var(--gold);

    background:rgba(201,162,39,.04);
}

.dropzone input{

    position:absolute;

    inset:0;

    width:100%;

    height:100%;

    opacity:0;

    cursor:pointer;
}

.upload-icon{

    font-size:25px;

    color:var(--gold2);
}

.upload-text{

    margin-top:7px;

    color:var(--muted);

    font-size:13px;
}

.upload-text b{
    color:var(--gold2);
}

.upload-hint{

    color:var(--muted2);

    font-size:11px;

    margin-top:5px;
}

.files-list{

    display:grid;

    gap:6px;

    margin-top:8px;
}

.file-item{

    display:flex;

    justify-content:space-between;

    gap:10px;

    padding:8px 11px;

    border-radius:8px;

    background:var(--panel2);

    border:1px solid var(--line);

    color:var(--muted);

    font-family:var(--mono);

    font-size:10px;
}

.submit{

    display:flex;

    align-items:center;

    gap:15px;

    flex-wrap:wrap;

    margin-top:5px;
}

.submit button{

    border:0;

    min-width:170px;

    padding:14px 22px;

    border-radius:999px;

    background:var(--gold);

    color:var(--bg);

    cursor:pointer;

    font-weight:900;

    transition:.2s;
}

.submit button:hover{

    background:var(--gold2);

    transform:translateY(-2px);
}

.submit button:disabled{

    opacity:.55;

    cursor:not-allowed;

    transform:none;
}

.submit-note{

    color:var(--muted2);

    font-size:11px;
}

@media(max-width:900px){

    .order-box{

        grid-template-columns:1fr;

        padding:28px;
    }
}

@media(max-width:560px){

    .form-row{
        grid-template-columns:1fr;
    }
}


/* =========================================================
   FLASH
========================================================= */

.flash-container{

    position:fixed;

    top:88px;

    left:50%;

    transform:translateX(-50%);

    z-index:500;

    width:min(92%,500px);

    display:grid;

    gap:10px;
}

.flash{

    padding:14px 17px;

    border-radius:12px;

    border:1px solid;

    box-shadow:0 20px 50px rgba(0,0,0,.4);

    animation:flashIn .3s ease;

    font-size:13px;
}

.flash.success{

    color:#c8f0da;

    background:rgba(76,174,125,.12);

    border-color:rgba(76,174,125,.35);
}

.flash.error{

    color:#ffd0cb;

    background:rgba(225,89,79,.12);

    border-color:rgba(225,89,79,.35);
}

@keyframes flashIn{

    from{
        opacity:0;
        transform:translateY(-10px);
    }

    to{
        opacity:1;
        transform:translateY(0);
    }
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

.footer p{

    color:var(--muted2);

    font-size:11px;
}


/* =========================================================
   MOBILE
========================================================= */

@media(max-width:600px){

    .wrap{
        width:min(100% - 28px,1120px);
    }

    .hero h1{
        font-size:39px;
    }

    .lead{
        font-size:15px;
    }

    .stats{
        gap:18px;
    }

    .stat strong{
        font-size:16px;
    }

    .stat span{
        font-size:10px;
    }

    .profile-card{
        width:285px;
    }

    .float.one{
        right:-5px;
    }

    .float.two{
        left:-5px;
    }

    .order{
        padding-top:60px;
    }

    .order-box{
        padding:20px;
    }
}

</style>

</head>

<body>


<!-- =========================================================
     FLASH MESSAGES
========================================================= -->

{% with messages = get_flashed_messages(with_categories=true) %}

{% if messages %}

<div class="flash-container" id="flashContainer">

{% for category, message in messages %}

<div class="flash {{ category }}">
    {{ message }}
</div>

{% endfor %}

</div>

{% endif %}

{% endwith %}


<!-- =========================================================
     NAV
========================================================= -->

<header>

<nav class="nav wrap">

<a href="/" class="brand">

<span class="badge">

<svg
viewBox="0 0 24 24"
fill="none"
stroke="#080a0f"
stroke-width="3"
stroke-linecap="round"
stroke-linejoin="round">

<polyline points="20 6 9 17 4 12"/>

</svg>

</span>

SHOVIX

</a>


<div class="nav-links">

<a href="#process">كيف نعمل</a>

<a href="#features">لماذا SHOVIX</a>

<a href="#order">اطلب الآن</a>

</div>


<a href="#order" class="nav-cta">
ابدأ طلبك
</a>

</nav>

</header>


<main>


<!-- =========================================================
     HERO
========================================================= -->

<section class="hero wrap">

<div>

<span class="eyebrow">

<span class="dot"></span>

PREMIUM PROFILE STUDIO

</span>


<h1>

هويتك الرقمية تستاهل تصميم

<span>
بحجم حضورك.
</span>

</h1>


<p class="lead">

SHOVIX يحوّل حسابك أو مشروعك إلى صفحة بروفايل احترافية
مصممة خصيصًا لك، بهوية بصرية مميزة وتجربة رقمية أنيقة.

</p>


<div class="actions">

<a href="#order" class="btn btn-primary">

ابدأ طلبك الآن

<span>↗</span>

</a>


<a href="#process" class="btn btn-secondary">

شاهد كيف نعمل

</a>

</div>


<div class="stats">

<div class="stat">

<strong>+300</strong>

<span>تصميم احترافي</span>

</div>


<div class="stat">

<strong>48H</strong>

<span>وقت التسليم</span>

</div>


<div class="stat">

<strong>4.9★</strong>

<span>رضا العملاء</span>

</div>

</div>

</div>


<!-- PROFILE -->

<div class="stage" id="stage">

<div class="float one">

✓ تصميم
<b>مخصص</b>

</div>


<div class="float two">

تسليم خلال
<b>48 ساعة</b>

</div>


<div class="profile-card" id="profileCard">

<div class="card-top">

<div class="avatar">

<div class="avatar-inner">
SX
</div>

</div>


<div class="verified">

✓

موثّق

</div>

</div>


<div class="profile-name">
بروفايل العميل
</div>

<div class="handle">
@your.profile
</div>


<div class="lines">

<i></i>
<i></i>
<i></i>

</div>


<div class="metrics">

<div>

<b>12.4K</b>

<span>متابع</span>

</div>

<div>

<b>98%</b>

<span>تفاعل</span>

</div>

<div>

<b>#SX-08</b>

<span>تصميم</span>

</div>

</div>

</div>

</div>

</section>


<!-- =========================================================
     PROCESS
========================================================= -->

<section class="section" id="process">

<div class="wrap">

<div class="section-head">

<span class="eyebrow">

<span class="dot"></span>

آلية العمل

</span>


<h2>
من الطلب إلى التسليم في 3 خطوات
</h2>


<p>
عملية واضحة ومباشرة للحصول على صفحة احترافية
تعكس هويتك الرقمية.
</p>

</div>


<div class="steps">

<div class="step">

<div class="number">
01
</div>

<h3>
ترسل التفاصيل
</h3>

<p>
أرسل بياناتك وفكرة التصميم وأي صور أو ملفات تريد استخدامها.
</p>

</div>


<div class="step">

<div class="number">
02
</div>

<h3>
نصمم صفحتك
</h3>

<p>
نجهز لك تصميمًا مخصصًا يناسب هويتك وطريقة ظهورك.
</p>

</div>


<div class="step">

<div class="number">
03
</div>

<h3>
تستلم التصميم
</h3>

<p>
بعد الانتهاء تتلقى تفاصيل طلبك والتصميم عبر وسيلة التواصل المناسبة.
</p>

</div>

</div>

</div>

</section>


<!-- =========================================================
     FEATURES
========================================================= -->

<section class="section">

<div class="wrap">

<div class="features" id="features">

<div class="feature">

<strong>
هوية مخصصة
</strong>

<span>
كل صفحة يتم تصميمها حسب طلب العميل.
</span>

</div>


<div class="feature">

<strong>
تصميم فاخر
</strong>

<span>
واجهة حديثة ومناسبة للعلامات الشخصية.
</span>

</div>


<div class="feature">

<strong>
تواصل مباشر
</strong>

<span>
نتابع التفاصيل حتى يصبح التصميم جاهزًا.
</span>

</div>


<div class="feature">

<strong>
رقم طلب
</strong>

<span>
كل طلب يحصل على رقم خاص.
</span>

</div>

</div>

</div>

</section>


<!-- =========================================================
     ORDER
========================================================= -->

<section class="order" id="order">

<div class="wrap">

<div class="order-box">


<div class="order-info">

<span class="eyebrow">

<span class="dot"></span>

طلب جديد

</span>


<h2>
جهّز بياناتك ونبدأ
</h2>


<p>
أرسل تفاصيل مشروعك وسنراجع الطلب ونتواصل معك.
</p>


<ul class="checks">

<li>

<span class="check">✓</span>

بياناتك تستخدم لغرض الطلب فقط.

</li>


<li>

<span class="check">✓</span>

يمكنك إرفاق صور وملفات مرجعية.

</li>


<li>

<span class="check">✓</span>

تحصل على رقم طلب بعد الإرسال.

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
placeholder="مثال: أحمد محمد"
autocomplete="name"
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
placeholder="+972..."
autocomplete="tel"
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
placeholder="example@email.com"
autocomplete="email"
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
placeholder="اسمك الظاهر"
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
placeholder="اكتب فكرتك، الألوان، الروابط، وأي تفاصيل تريدها..."
required
></textarea>

</div>


<div class="field">

<label>
الصور والملفات
</label>


<div class="dropzone" id="dropzone">

<input
type="file"
id="files"
name="files"
multiple
accept=".png,.jpg,.jpeg,.webp,.pdf"
>


<div class="upload-icon">
↑
</div>


<div class="upload-text">

<b>
اضغط للرفع
</b>

أو اسحب الملفات هنا

</div>


<div class="upload-hint">

PNG / JPG / WEBP / PDF — حتى 15MB

</div>

</div>


<div class="files-list" id="fileList"></div>

</div>


<div class="submit">

<button
type="submit"
id="submitBtn"
>

إرسال الطلب
↗

</button>


<span class="submit-note">

سيظهر رقم الطلب بعد الإرسال.

</span>

</div>

</form>

</div>

</div>

</section>

</main>


<!-- =========================================================
     FOOTER
========================================================= -->

<footer>

<div class="footer wrap">

<div class="brand">

<span class="badge">

<svg
viewBox="0 0 24 24"
fill="none"
stroke="#080a0f"
stroke-width="3"
stroke-linecap="round"
stroke-linejoin="round">

<polyline points="20 6 9 17 4 12"/>

</svg>

</span>

SHOVIX

</div>


<p>
© <span id="year"></span> SHOVIX — جميع الحقوق محفوظة.
</p>

</div>

</footer>


<script>

/* =========================================================
   YEAR
========================================================= */

document.getElementById("year").textContent =
    new Date().getFullYear();


/* =========================================================
   CARD EFFECT
========================================================= */

(function(){

    const stage =
        document.getElementById("stage");

    const card =
        document.getElementById("profileCard");

    if(!stage || !card) return;

    const reduce =
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if(reduce) return;

    stage.addEventListener(
        "mousemove",
        function(e){

            const rect =
                stage.getBoundingClientRect();

            const x =
                (e.clientX - rect.left) /
                rect.width - .5;

            const y =
                (e.clientY - rect.top) /
                rect.height - .5;

            card.style.transform =
                "rotateY(" +
                (-10 - x * 14) +
                "deg) rotateX(" +
                (6 + y * 10) +
                "deg)";

        }
    );

    stage.addEventListener(
        "mouseleave",
        function(){

            card.style.transform =
                "rotateY(-10deg) rotateX(6deg)";

        }
    );

})();


/* =========================================================
   FILE UPLOAD
========================================================= */

(function(){

    const input =
        document.getElementById("files");

    const dropzone =
        document.getElementById("dropzone");

    const list =
        document.getElementById("fileList");

    if(!input || !dropzone || !list)
        return;


    function renderFiles(){

        list.innerHTML = "";

        const files =
            Array.from(input.files || []);

        files.forEach(function(file){

            const item =
                document.createElement("div");

            item.className =
                "file-item";

            const size =
                (file.size / 1024 / 1024)
                .toFixed(2);

            const nameSpan = document.createElement("span");
            nameSpan.textContent = file.name;

            const sizeSpan = document.createElement("span");
            sizeSpan.textContent = size + " MB";

            item.appendChild(nameSpan);
            item.appendChild(sizeSpan);

            list.appendChild(item);

        });

    }


    input.addEventListener(
        "change",
        renderFiles
    );


    ["dragenter","dragover"].forEach(
        function(eventName){

            dropzone.addEventListener(
                eventName,
                function(e){

                    e.preventDefault();

                    dropzone.classList.add("drag");

                }
            );

        }
    );


    ["dragleave","drop"].forEach(
        function(eventName){

            dropzone.addEventListener(
                eventName,
                function(e){

                    e.preventDefault();

                    dropzone.classList.remove("drag");

                }
            );

        }
    );


    dropzone.addEventListener(
        "drop",
        function(e){

            if(
                e.dataTransfer &&
                e.dataTransfer.files.length
            ){

                input.files =
                    e.dataTransfer.files;

                renderFiles();

            }

        }
    );

})();


/* =========================================================
   FORM SUBMIT
   بيضمن POST دايمًا عن طريق fetch، وبيمنع الضغط المتكرر
   على الزرار، وبيوضح لو حصل خطأ بدل ما يفضل عالق.
========================================================= */

(function(){

    const form =
        document.getElementById("orderForm");

    const button =
        document.getElementById("submitBtn");

    if(!form || !button)
        return;

    const ORDER_URL =
        form.getAttribute("action") || "/order";

    const originalHTML =
        button.innerHTML;

    form.addEventListener(
        "submit",
        function(e){

            e.preventDefault();

            if(button.disabled)
                return;

            button.disabled = true;

            button.textContent =
                "جاري إرسال الطلب...";

            const formData =
                new FormData(form);

            fetch(ORDER_URL, {
                method: "POST",
                body: formData,
                credentials: "same-origin",
                redirect: "follow"
            })
            .then(function(response){

                if(response.status === 405){
                    throw new Error(
                        "السيرفر رفض الطريقة المستخدمة (405). تأكد إن الراوت في app.py يقبل POST."
                    );
                }

                window.location.href =
                    response.url || "/";

            })
            .catch(function(err){

                console.error(
                    "Order submit error:",
                    err
                );

                button.disabled = false;

                button.innerHTML =
                    originalHTML;

                alert(
                    "حصل خطأ أثناء إرسال الطلب: " +
                    err.message
                );

            });

        }
    );

})();


/* =========================================================
   FLASH AUTO HIDE
========================================================= */

(function(){

    const container =
        document.getElementById("flashContainer");

    if(!container) return;

    setTimeout(
        function(){

            container.style.transition =
                "opacity .4s ease";

            container.style.opacity = "0";

            setTimeout(
                function(){
                    container.remove();
                },
                500
            );

        },
        7000
    );

})();

</script>

</body>
</html>
"""


# =========================================================
# HELPERS
# =========================================================

def allowed_file(filename):

    if not filename:
        return False

    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()

    return extension in ALLOWED_EXTENSIONS


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
            "OWNER_EMAIL غير موجود."
        )

    if not GMAIL_APP_PASSWORD:
        raise RuntimeError(
            "GMAIL_APP_PASSWORD غير موجود."
        )

    order_id = str(uuid.uuid4())[:8].upper()

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    message = EmailMessage()

    message["Subject"] = (
        f"SHOVIX | طلب #{order_id} | "
        f"{data['name']}"
    )

    message["From"] = OWNER_EMAIL

    message["To"] = OWNER_EMAIL

    if data.get("email"):
        message["Reply-To"] = data["email"]


    body = f"""
SHOVIX
PREMIUM PROFILE STUDIO
========================================

طلب تصميم جديد

رقم الطلب:
#{order_id}

وقت الطلب:
{now}

----------------------------------------
بيانات العميل
----------------------------------------

الاسم:
{data["name"]}

الهاتف:
{data["phone"]}

البريد:
{data.get("email") or "غير محدد"}

نوع الحساب:
{data["client_type"]}

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


    for file in files:

        if not file:
            continue

        if not file.filename:
            continue

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

        maintype, subtype = mime_types[
            extension
        ]

        message.add_attachment(

            file_data,

            maintype=maintype,

            subtype=subtype,

            filename=filename
        )


    # =====================================================
    # GMAIL
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

@app.route("/", methods=["GET"])
def home():

    return render_template_string(
        HTML
    )


# =========================================================
# ORDER
# =========================================================

@app.route(
    "/order",
    methods=["GET", "POST"]
)
def order():

    # -----------------------------------------------------
    # مهم جدًا:
    # إذا دخل شخص إلى /order مباشرة في المتصفح
    # لن يظهر 405.
    # -----------------------------------------------------

    if request.method == "GET":

        return redirect(
            url_for("home")
        )


    # -----------------------------------------------------
    # FORM DATA
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not name:

        flash(
            "يرجى كتابة الاسم الكامل.",
            "error"
        )

        return redirect(
            url_for("home") + "#order"
        )


    if not phone:

        flash(
            "يرجى كتابة رقم الهاتف.",
            "error"
        )

        return redirect(
            url_for("home") + "#order"
        )


    if not description:

        flash(
            "يرجى كتابة تفاصيل المشروع.",
            "error"
        )

        return redirect(
            url_for("home") + "#order"
        )


    # البريد الإلكتروني اختياري، لكن لو اتكتب لازم يكون صحيح
    if email and not is_valid_email(email):

        flash(
            "صيغة البريد الإلكتروني غير صحيحة.",
            "error"
        )

        return redirect(
            url_for("home") + "#order"
        )


    # -----------------------------------------------------
    # DUPLICATE PROTECTION
    # -----------------------------------------------------

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
            url_for("home") + "#order"
        )


    # -----------------------------------------------------
    # FILES
    # -----------------------------------------------------

    files = request.files.getlist(
        "files"
    )


    # -----------------------------------------------------
    # CHECK FILE EXTENSIONS
    # -----------------------------------------------------

    for file in files:

        if not file:
            continue

        if not file.filename:
            continue

        if not allowed_file(
            file.filename
        ):

            flash(
                f"نوع الملف غير مسموح: {file.filename}",
                "error"
            )

            return redirect(
                url_for("home") + "#order"
            )


    # -----------------------------------------------------
    # SEND
    # -----------------------------------------------------

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
            "تعذر تسجيل الدخول إلى Gmail. تأكد من App Password.",
            "error"
        )


    except smtplib.SMTPException as error:

        print(
            "SHOVIX SMTP ERROR:",
            error
        )

        flash(
            "حدث خطأ في اتصال البريد الإلكتروني.",
            "error"
        )


    except Exception as error:

        print(
            "SHOVIX ERROR:",
            error
        )

        flash(
            "حدث خطأ أثناء إرسال الطلب.",
            "error"
        )


    return redirect(
        url_for("home") + "#order"
    )


# =========================================================
# 413 — FILE TOO LARGE
# =========================================================

@app.errorhandler(413)
def file_too_large(error):

    flash(
        "حجم الملفات أكبر من 15MB.",
        "error"
    )

    return redirect(
        url_for("home") + "#order"
    )


# =========================================================
# 404
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

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
        "حدث خطأ داخلي في الخادم.",
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
