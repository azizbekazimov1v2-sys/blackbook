import re
import time

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.cache import cache
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

from .models import UserProfile


SUSPICIOUS_USERNAME_PARTS = [
    "http",
    "www",
    ".com",
    ".ru",
    ".net",
    ".org",
    "telegram",
    "instagram",
    "remove it",
    "bluebooky",
    "casino",
    "bonus",
    "crypto",
    "loan",
    "bet",
]


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def is_suspicious_username(username: str) -> bool:
    u = username.lower()

    for part in SUSPICIOUS_USERNAME_PARTS:
        if part in u:
            return True

    # Juda uzun username
    if len(username) > 24:
        return True

    # Juda ko‘p raqam
    digit_count = sum(ch.isdigit() for ch in username)
    if digit_count >= 8:
        return True

    # Faqat harf, raqam, underscore, nuqta bo‘lsin
    if not re.fullmatch(r"[A-Za-z0-9_.]+", username):
        return True

    return False


def too_many_requests(ip: str) -> bool:
    minute_key = f"register_minute_{ip}"
    hour_key = f"register_hour_{ip}"

    minute_count = cache.get(minute_key, 0)
    hour_count = cache.get(hour_key, 0)

    # 10 daqiqada 5 marta, 1 soatda 12 marta urinsa bloklaymiz
    if minute_count >= 5 or hour_count >= 12:
        return True

    return False


def increase_request_counters(ip: str):
    minute_key = f"register_minute_{ip}"
    hour_key = f"register_hour_{ip}"

    minute_count = cache.get(minute_key, 0)
    hour_count = cache.get(hour_key, 0)

    cache.set(minute_key, minute_count + 1, timeout=600)   # 10 daqiqa
    cache.set(hour_key, hour_count + 1, timeout=3600)      # 1 soat


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = (request.POST.get("password") or "").strip()

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")

        return render(request, "exam/login.html", {
            "error": "Username yoki password noto‘g‘ri."
        })

    return render(request, "exam/login.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "GET":
        request.session["register_started_at"] = int(time.time())
        return render(request, "exam/register.html")

    ip = get_client_ip(request)

    # 1) Rate limit
    if too_many_requests(ip):
        return render(request, "exam/register.html", {
            "error": "Juda ko‘p urinish bo‘ldi. Bir ozdan keyin qayta urinib ko‘ring."
        })

    increase_request_counters(ip)

    username = (request.POST.get("username") or "").strip()
    email = (request.POST.get("email") or "").strip()
    password = (request.POST.get("password") or "").strip()
    website = (request.POST.get("website") or "").strip()  # honeypot

    # 2) Honeypot
    if website:
        return render(request, "exam/register.html", {
            "error": "Ro‘yxatdan o‘tish rad etildi."
        })

    # 3) Form juda tez to‘ldirilganmi?
    started_at = request.session.get("register_started_at")
    now_ts = int(time.time())

    if started_at:
        elapsed = now_ts - int(started_at)
        if elapsed < 3:
            return render(request, "exam/register.html", {
                "error": "Forma juda tez yuborildi. Iltimos, qayta urinib ko‘ring."
            })

    # 4) Majburiy fieldlar
    if not username or not email or not password:
        return render(request, "exam/register.html", {
            "error": "Username, email va password kiritilishi shart."
        })

    # 5) Username tekshirish
    if len(username) < 4:
        return render(request, "exam/register.html", {
            "error": "Username kamida 4 ta belgidan iborat bo‘lishi kerak."
        })

    if is_suspicious_username(username):
        return render(request, "exam/register.html", {
            "error": "Bu username qabul qilinmaydi. Oddiy va toza username tanlang."
        })

    if User.objects.filter(username__iexact=username).exists():
        return render(request, "exam/register.html", {
            "error": "Bu foydalanuvchi nomi band."
        })

    # 6) Email tekshirish
    try:
        validate_email(email)
    except ValidationError:
        return render(request, "exam/register.html", {
            "error": "Email noto‘g‘ri kiritildi."
        })

    if User.objects.filter(email__iexact=email).exists():
        return render(request, "exam/register.html", {
            "error": "Bu email allaqachon ishlatilgan."
        })

    # 7) Password tekshirish
    if len(password) < 8:
        return render(request, "exam/register.html", {
            "error": "Password kamida 8 ta belgidan iborat bo‘lishi kerak."
        })

    if password.isdigit():
        return render(request, "exam/register.html", {
            "error": "Password faqat raqamlardan iborat bo‘lmasligi kerak."
        })

    # 8) User yaratish
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )

    UserProfile.objects.get_or_create(user=user)

    # session ni yangilab qo‘yamiz
    request.session.pop("register_started_at", None)

    login(request, user)
    messages.success(request, f"Xush kelibsiz, {username}!")
    return redirect("home")


def custom_logout(request):
    logout(request)
    return redirect("home")