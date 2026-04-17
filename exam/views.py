from .views_home import home
from .views_auth import login_view, register, custom_logout
from .views_profile import profile_view, edit_profile, leaderboard_view
from .views_tests import take_pdf_test, submit_pdf_test, check_access
from .views_admin import admin_panel, users_list, give_premium, delete_test, delete_video, create_admin
from .views_uploads import create_video, upload_sat_pdf, upload_latex_test, upload_pdf_bank, append_pdf_bank
from .views_career import career_mode_view, career_watch_video, career_test_view
from .views_career_admin import (
    career_manager,
    career_video_create,
    career_test_create,
    career_topic_create,
    career_topic_edit,
    career_topic_delete,
)
from .views_score import score_calculator_view