from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.custom_logout, name='logout'),

    path('profile/', views.profile_view, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),

    path('career-mode/', views.career_mode_view, name='career_mode'),
    path('score-calculator/', views.score_calculator_view, name='score_calculator'),
    path('career-watch-video/<int:topic_id>/', views.career_watch_video, name='career_watch_video'),
    path('career-test/<int:topic_id>/', views.career_test_view, name='career_test'),

    path('career-manager/', views.career_manager, name='career_manager'),
    path('career-video-create/', views.career_video_create, name='career_video_create'),
    path('career-test-create/', views.career_test_create, name='career_test_create'),
    path('career-topic-create/', views.career_topic_create, name='career_topic_create'),
    path('career-topic-edit/<int:topic_id>/', views.career_topic_edit, name='career_topic_edit'),
    path('career-topic-delete/<int:topic_id>/', views.career_topic_delete, name='career_topic_delete'),

    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('users/', views.users_list, name='users_list'),
    path('give-premium/<int:user_id>/<str:premium_type>/', views.give_premium, name='give_premium'),

    path('upload-sat-pdf/', views.upload_sat_pdf, name='upload_sat_pdf'),
    path('upload-latex-test/', views.upload_latex_test, name='upload_latex_test'),
    path('upload-pdf-bank/', views.upload_pdf_bank, name='upload_pdf_bank'),
    path('append-pdf-bank/<int:test_id>/', views.append_pdf_bank, name='append_pdf_bank'),
    path('create-video/', views.create_video, name='create_video'),

    path('check-access/<str:content_type>/<int:content_id>/', views.check_access, name='check_access'),
    path('take-pdf-test/<int:test_id>/', views.take_pdf_test, name='take_pdf_test'),
    path('submit-pdf-test/<int:test_id>/', views.submit_pdf_test, name='submit_pdf_test'),

    path('delete-test/<int:test_id>/', views.delete_test, name='delete_test'),
    path('delete-video/<int:video_id>/', views.delete_video, name='delete_video'),
]