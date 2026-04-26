from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count

from .models import Test, DuelChallenge, TestAttempt


def has_active_duel(user):
    return DuelChallenge.objects.filter(
        Q(challenger=user) | Q(opponent=user),
        status__in=['pending', 'accepted']
    ).exists()


def get_duel_stats(user):
    completed = DuelChallenge.objects.filter(
        Q(challenger=user) | Q(opponent=user),
        status='completed'
    )

    wins = completed.filter(winner=user).count()
    draws = completed.filter(winner__isnull=True).count()
    losses = completed.exclude(winner=user).exclude(winner__isnull=True).count()

    total = completed.count()
    win_rate = round((wins / total) * 100) if total > 0 else 0

    return {
        'wins': wins,
        'losses': losses,
        'draws': draws,
        'total': total,
        'win_rate': win_rate,
    }


def build_duel_leaderboard():
    users = User.objects.all().order_by('username')
    rows = []

    for user in users:
        stats = get_duel_stats(user)
        if stats['total'] > 0:
            rows.append({
                'user': user,
                **stats
            })

    rows.sort(key=lambda x: (-x['wins'], x['losses'], -x['win_rate'], x['user'].username.lower()))
    return rows[:20]


@login_required
def duel_mode(request):
    tests = Test.objects.filter(is_published=True).order_by('-created_at')
    users = User.objects.exclude(id=request.user.id).order_by('username')

    incoming_duels = DuelChallenge.objects.filter(
        opponent=request.user,
        status='pending'
    ).select_related('test', 'challenger').order_by('-created_at')

    my_duels = DuelChallenge.objects.filter(
        Q(challenger=request.user) | Q(opponent=request.user)
    ).select_related('test', 'challenger', 'opponent', 'winner').order_by('-created_at')[:30]

    my_stats = get_duel_stats(request.user)
    leaderboard = build_duel_leaderboard()

    return render(request, 'exam/duel_mode.html', {
        'tests': tests,
        'users': users,
        'incoming_duels': incoming_duels,
        'my_duels': my_duels,
        'my_stats': my_stats,
        'leaderboard': leaderboard,
    })


@login_required
def create_duel(request):
    if request.method != 'POST':
        return redirect('duel_mode')

    if has_active_duel(request.user):
        messages.error(request, "Sizda hozir faol duel bor.")
        return redirect('duel_mode')

    test = get_object_or_404(Test, id=request.POST.get('test_id'), is_published=True)
    opponent = get_object_or_404(User, id=request.POST.get('opponent_id'))

    if opponent == request.user:
        messages.error(request, "O‘zingizga duel yubora olmaysiz.")
        return redirect('duel_mode')

    if has_active_duel(opponent):
        messages.error(request, "Bu userda hozir faol duel bor.")
        return redirect('duel_mode')

    DuelChallenge.objects.create(
        test=test,
        challenger=request.user,
        opponent=opponent
    )

    messages.success(request, f"{opponent.username} ga duel taklifi yuborildi.")
    return redirect('duel_mode')


@login_required
def accept_duel(request, duel_id):
    duel = get_object_or_404(
        DuelChallenge,
        id=duel_id,
        opponent=request.user,
        status='pending'
    )

    duel.status = 'accepted'
    duel.accepted_at = timezone.now()
    duel.save()

    messages.success(request, "Duel qabul qilindi. Testni boshlang.")
    return redirect('take_pdf_test', test_id=duel.test.id)


@login_required
def cancel_duel(request, duel_id):
    duel = get_object_or_404(DuelChallenge, id=duel_id)

    if request.user not in [duel.challenger, duel.opponent]:
        return redirect('duel_mode')

    if duel.status in ['pending', 'accepted']:
        duel.status = 'cancelled'
        duel.save()
        messages.success(request, "Duel bekor qilindi.")

    return redirect('duel_mode')


@login_required
def start_duel(request, duel_id):
    duel = get_object_or_404(DuelChallenge, id=duel_id)

    if request.user not in [duel.challenger, duel.opponent]:
        return redirect('duel_mode')

    if duel.status == 'completed':
        return redirect('duel_result', duel_id=duel.id)

    return redirect('take_pdf_test', test_id=duel.test.id)


@login_required
def duel_result(request, duel_id):
    duel = get_object_or_404(DuelChallenge, id=duel_id)

    if request.user not in [duel.challenger, duel.opponent]:
        return redirect('duel_mode')

    challenger_attempt = TestAttempt.objects.filter(
        test=duel.test,
        user=duel.challenger,
        completed_at__gte=duel.created_at
    ).order_by('-completed_at').first()

    opponent_attempt = TestAttempt.objects.filter(
        test=duel.test,
        user=duel.opponent,
        completed_at__gte=duel.created_at
    ).order_by('-completed_at').first()

    if challenger_attempt and opponent_attempt and duel.status != 'completed':
        if challenger_attempt.score > opponent_attempt.score:
            duel.winner = duel.challenger
        elif opponent_attempt.score > challenger_attempt.score:
            duel.winner = duel.opponent
        else:
            duel.winner = None

        duel.status = 'completed'
        duel.completed_at = timezone.now()
        duel.save()

    return render(request, 'exam/duel_result.html', {
        'duel': duel,
        'challenger_attempt': challenger_attempt,
        'opponent_attempt': opponent_attempt,
    })