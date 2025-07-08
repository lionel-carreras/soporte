
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.conf import settings
from django.contrib import messages
from django.contrib.messages import get_messages


class RoleBasedLoginView(LoginView):
    template_name = 'users/login.html'

    def get(self, request, *args, **kwargs):
        # Consumir cualquier mensaje pendiente para que no aparezca en el login
        list(get_messages(request))
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        """
        Se llama cuando las credenciales son válidas.
        """
        # Primero, logueamos al usuario
        user = form.get_user()
        login(self.request, user)

        # Si es usuario y debe cambiar la contraseña, forzamos ese paso
        if user.groups.filter(name='usuario').exists() and getattr(user, 'must_change_password', False):
            return redirect('users:password_change')

        # Si pasó el cambio (o no aplica), vamos al dashboard correspondiente
        if user.is_superuser:
            return redirect(reverse_lazy('soporte:dashboard_superadmin'))
        if user.groups.filter(name='agente').exists():
            return redirect(reverse_lazy('soporte:dashboard_agente'))
        if user.groups.filter(name='usuario').exists():
            return redirect(reverse_lazy('soporte:dashboard_usuario'))

        # Fallback al setting o al super
        return redirect(settings.LOGIN_REDIRECT_URL or super().get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, "Usuario o contraseña incorrectos.")
        return super().form_invalid(form)

class FirstTimePasswordChangeView(PasswordChangeView):
    template_name = 'soporte/usuarios/password_change.html'
    success_url   = reverse_lazy('soporte:dashboard_usuario')

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        user.must_change_password = False
        user.save(update_fields=['must_change_password'])
        return response
