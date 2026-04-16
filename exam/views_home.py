from django.shortcuts import render

from .models import Test, VideoCourse, UserPremiumAccess


def home(request):
    english_tests = Test.objects.filter(is_published=True, is_premium=False, category='english')
    math_tests = Test.objects.filter(is_published=True, is_premium=False, category='math')
    analysis_videos = VideoCourse.objects.filter(is_premium=False, category='analysis')

    premium_english_tests = Test.objects.filter(is_published=True, is_premium=True, category='english')
    premium_math_tests = Test.objects.filter(is_published=True, is_premium=True, category='math')
    premium_analysis_videos = VideoCourse.objects.filter(is_premium=True, category='analysis')

    user_premiums = []
    if request.user.is_authenticated:
        accesses = UserPremiumAccess.objects.filter(user=request.user, is_active=True)
        user_premiums = [a.premium_type for a in accesses if a.is_valid()]

    return render(request, 'exam/home.html', {
        'english_tests': english_tests,
        'math_tests': math_tests,
        'analysis_videos': analysis_videos,
        'premium_english_tests': premium_english_tests,
        'premium_math_tests': premium_math_tests,
        'premium_analysis_videos': premium_analysis_videos,
        'user_premiums': user_premiums,
    })