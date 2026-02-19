from django.urls import path
from . import views

urlpatterns = [
    path('', views.indexview, name='home'),
    # path('predict/', views.predictview, name='predict'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path('google-verify/', views.google_verify_view, name='google_verify'),
    path('profile/<int:user_id>/', views.profile_view, name='profile_view'),
    path('profile/update/', views.profile_update_view, name='update_profile'),
    path('logout/', views.logout_view, name='logout'),
    path('delete-account/', views.delete_account_view, name='delete_account'),
    path('predict/', views.predictview, name='predict'),
    path('history/', views.history_view, name='history_view'),
    path('predict/', views.predictview, name='predict'),
    path('about/', views.about_view, name='about'),
    # 2. Add a new Solar System configuration
    path('add-system/', views.add_system, name='add_system'),
    
    # 3. Trigger AI Prediction (captures the specific system's ID)
    path('run-prediction/<int:system_id>/', views.run_prediction, name='run_prediction'),
    
    # 4. Submit Actual Power Data (maps to a specific system)
    path('update-actual/<int:system_id>/', views.update_actual_power, name='update_actual_power'),
    path('remove-system/<int:system_id>/', views.remove_system, name='remove_system'),
    path('delete-entry/<int:entry_id>/', views.delete_entry, name='delete_entry'),
    path('history/update/', views.manual_update_actual, name='manual_update_actual'),
    path('forgot-password-send-otp/', views.forgot_password_send_otp, name='forgot_password_send_otp'),
    path('forgot-password-verify-otp/', views.forgot_password_verify_otp, name='forgot_password_verify_otp'),
    path('reset-password-save/', views.reset_password_save, name='reset_password_save'),
]