from django.contrib import admin
from .models import Impresora



@admin.register(Impresora)
class ImpresoraAdmin(admin.ModelAdmin):
    list_display  = ("marca", "modelo", "nro_serie", "sucursal", "conexion", "ip", "propiedad", "activa")
    list_filter   = ("sucursal", "conexion", "propiedad", "activa")
    search_fields = ("marca", "modelo", "nro_serie", "ip", "ubicacion")

