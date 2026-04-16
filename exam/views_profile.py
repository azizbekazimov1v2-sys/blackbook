from datetime import timedelta
from collections import defaultdict

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Max, Count

from .forms import ProfileUpdateForm
from .models import UserProfile, TestAttempt, UserPremiumAccess, Test, VideoCourse


def get_user_badge(best_score):
    if best_score >= 700:
        return "Gold"
    if best_score >= 600:
        return "Silver"
    if best_score >= 500:
        return "Bronze"
    return "Starter"


def get_streak_days(attempts):
    dates = sorted({a.completed_at.date() for a in attempts}, reverse=True)
    if not dates:
        return 0

    streak = 1
    current = dates[0]

    for next_date in dates[1:]:
        if current - next_date == timedelta(days=1):
            streak += 1
            current = next_date
        elif current == next_date:
            continue
        else:
            break

    return streak


def build_category_stats(attempts):
    category_stats = defaultdict(lambda: {
        "count": 0,
        "best": 0,
        "avg_score_total": 0,
        "avg_percentage_total": 0,
    })

    for attempt in attempts:
        category = getattr(attempt.test, 'category', 'unknown')
        category_stats[category]["count"] += 1
        category_stats[category]["best"] = max(category_stats[category]["best"], attempt.score)
        category_stats[category]["avg_score_total"] += attempt.score
        category_stats[category]["avg_percentage_total"] += float(attempt.percentage)

    final_stats = {}
    for category, stats in category_stats.items():
        count = stats["count"] or 1
        final_stats[category] = {
            "count": stats["count"],
            "best": stats["best"],
            "avg_score": round(stats["avg_score_total"] / count),
            "avg_percentage": round(stats["avg_percentage_total"] / count, 1),
        }

    return final_stats


def get_weakest_category(category_stats):
    if not category_stats:
        return None

    ordered = sorted(
        category_stats.items(),
        key=lambda item: (item[1]["avg_percentage"], item[1]["avg_score"])
    )
    return ordered[0][0]


def get_category_label(category_key):
    mapping = {
        "english": "English",
        "math": "Math",
        "analysis": "Analysis",
    }
    return mapping.get(category_key, category_key.title() if category_key else "Unknown")


def get_user_active_premium_types(user):
    accesses = UserPremiumAccess.objects.filter(user=user, is_active=True)
    return [a.premium_type for a in accesses if a.is_valid()]


def get_recommended_tests(user, weakest_category):
    attempted_test_ids = TestAttempt.objects.filter(user=user).values_list('test_id', flat=True)
    active_premium_types = get_user_active_premium_types(user)

    tests = Test.objects.filter(
        is_published=True,
        category=weakest_category
    ).exclude(id__in=attempted_test_ids).order_by('-created_at')

    visible_tests = [
        t for t in tests
        if (not t.is_premium) or (t.category in active_premium_types) or user.is_staff or user.is_superuser
    ]

    if visible_tests:
        return visible_tests[:3]

    fallback_tests = Test.objects.filter(
        is_published=True
    ).exclude(id__in=attempted_test_ids).order_by('-created_at')

    visible_fallback = [
        t for t in fallback_tests
        if (not t.is_premium) or (t.category in active_premium_types) or user.is_staff or user.is_superuser
    ]

    return visible_fallback[:3]


def get_recommended_videos(user, weakest_category):
    active_premium_types = get_user_active_premium_types(user)

    videos = VideoCourse.objects.filter(
        category=weakest_category
    ).order_by('-created_at')

    visible_videos = [
        v for v in videos
        if (not v.is_premium) or (v.category in active_premium_types) or user.is_staff or user.is_superuser
    ]

    if visible_videos:
        return visible_videos[:3]

    fallback_videos = VideoCourse.objects.all().order_by('-created_at')
    visible_fallback = [
        v for v in fallback_videos
        if (not v.is_premium) or (v.category in active_premium_types) or user.is_staff or user.is_superuser
    ]

    return visible_fallback[:3]


def get_weekly_goal_data(user):
    week_ago = timezone.now() - timedelta(days=7)
    attempts_7d = TestAttempt.objects.filter(
        user=user,
        completed_at__gte=week_ago
    ).count()

    weekly_goal = 3
    remaining = max(weekly_goal - attempts_7d, 0)

    if attempts_7d >= weekly_goal:
        message = "Ajoyib! Bu haftalik maqsad bajarilgan."
    elif attempts_7d == 2:
        message = "Zo‘r ketayapsiz. Yana 1 ta test ishlasangiz haftalik goal bajariladi."
    elif attempts_7d == 1:
        message = "Yaxshi boshlanish. Yana 2 ta test bilan haftalik maqsadga yetasiz."
    else:
        message = "Bu hafta kamroq ishlangansiz. Kamida 3 ta test bajarishni tavsiya qilaman."

    return {
        "weekly_goal": weekly_goal,
        "attempts_7d": attempts_7d,
        "remaining": remaining,
        "message": message,
    }


def build_recommendation_data(user, category_stats):
    weakest_category = get_weakest_category(category_stats)
    weakest_category_label = get_category_label(weakest_category) if weakest_category else None

    if not weakest_category:
        recommended_tests = Test.objects.filter(is_published=True, is_premium=False).order_by('-created_at')[:3]
        recommended_videos = VideoCourse.objects.filter(is_premium=False).order_by('-created_at')[:3]

        return {
            "has_data": False,
            "weakest_category": None,
            "weakest_category_label": None,
            "reason": "Hali yetarli attempt yo‘q. Boshlash uchun yangi test va videolar tavsiya qilindi.",
            "recommended_tests": recommended_tests,
            "recommended_videos": recommended_videos,
            **get_weekly_goal_data(user),
        }

    recommended_tests = get_recommended_tests(user, weakest_category)
    recommended_videos = get_recommended_videos(user, weakest_category)

    return {
        "has_data": True,
        "weakest_category": weakest_category,
        "weakest_category_label": weakest_category_label,
        "reason": f"Sizning eng sust yo‘nalishingiz hozircha {weakest_category_label}. Shu yo‘nalishda ko‘proq practice qilish tavsiya qilinadi.",
        "recommended_tests": recommended_tests,
        "recommended_videos": recommended_videos,
        **get_weekly_goal_data(user),
    }


def build_leaderboard():
    leaderboard_qs = (
        TestAttempt.objects
        .filter(user__isnull=False)
        .values('user', 'user__username')
        .annotate(
            best_score=Max('score'),
            avg_score=Avg('score'),
            total_attempts=Count('id'),
            last_activity=Max('completed_at')
        )
        .order_by('-best_score', '-avg_score', '-total_attempts', '-last_activity')
    )

    leaderboard = []
    for index, row in enumerate(leaderboard_qs, start=1):
        leaderboard.append({
            "rank": index,
            "user_id": row["user"],
            "username": row["user__username"],
            "best_score": row["best_score"] or 0,
            "avg_score": round(row["avg_score"] or 0),
            "total_attempts": row["total_attempts"] or 0,
            "last_activity": row["last_activity"],
        })
    return leaderboard


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    attempts = list(
        TestAttempt.objects.filter(user=request.user)
        .select_related('test')
        .order_by('-completed_at')
    )

    total_attempts = len(attempts)
    last_attempts = attempts[:5]

    best_score = max([a.score for a in attempts], default=0)
    avg_score = round(sum(a.score for a in attempts) / total_attempts) if total_attempts else 0
    avg_percentage = round(sum(float(a.percentage) for a in attempts) / total_attempts, 1) if total_attempts else 0

    streak_days = get_streak_days(attempts)
    badge = get_user_badge(best_score)

    premium_accesses = UserPremiumAccess.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('premium_type')

    active_premiums = [p for p in premium_accesses if p.is_valid()]

    category_stats = build_category_stats(attempts)
    recommendation_data = build_recommendation_data(request.user, category_stats)

    leaderboard = build_leaderboard()
    top_10 = leaderboard[:10]

    my_rank = None
    for row in leaderboard:
        if row["user_id"] == request.user.id:
            my_rank = row
            break

    return render(request, 'exam/profile.html', {
        'profile': profile,
        'total_attempts': total_attempts,
        'best_score': best_score,
        'avg_score': avg_score,
        'avg_percentage': avg_percentage,
        'streak_days': streak_days,
        'badge': badge,
        'last_attempts': last_attempts,
        'active_premiums': active_premiums,
        'category_stats': category_stats,
        'recommendation_data': recommendation_data,
        'leaderboard_preview': top_10,
        'my_rank': my_rank,
    })


@login_required
def leaderboard_view(request):
    leaderboard = build_leaderboard()

    my_rank = None
    for row in leaderboard:
        if row["user_id"] == request.user.id:
            my_rank = row
            break

    return render(request, 'exam/leaderboard.html', {
        'leaderboard': leaderboard,
        'my_rank': my_rank,
    })


@login_required
def edit_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil muvaffaqiyatli yangilandi.")
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, 'exam/edit_profile.html', {'form': form})