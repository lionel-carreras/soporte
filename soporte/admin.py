from django.contrib import admin
from .models import EstadoTicket, Ticket, Sucursal, ProblemaComun, CategoriaProblema, Respuesta_pred



@admin.register(EstadoTicket)
class EstadoTicketAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display  = ('titulo', 'estado', 'creado_por', 'asignado_a', 'fecha_creado')
    list_filter   = ('estado', 'fecha_creado')
    search_fields = ('titulo', 'descripcion')

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'id')
    
@admin.register(CategoriaProblema)
class CategoriaProblemaAdmin(admin.ModelAdmin):
    list_display   = ('id', 'nombre')
    search_fields  = ('nombre',)

@admin.register(ProblemaComun)
class ProblemaComunAdmin(admin.ModelAdmin):
    list_display     = ('id', 'nombre', 'categoria', 'codigo_error')
    list_filter      = ('categoria',)
    search_fields    = ('nombre', 'codigo_error', 'categoria__nombre')
    autocomplete_fields = ('categoria',)  # si tienes muchos registros

    fieldsets = (
        (None, {
            'fields': ('categoria', 'nombre', 'codigo_error', 'solucion', 'imagen')
        }),

    )

@admin.register(Respuesta_pred)
class Respuesta_pred(admin.ModelAdmin):
    list_display = ('id', 'respuesta')
    
    