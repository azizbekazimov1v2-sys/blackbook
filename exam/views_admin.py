from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Max, Count, Q
from django.http import HttpResponse

from .models import Test, VideoCourse, UserPremiumAccess, TestAttempt


@login_required
def admin_panel(request):
    if not request.user.is_staff:
        return redirect('home')

    query = (request.GET.get('q') or '').strip()
    category_filter = (request.GET.get('category') or '').strip()
    premium_filter = (request.GET.get('premium') or '').strip()

    tests = Test.objects.filter(created_by=request.user).prefetch_related(
        'questions',
        'attempts',
        'questions__attempt_answers',
    ).order_by('-created_at')

    videos = VideoCourse.objects.filter(created_by=request.user).order_by('-created_at')
    users = User.objects.all().order_by('-date_joined')

    if query:
        tests = tests.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )
        videos = videos.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )

    if category_filter:
        tests = tests.filter(category=category_filter)
        videos = videos.filter(category=category_filter)

    if premium_filter == 'premium':
        tests = tests.filter(is_premium=True)
        videos = videos.filter(is_premium=True)
    elif premium_filter == 'free':
        tests = tests.filter(is_premium=False)
        videos = videos.filter(is_premium=False)

    attempts_all = TestAttempt.objects.filter(test__created_by=request.user)

    total_attempts = attempts_all.count()
    avg_score_all = round(attempts_all.aggregate(avg=Avg('score'))['avg'] or 0)
    best_score_all = attempts_all.aggregate(best=Max('score'))['best'] or 0

    active_users_7d = TestAttempt.objects.filter(
        test__created_by=request.user,
        completed_at__gte=timezone.now() - timedelta(days=7)
    ).values('user').distinct().count()

    premium_users_count = UserPremiumAccess.objects.filter(
        is_active=True,
        expires_at__gt=timezone.now()
    ).values('user').distinct().count()

    test_cards = []

    for test in tests:
        attempts_qs = test.attempts.all().order_by('-completed_at')

        stats = attempts_qs.aggregate(
            attempt_count=Count('id'),
            avg_score=Avg('score'),
            avg_percentage=Avg('percentage'),
            best_score=Max('score'),
        )

        participant_count = attempts_qs.exclude(user__isnull=True).values('user').distinct().count()
        last_taken = attempts_qs.first()

        hard_questions = []
        for question in test.questions.all().order_by('order'):
            total_q_attempts = question.attempt_answers.count()
            wrong_count = question.attempt_answers.filter(is_correct=False).count()

            if total_q_attempts > 0:
                wrong_rate = round((wrong_count / total_q_attempts) * 100, 1)
                hard_questions.append({
                    'order': question.order,
                    'wrong_count': wrong_count,
                    'total_attempts': total_q_attempts,
                    'wrong_rate': wrong_rate,
                })

        hard_questions.sort(key=lambda x: (-x['wrong_rate'], -x['wrong_count'], x['order']))

        test_cards.append({
            'test': test,
            'attempt_count': stats['attempt_count'] or 0,
            'participant_count': participant_count,
            'avg_score': round(stats['avg_score'] or 0),
            'avg_percentage': round(float(stats['avg_percentage'] or 0), 1),
            'best_score': stats['best_score'] or 0,
            'last_taken': last_taken,
            'hard_questions': hard_questions[:5],
        })

    return render(request, 'exam/admin_panel.html', {
        'test_cards': test_cards,
        'videos': videos,
        'users': users[:10],
        'total_tests': tests.count(),
        'total_videos': videos.count(),
        'total_users': users.count(),
        'total_attempts': total_attempts,
        'avg_score_all': avg_score_all,
        'best_score_all': best_score_all,
        'active_users_7d': active_users_7d,
        'premium_users_count': premium_users_count,
        'query': query,
        'category_filter': category_filter,
        'premium_filter': premium_filter,
    })


@login_required
def users_list(request):
    if not request.user.is_staff:
        return redirect('home')

    users = User.objects.all().order_by('-date_joined')
    return render(request, 'exam/users_list.html', {
        'users': users,
        'total_users': users.count()
    })


@login_required
def give_premium(request, user_id, premium_type):
    if not request.user.is_staff:
        return redirect('home')

    if request.method != 'POST':
        messages.error(request, "Noto‘g‘ri so‘rov.")
        return redirect('users_list')

    if premium_type not in ['english', 'math', 'analysis']:
        messages.error(request, "Premium turi noto‘g‘ri.")
        return redirect('users_list')

    user = get_object_or_404(User, id=user_id)

    access, created = UserPremiumAccess.objects.get_or_create(
        user=user,
        premium_type=premium_type,
        defaults={
            'is_active': True,
            'expires_at': timezone.now() + timedelta(days=30)
        }
    )

    if not created:
        access.is_active = True
        access.expires_at = timezone.now() + timedelta(days=30)
        access.save()

    messages.success(request, f'{user.username} ga {premium_type} premium 30 kunga berildi.')
    return redirect('users_list')


@login_required
def delete_test(request, test_id):
    if not request.user.is_staff:
        return redirect('home')

    test = get_object_or_404(Test, id=test_id, created_by=request.user)

    if request.method == 'POST':
        test.delete()
        messages.success(request, 'Test o‘chirildi.')
        return redirect('admin_panel')

    return render(request, 'exam/delete_test.html', {'test': test})


@login_required
def delete_video(request, video_id):
    if not request.user.is_staff:
        return redirect('home')

    video = get_object_or_404(VideoCourse, id=video_id, created_by=request.user)

    if request.method == 'POST':
        if video.video_file:
            video.video_file.delete(save=False)

        video.delete()
        messages.success(request, 'Video o‘chirildi.')
        return redirect('admin_panel')

    return render(request, 'exam/delete_video.html', {'video': video})
from django.http import HttpResponse
from django.contrib.auth.models import User


def create_admin(request):
    username = "SATazizbek"
    email = "azizbekazimov1v2@gmail.com"
    password = "SATazizbek21."

    if User.objects.filter(username=username).exists():
        return HttpResponse("Admin already exists")

    User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    return HttpResponse("Admin created successfully")