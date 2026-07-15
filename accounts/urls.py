from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import EmailAwareAuthenticationForm

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_landing, name='register_landing'),
    path('register/student/', views.register_student, name='register_student'),
    path('register/teacher/', views.register_teacher, name='register_teacher'),

    path(
        'verify/<str:uidb64>/<str:token>/',
        views.verify_email,
        name='verify_email',
    ),
    path('resend-verification/', views.resend_verification, name='resend_verification'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),


    path(
        'password-change/',
        auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html'),
        name='password_change',
    ),
    path(
        'password-change/done/',
        auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'),
        name='password_change_done',
    ),

    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/<str:username>/', views.profile_view, name='profile_detail'),
]
