from django.urls import path
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from django.views.decorators.http import require_http_methods

from . import views, auth_views as custom_auth_views
from .custom_auth import login_with_2fa

urlpatterns = [
    # Redirection de la racine vers le dashboard
    path('', lambda request: redirect('dashboard'), name='home_redirect'),

    # ==============================
    # Auth
    # ==============================
    path('login/', login_with_2fa, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    
    # ==============================
    # 2FA Authentication
    # ==============================
    path('two-factor/verify/', custom_auth_views.two_factor_verify, name='two_factor_verify'),
    path('two-factor/toggle/', custom_auth_views.toggle_two_factor, name='toggle_two_factor'),
    path('two-factor/resend-code/', require_http_methods(['POST'])(custom_auth_views.resend_verification_code), name='resend_2fa_code'),
    
    # ==============================
    # Password Reset
    # ==============================
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
        success_url='/login/'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url='/login/'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),

    # ==============================
    # Password Change
    # ==============================
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change_form.html',
        success_url='/password_change/done/'
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'
    ), name='password_change_done'),

    # ==============================
    # Dashboard
    # ==============================
    path('dashboard/', views.dashboard, name='dashboard'),

    # ==============================
    # Events CRUD
    # ==============================
    path('add/private/', views.add_private_event, name='add_private_event'),
    path('add/public/', views.add_public_event, name='add_public_event'),
    path('edit/private/<int:event_id>/', views.edit_private_event, name='edit_private_event'),
    path('edit/public/<int:event_id>/', views.edit_public_event, name='edit_public_event'),
    path('delete/event/<int:event_id>/', views.delete_confirm, name='delete_event'),

    # ==============================
    # Event view & RSVP
    # ==============================
    path('event/<str:event_type>/<int:event_id>/', views.event_detail, name='event_detail'),
    path('join/<int:event_id>/', views.join_event, name='join_event'),
    path('events/<int:event_id>/join/', views.join_public_event, name='join_public_event'),
    path('rsvp/<uuid:token>/', views.rsvp, name='rsvp'),
    path('rsvp/<uuid:token>/confirm/', views.rsvp_confirm, name='rsvp_confirm'),

    # ==============================
    # Profile
    # ==============================
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # ==============================
    # Statistiques
    # ==============================
    path('statistiques/', views.statistiques, name='statistiques'),

    # Vue publique pour consulter le profil d'un utilisateur (visible par tous)
    path('user/<int:user_id>/', views.user_profile, name='user_profile'),

    # ==============================
    # Admin Statistics
    # ==============================
    path('admin/stats/', views.admin_stats, name='admin_stats'),

    # ==============================
    # Public pages
    # ==============================
    path('home/', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # ==============================
    # Public/Private event lists
    # ==============================
    path('public/', views.public_events, name='public_events'),
    path('private/', views.private_events, name='private_events'),

    path('join-public-event/<int:event_id>/', views.join_public_event, name='join_public_event'),

    # ==============================
    # Payments
    # ==============================
    path('payment/<int:event_id>/', views.payment_view, name='payment'),
    path('event/<int:event_id>/payment/', views.event_payment, name='event_payment'),

    path('payment_success/<int:event_id>/', views.payment_success, name='payment_success'),
]
