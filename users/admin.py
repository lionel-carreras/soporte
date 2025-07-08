
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.contrib import admin


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Mostrar los campos por defecto de UserAdmin y añadir la sucursal
    list_display = UserAdmin.list_display + ('sucursal',)

    fieldsets = UserAdmin.fieldsets + (
        ('Datos Adicionales', {
            'fields': ('sucursal',),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Datos Adicionales', {
            'fields': ('sucursal',),
        }),
    )


