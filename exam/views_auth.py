from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponseForbidden


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = (request.POST.get('password') or '').strip()

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')

        return render(request, 'exam/login.html', {
            'error': 'Username yoki password noto‘g‘ri.'
        })

    return render(request, 'exam/login.html')


def register(request):
    return HttpResponseForbidden("Registration is temporarily closed.")


def custom_logout(request):
    logout(request)
    return redirect('home')