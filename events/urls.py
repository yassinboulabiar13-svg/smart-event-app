from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add/', views.add_event, name='add_event'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='events/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('rsvp/<int:event_id>/<str:guest_email>/', views.rsvp, name='rsvp'),
]
