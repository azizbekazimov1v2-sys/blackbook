from django.urls import path
from .views_home import home
from .views_auth import login_view, register, custom_logout
from .views_profile import profile_view, edit_profile, leaderboard_view
from .views_tests import take_pdf_test, submit_pdf_test, check_access, pdf_proxy
from .views_admin import (
    admin_panel,
    users_list,
    give_premium,
    delete_test,
    delete_video,
    create_admin,
    edit_test,
    edit_video,
)
from .views_uploads import (
    create_video,
    upload_sat_pdf,
    upload_latex_test,
    upload_pdf_bank,
    append_pdf_bank,
)
from .views_career import (
    career_mode_view,
    career_watch_video,
    career_test_view,
    secure_video_stream,
)
from .views_career_admin import (
    career_manager,
    career_video_create,
    career_test_create,
    career_topic_create,
    career_topic_edit,
    career_topic_delete,
)
from .views_score import score_calculator_view
from .views_duel import (  # Yangi importlar
    duel_list,
    create_duel,
    accept_duel,
    cancel_duel,
    take_duel_test,
    submit_duel_test,
    duel_result,
)

urlpatterns = [
    # Home
    path('', home, name='home'),

    # Auth
    path('login/', login_view, name='login'),
    path('register/', register, name='register'),
    path('logout/', custom_logout, name='logout'),

    # Profile
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('leaderboard/', leaderboard_view, name='leaderboard'),

    # Tests
    path('test/<int:test_id>/', take_pdf_test, name='take_pdf_test'),
    path('test/<int:test_id>/submit/', submit_pdf_test, name='submit_pdf_test'),
    path('check-access/<str:content_type>/<int:content_id>/', check_access, name='check_access'),
    path('pdf-proxy/<str:file_path>/', pdf_proxy, name='pdf_proxy'),

    # Admin
    path('admin-panel/', admin_panel, name='admin_panel'),
    path('admin-panel/users/', users_list, name='users_list'),
    path('admin-panel/give-premium/<int:user_id>/', give_premium, name='give_premium'),
    path('admin-panel/delete-test/<int:test_id>/', delete_test, name='delete_test'),
    path('admin-panel/delete-video/<int:video_id>/', delete_video, name='delete_video'),
    path('admin-panel/create-admin/', create_admin, name='create_admin'),
    path('admin-panel/edit-test/<int:test_id>/', edit_test, name='edit_test'),
    path('admin-panel/edit-video/<int:video_id>/', edit_video, name='edit_video'),

    # Uploads
    path('upload/video/', create_video, name='create_video'),
    path('upload/sat-pdf/', upload_sat_pdf, name='upload_sat_pdf'),
    path('upload/latex-test/', upload_latex_test, name='upload_latex_test'),
    path('upload/pdf-bank/', upload_pdf_bank, name='upload_pdf_bank'),
    path('upload/append-pdf-bank/', append_pdf_bank, name='append_pdf_bank'),

    # Career Mode
    path('career/', career_mode_view, name='career_mode'),
    path('career/video/<int:video_id>/', career_watch_video, name='career_watch_video'),
    path('career/test/<int:test_id>/', career_test_view, name='career_test_view'),
    path('career/stream/<str:video_id>/', secure_video_stream, name='secure_video_stream'),

    # Career Admin
    path('career/manager/', career_manager, name='career_manager'),
    path('career/video/create/', career_video_create, name='career_video_create'),
    path('career/test/create/', career_test_create, name='career_test_create'),
    path('career/topic/create/', career_topic_create, name='career_topic_create'),
    path('career/topic/<int:topic_id>/edit/', career_topic_edit, name='career_topic_edit'),
    path('career/topic/<int:topic_id>/delete/', career_topic_delete, name='career_topic_delete'),

    # Score Calculator
    path('score-calculator/', score_calculator_view, name='score_calculator'),

    # Duel Mode (yangi qo'shilgan URL'lar)
    path('duels/', duel_list, name='duel_list'),
    path('duel/create/', create_duel, name='create_duel'),
    path('duel/<int:duel_id>/accept/', accept_duel, name='accept_duel'),
    path('duel/<int:duel_id>/cancel/', cancel_duel, name='cancel_duel'),
    path('duel/<int:duel_id>/take/', take_duel_test, name='take_duel_test'),
    path('duel/<int:duel_id>/submit/', submit_duel_test, name='submit_duel_test'),
    path('duel/<int:duel_id>/result/', duel_result, name='duel_result'),
]