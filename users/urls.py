# ticket/users/urls.py

from django.urls import path
from .views import RoleBasedLoginView
from django.contrib.auth import views as auth_views
from .views import FirstTimePasswordChangeView

app_name = 'users'

urlpatterns = [
    path(
        '',
        RoleBasedLoginView.as_view(),
        name='login'
    ),
    path(
        'logout/',
        auth_views.LogoutView.as_view(next_page='users:login'),
        name='logout'
    ),

    # Forzar cambio de contraseña la primera vez
    path(
        'password_change/',
        FirstTimePasswordChangeView.as_view(),
        name='password_change'
    ),
    path(
        'password_change/done/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='users/password_change_done.html'
        ),
        name='password_change_done'
    ),
]

