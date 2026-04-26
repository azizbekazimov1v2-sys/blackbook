from django.urls import path

from .views_home import home
from .views_auth import login_view, register, custom_logout
from .views_profile import profile_view, edit_profile, leaderboard_view

from .views_tests import (
    take_pdf_test,
    submit_pdf_test,
    check_access,
    pdf_proxy,
    add_test_comment,
    delete_comment,
)

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
    add_video_comment,
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

from .views_duel import (
    duel_mode,
    create_duel,
    accept_duel,
    cancel_duel,
    start_duel,
    duel_result,
)


urlpatterns = [
    # HOME
    path('', home, name='home'),

    # AUTH
    path('login/', login_view, name='login'),
    path('register/', register, name='register'),
    path('logout/', custom_logout, name='logout'),

    # PROFILE
    path('profile/', profile_view, name='profile'),
    path('edit-profile/', edit_profile, name='edit_profile'),
    path('profile/edit/', edit_profile, name='edit_profile_alt'),
    path('leaderboard/', leaderboard_view, name='leaderboard'),

    # TESTS
    path('take-pdf-test/<int:test_id>/', take_pdf_test, name='take_pdf_test'),
    path('submit-pdf-test/<int:test_id>/', submit_pdf_test, name='submit_pdf_test'),

    # Eski linklar buzilmasin uchun
    path('test/<int:test_id>/', take_pdf_test, name='take_pdf_test_alt'),
    path('test/<int:test_id>/submit/', submit_pdf_test, name='submit_pdf_test_alt'),

    path('check-access/<str:content_type>/<int:content_id>/', check_access, name='check_access'),
    path('pdf-proxy/<int:test_id>/', pdf_proxy, name='pdf_proxy'),

    # COMMENTS
    path('test/<int:test_id>/comment/', add_test_comment, name='add_test_comment'),
    path('video/<int:video_id>/comment/', add_video_comment, name='add_video_comment'),
    path('comment/delete/<int:comment_id>/', delete_comment, name='delete_comment'),

    # ADMIN PANEL
    path('admin-panel/', admin_panel, name='admin_panel'),
    path('users/', users_list, name='users_list'),
    path('admin-panel/users/', users_list, name='users_list_alt'),

    path('give-premium/<int:user_id>/<str:premium_type>/', give_premium, name='give_premium'),
    path('admin-panel/give-premium/<int:user_id>/<str:premium_type>/', give_premium, name='give_premium_alt'),

    path('delete-test/<int:test_id>/', delete_test, name='delete_test'),
    path('delete-video/<int:video_id>/', delete_video, name='delete_video'),

    path('admin-panel/delete-test/<int:test_id>/', delete_test, name='delete_test_alt'),
    path('admin-panel/delete-video/<int:video_id>/', delete_video, name='delete_video_alt'),

    path('admin-panel/create-admin/', create_admin, name='create_admin'),

    path('edit-test/<int:test_id>/', edit_test, name='edit_test'),
    path('edit-video/<int:video_id>/', edit_video, name='edit_video'),

    path('admin-panel/edit-test/<int:test_id>/', edit_test, name='edit_test_alt'),
    path('admin-panel/edit-video/<int:video_id>/', edit_video, name='edit_video_alt'),

    # UPLOADS
    path('create-video/', create_video, name='create_video'),
    path('upload/video/', create_video, name='create_video_alt'),

    path('upload-sat-pdf/', upload_sat_pdf, name='upload_sat_pdf'),
    path('upload/sat-pdf/', upload_sat_pdf, name='upload_sat_pdf_alt'),

    path('upload-latex-test/', upload_latex_test, name='upload_latex_test'),
    path('upload/latex-test/', upload_latex_test, name='upload_latex_test_alt'),

    path('upload-pdf-bank/', upload_pdf_bank, name='upload_pdf_bank'),
    path('upload/pdf-bank/', upload_pdf_bank, name='upload_pdf_bank_alt'),

    path('append-pdf-bank/<int:test_id>/', append_pdf_bank, name='append_pdf_bank'),

    # CAREER MODE
    path('career-mode/', career_mode_view, name='career_mode'),
    path('career/', career_mode_view, name='career_mode_alt'),

    path('career-watch-video/<int:topic_id>/', career_watch_video, name='career_watch_video'),
    path('career-test/<int:topic_id>/', career_test_view, name='career_test'),

    path('secure-video/<int:topic_id>/', secure_video_stream, name='secure_video'),

    # CAREER ADMIN
    path('career-manager/', career_manager, name='career_manager'),
    path('career-video-create/', career_video_create, name='career_video_create'),
    path('career-test-create/', career_test_create, name='career_test_create'),
    path('career-topic-create/', career_topic_create, name='career_topic_create'),
    path('career-topic-edit/<int:topic_id>/', career_topic_edit, name='career_topic_edit'),
    path('career-topic-delete/<int:topic_id>/', career_topic_delete, name='career_topic_delete'),

    # SCORE CALCULATOR
    path('score-calculator/', score_calculator_view, name='score_calculator'),

    # DUEL MODE
    path('duel/', duel_mode, name='duel_mode'),
    path('duels/', duel_mode, name='duel_list'),

    path('duel/create/', create_duel, name='create_duel'),
    path('duel/<int:duel_id>/accept/', accept_duel, name='accept_duel'),
    path('duel/<int:duel_id>/cancel/', cancel_duel, name='cancel_duel'),
    path('duel/<int:duel_id>/start/', start_duel, name='start_duel'),
    path('duel/<int:duel_id>/result/', duel_result, name='duel_result'),
]