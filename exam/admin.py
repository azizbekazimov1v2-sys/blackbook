from django.contrib import admin
from .models import (
    Test,
    Question,
    VideoCourse,
    UserProfile,
    UserPremiumAccess,
    TestAttempt,
    TestAttemptAnswer,
    CareerVideo,
    CareerTest,
    CareerQuestion,
    CareerTopic,
    CareerProgress,
)


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'upload_mode',
        'total_questions',
        'pick_count',
        'randomize_questions',
        'is_premium',
        'is_published',
        'created_by',
    )
    list_filter = ('category', 'upload_mode', 'is_premium', 'is_published')
    search_fields = ('title', 'description')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('test', 'order', 'source_number', 'pdf_page', 'correct_choice')
    list_filter = ('test',)
    search_fields = ('text', 'correct_choice')


@admin.register(VideoCourse)
class VideoCourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_premium', 'created_by')
    list_filter = ('category', 'is_premium')
    search_fields = ('title', 'description')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)


@admin.register(UserPremiumAccess)
class UserPremiumAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'premium_type', 'is_active', 'expires_at')
    list_filter = ('premium_type', 'is_active')


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'score', 'percentage', 'completed_at')
    list_filter = ('test', 'user')


@admin.register(TestAttemptAnswer)
class TestAttemptAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'order', 'is_correct')


@admin.register(CareerVideo)
class CareerVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title', 'description')


@admin.register(CareerTest)
class CareerTestAdmin(admin.ModelAdmin):
    list_display = ('title', 'total_questions', 'time_limit_minutes', 'pass_percentage', 'created_at')
    search_fields = ('title', 'description')


@admin.register(CareerQuestion)
class CareerQuestionAdmin(admin.ModelAdmin):
    list_display = ('test', 'order', 'pdf_page', 'correct_answer')
    list_filter = ('test',)
    search_fields = ('test__title',)


@admin.register(CareerTopic)
class CareerTopicAdmin(admin.ModelAdmin):
    list_display = ('order', 'title', 'is_free', 'is_active', 'video', 'test')
    list_filter = ('is_free', 'is_active')
    search_fields = ('title', 'subtitle', 'description')
    ordering = ('order',)


@admin.register(CareerProgress)
class CareerProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic', 'video_done', 'test_passed', 'score_percent', 'updated_at')
    list_filter = ('video_done', 'test_passed')