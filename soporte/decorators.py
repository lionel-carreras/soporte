

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def group_required(group_name):
    """
    Decorador que permite el acceso únicamente si el usuario está autenticado
    y pertenece al grupo cuyo nombre es `group_name`. En otro caso, lanza 403.
    """
    def in_group(u):
        return u.is_authenticated and u.groups.filter(name=group_name).exists()

    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not in_group(request.user):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view

    return decorator
