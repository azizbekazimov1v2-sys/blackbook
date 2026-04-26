from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import User

from .models import DuelChallenge, Test, TestAttempt


# =========================
# HELPERS
# =========================

def has_active_duel(user):
    return DuelChallenge.objects.filter(
        Q(challenger=user) | Q(opponent=user),
        status__in=['pending', 'accepted']
    ).exists()


def get_user_stats(user):
    duels = DuelChallenge.objects.filter(
        Q(challenger=user) | Q(opponent=user),
        status='completed'
    )

    wins = duels.filter(winner=user).count()
    draws = duels.filter(winner__isnull=True).count()
    losses = duels.exclude(winner=user).exclude(winner__isnull=True).count()

    total = duels.count()
    win_rate = int((wins / total) * 100) if total > 0 else 0

    return {
        'wins': wins,
        'losses': losses,
        'draws': draws,
        'total': total,
        'win_rate': win_rate,
    }


def get_leaderboard():
    users = User.objects.all()
    data = []

    for user in users:
        stats = get_user_stats(user)
        if stats['total'] > 0:
            data.append({
                'user': user,
                **stats
            })

    data.sort(key=lambda x: (-x['wins'], x['losses'], -x['win_rate']))
    return data[:20]


# =========================
# MAIN PAGE
# =========================

@login_required
def duel_mode(request):
    tests = Test.objects.all().order_by('-id')
    users = User.objects.exclude(id=request.user.id)

    incoming = DuelChallenge.objects.filter(
        opponent=request.user,
        status='pending'
    )

    my_duels = DuelChallenge.objects.filter(
        Q(challenger=request.user) | Q(opponent=request.user)
    ).order_by('-created_at')

    context = {
        'tests': tests,
        'users': users,
        'incoming_duels': incoming,
        'my_duels': my_duels,
        'my_stats': get_user_stats(request.user),
        'leaderboard': get_leaderboard()
    }

    return render(request, 'exam/duel_mode.html', context)


# =========================
# CREATE
# =========================

@login_required
def create_duel(request):
    if request.method == 'POST':

        if has_active_duel(request.user):
            messages.error(request, "Sizda faol duel bor.")
            return redirect('duel_mode')

        test = get_object_or_404(Test, id=request.POST.get('test_id'))
        opponent = get_object_or_404(User, id=request.POST.get('opponent_id'))

        if opponent == request.user:
            messages.error(request, "O‘zingizga duel qila olmaysiz.")
            return redirect('duel_mode')

        DuelChallenge.objects.create(
            challenger=request.user,
            opponent=opponent,
            test=test
        )

        messages.success(request, "Duel yuborildi.")

    return redirect('duel_mode')


# =========================
# ACCEPT / CANCEL
# =========================

@login_required
def accept_duel(request, duel_id):
    duel = get_object_or_404(DuelChallenge, id=duel_id)

    if duel.opponent != request.user:
        return redirect('duel_mode')

    duel.status = 'accepted'
    duel.accepted_at = timezone.now()
    duel.save()

    return redirect('take_pdf_test', test_id=duel.test.id)


@login_required
def cancel_duel(request, duel_id):
    duel = get_object_or_404(DuelChallenge, id=duel_id)

    if request.user in [duel.challenger, duel.opponent]:
        duel.status = 'cancelled'
        duel.save()

    return redirect('duel_mode')


# =========================
# START TEST
# =========================

@login_required
def start_duel(request, duel_id):
    duel = get_object_or_404(DuelChallenge, id=duel_id)

    return redirect('take_pdf_test', test_id=duel.test.id)


# =========================
# RESULT
# =========================

@login_required
def duel_result(request, duel_id):
    duel = get_object_or_404(DuelChallenge, id=duel_id)

    challenger_attempt = TestAttempt.objects.filter(
        test=duel.test,
        user=duel.challenger
    ).order_by('-completed_at').first()

    opponent_attempt = TestAttempt.objects.filter(
        test=duel.test,
        user=duel.opponent
    ).order_by('-completed_at').first()

    # Winner aniqlash
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