from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages

from .models import UserProfile


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')

        return render(request, 'exam/login.html', {
            'error': 'Username yoki password noto‘g‘ri.'
        })

    return render(request, 'exam/login.html')


def register(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        email = (request.POST.get('email') or '').strip()
        password = (request.POST.get('password') or '').strip()

        if not username or not password:
            return render(request, 'exam/register.html', {
                'error': 'Username va password kiritilishi shart.'
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'exam/register.html', {
                'error': 'Bu foydalanuvchi nomi band.'
            })

        if email and User.objects.filter(email=email).exists():
            return render(request, 'exam/register.html', {
                'error': 'Bu email allaqachon ishlatilgan.'
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        UserProfile.objects.get_or_create(user=user)

        login(request, user)
        messages.success(request, f'Xush kelibsiz, {username}!')
        return redirect('home')

    return render(request, 'exam/register.html')


def custom_logout(request):
    logout(request)
    return redirect('home')