from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    sucursal = models.ForeignKey(
        'soporte.Sucursal',
        verbose_name="Sucursal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='sucursalid_usuario',
    )
    must_change_password = models.BooleanField(
        default=True,
        help_text="Si es True, el usuario debe cambiar la contraseña en su próximo inicio de sesión."
    )
