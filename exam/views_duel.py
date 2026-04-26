# views_duel.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponseForbidden
from .models import DuelChallenge, Test, User


# Agar DuelResult modeli mavjud bo'lmasa, vaqtincha dict ishlatamiz
# Keyinchalik model yaratishingiz mumkin

@login_required
def duel_list(request):
    """Barcha duellarni ko'rsatish"""
    active_duels = DuelChallenge.objects.filter(
        Q(challenger=request.user) | Q(opponent=request.user)
    ).exclude(status='completed').exclude(status='cancelled')

    completed_duels = DuelChallenge.objects.filter(
        Q(challenger=request.user) | Q(opponent=request.user),
        status='completed'
    )

    # Duel natijalarini olish (vaqtincha)
    duel_results = {}
    for duel in active_duels:
        duel_results[duel.id] = {
            'challenger_completed': False,
            'opponent_completed': False
        }

    return render(request, 'duel_list.html', {
        'active_duels': active_duels,
        'completed_duels': completed_duels,
        'duel_results': duel_results,
    })


@login_required
def create_duel(request):
    """Yangi duel yaratish"""
    if request.method == 'POST':
        test_id = request.POST.get('test_id')
        opponent_id = request.POST.get('opponent_id')

        if not test_id or not opponent_id:
            messages.error(request, "Iltimos, test va raqibni tanlang!")
            return redirect('home')

        # O'ziga o'zi duel yaratishni oldini olish
        try:
            opponent_id = int(opponent_id)
        except ValueError:
            messages.error(request, "Noto'g'ri raqib ID si!")
            return redirect('home')

        if opponent_id == request.user.id:
            messages.error(request, "O'zingiz bilan duel yarata olmaysiz!")
            return redirect('home')

        test = get_object_or_404(Test, id=test_id)
        opponent = get_object_or_404(User, id=opponent_id)

        # Shu test va shu raqib bilan kutilayotgan duel borligini tekshirish
        existing_duel = DuelChallenge.objects.filter(
            test=test,
            challenger=request.user,
            opponent=opponent,
            status='pending'
        ).exists()

        if existing_duel:
            messages.warning(request, f"Siz allaqachon {opponent.username} bilan ushbu test bo'yicha duel yaratgansiz!")
            return redirect('home')

        duel = DuelChallenge.objects.create(
            test=test,
            challenger=request.user,
            opponent=opponent,
            status='pending'
        )

        messages.success(request, f"Duel yaratildi! {opponent.username} bilan jang qiling.")
        return redirect('home')

    return redirect('home')


@login_required
def accept_duel(request, duel_id):
    """Duelli qabul qilish"""
    duel = get_object_or_404(DuelChallenge, id=duel_id, opponent=request.user, status='pending')
    duel.status = 'accepted'
    duel.accepted_at = timezone.now()
    duel.save()
    messages.success(request, f"Duel qabul qilindi! Endi testni boshlashingiz mumkin.")
    return redirect('duel_list')


@login_required
def cancel_duel(request, duel_id):
    """Duelli bekor qilish"""
    duel = get_object_or_404(DuelChallenge, id=duel_id, status='pending')

    # Faqat challenger yoki opponent bekor qila oladi
    if duel.challenger == request.user or duel.opponent == request.user:
        duel.status = 'cancelled'
        duel.save()
        messages.info(request, "Duel bekor qilindi.")
    else:
        messages.error(request, "Bu duelli bekor qilish huquqingiz yo'q!")

    return redirect('duel_list')


@login_required
def take_duel_test(request, duel_id):
    """Duelli testni boshlash"""
    duel = get_object_or_404(DuelChallenge, id=duel_id, status='accepted')

    # Faqat duel ishtirokchilari testni ishlay oladi
    if request.user not in [duel.challenger, duel.opponent]:
        messages.error(request, "Bu duelda qatnashish huquqingiz yo'q!")
        return redirect('duel_list')

    # Session orqali duel natijalarini saqlash (vaqtincha)
    # Keyinchalik DuelResult modeliga o'tkazishingiz mumkin
    session_key = f'duel_{duel_id}_{request.user.id}'
    if request.session.get(session_key, {}).get('completed', False):
        messages.warning(request, "Siz bu duelni allaqachon topshirgansiz!")
        return redirect('duel_list')

    # Testni ko'rsatish
    return render(request, 'duel_test.html', {
        'duel': duel,
        'test': duel.test,
    })


@login_required
def submit_duel_test(request, duel_id):
    """Duelli test natijalarini saqlash"""
    if request.method != 'POST':
        return redirect('duel_list')

    duel = get_object_or_404(DuelChallenge, id=duel_id, status='accepted')

    if request.user not in [duel.challenger, duel.opponent]:
        messages.error(request, "Bu duelda qatnashish huquqingiz yo'q!")
        return redirect('duel_list')

    # Test javoblarini hisoblash (soddalashtirilgan)
    # Aslida bu yerda test savollariga qarab hisoblash kerak
    total_questions = duel.test.total_questions

    # POST orqali kelgan javoblarni hisoblash
    correct_count = 0
    for key, value in request.POST.items():
        if key.startswith('question_'):
            # Bu yerda to'g'ri javobni tekshirish logikasi
            # Hozircha misol uchun random
            pass

    # Ballni hisoblash
    score = int((correct_count / total_questions) * 100) if total_questions > 0 else 0

    # Sessionga natijalarni saqlash
    session_key = f'duel_{duel_id}_{request.user.id}'
    request.session[session_key] = {
        'score': score,
        'correct_answers': correct_count,
        'completed': True,
        'completed_at': str(timezone.now())
    }

    # Ikkala foydalanuvchi ham testni topshirganligini tekshirish
    other_user = duel.challenger if duel.opponent == request.user else duel.opponent
    other_session_key = f'duel_{duel_id}_{other_user.id}'
    other_result = request.session.get(other_session_key, {})

    if other_result.get('completed', False):
        # Duel tugadi, g'olibni aniqlash
        duel.completed_at = timezone.now()

        if score > other_result.get('score', 0):
            duel.winner = request.user
            messages.success(request,
                             f"Tabriklaymiz! Siz g'olib bo'ldingiz! Hisob: {score} - {other_result.get('score', 0)}")
        elif score < other_result.get('score', 0):
            duel.winner = other_user
            messages.info(request, f"Siz yutqazdingiz. Hisob: {score} - {other_result.get('score', 0)}")
        else:
            messages.info(request, f"Durang! Hisob: {score} - {other_result.get('score', 0)}")

        duel.status = 'completed'
        duel.save()

        # Sessionni tozalash
        request.session.pop(session_key, None)
        request.session.pop(other_session_key, None)

        return redirect('duel_result', duel_id=duel.id)

    messages.success(request, f"Test yakunlandi! Sizning ballingiz: {score}%. Raqibni kuting.")
    return redirect('duel_list')


@login_required
def duel_result(request, duel_id):
    """Duel natijalarini ko'rsatish"""
    duel = get_object_or_404(DuelChallenge, id=duel_id)

    if request.user not in [duel.challenger, duel.opponent]:
        messages.error(request, "Bu duel natijalarini ko'rish huquqingiz yo'q!")
        return redirect('duel_list')

    # Sessiondan natijalarni olish
    results = []
    for user in [duel.challenger, duel.opponent]:
        session_key = f'duel_{duel_id}_{user.id}'
        result = request.session.get(session_key, {})
        results.append({
            'user': user,
            'score': result.get('score', 0),
            'correct_answers': result.get('correct_answers', 0),
            'completed': result.get('completed', False),
            'completed_at': result.get('completed_at', None)
        })

    return render(request, 'duel_result.html', {
        'duel': duel,
        'results': results,
    })