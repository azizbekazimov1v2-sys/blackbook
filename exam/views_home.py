from django.shortcuts import render
from django.contrib.auth.models import User
from django.db.models import Q

from .models import Test, VideoCourse, UserPremiumAccess, Duel


def home(request):
    # Free testlar
    english_tests = Test.objects.filter(
        is_published=True,
        is_premium=False,
        category='english'
    ).order_by('-created_at')

    math_tests = Test.objects.filter(
        is_published=True,
        is_premium=False,
        category='math'
    ).order_by('-created_at')

    # Free analysis videolar
    analysis_videos = VideoCourse.objects.filter(
        is_premium=False,
        category='analysis'
    ).order_by('-created_at')

    # Premium testlar
    premium_english_tests = Test.objects.filter(
        is_published=True,
        is_premium=True,
        category='english'
    ).order_by('-created_at')

    premium_math_tests = Test.objects.filter(
        is_published=True,
        is_premium=True,
        category='math'
    ).order_by('-created_at')

    # Premium analysis videolar
    premium_analysis_videos = VideoCourse.objects.filter(
        is_premium=True,
        category='analysis'
    ).order_by('-created_at')

    # Duel uchun barcha published testlar
    all_tests = Test.objects.filter(
        is_published=True
    ).order_by('-created_at')

    # Default qiymatlar
    user_premiums = []
    other_users = []
    active_duels = []
    pending_duels_count = 0

    if request.user.is_authenticated:
        # Premiumlar
        accesses = UserPremiumAccess.objects.filter(
            user=request.user,
            is_active=True
        )

        user_premiums = [
            access.premium_type
            for access in accesses
            if access.is_valid()
        ]

        # Duel uchun boshqa userlar
        other_users = User.objects.exclude(
            id=request.user.id
        ).order_by('username')

        # Userga tegishli duellar
        active_duels = Duel.objects.filter(
            Q(challenger=request.user) | Q(opponent=request.user)
        ).select_related(
            'test',
            'challenger',
            'opponent',
            'winner'
        ).order_by('-created_at')[:10]

        # Navbar notification uchun
        pending_duels_count = Duel.objects.filter(
            opponent=request.user,
            status='pending'
        ).count()

    return render(request, 'exam/home.html', {
        'english_tests': english_tests,
        'math_tests': math_tests,
        'analysis_videos': analysis_videos,

        'premium_english_tests': premium_english_tests,
        'premium_math_tests': premium_math_tests,
        'premium_analysis_videos': premium_analysis_videos,

        'user_premiums': user_premiums,

        # Duel context
        'all_tests': all_tests,
        'other_users': other_users,
        'active_duels': active_duels,
        'pending_duels_count': pending_duels_count,
    })