
from django.conf import settings
from django.db import models




class EstadoTicket(models.Model):
    nombre = models.CharField("Estado", max_length=50, unique=True)

    class Meta:
        verbose_name = "Estado de Ticket"
        verbose_name_plural = "Estados de Ticket"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


    
class CategoriaProblema(models.Model):
    nombre = models.CharField("Nombre de Categoría", max_length=100, unique=True)

    class Meta:
        verbose_name = "Categoría de Problema"
        verbose_name_plural = "Categorías de Problema"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class ProblemaComun(models.Model):
    categoria     = models.ForeignKey(
        CategoriaProblema,
        verbose_name="Categoría",
        on_delete=models.PROTECT,
        null=True, blank=True,
        
    )
    nombre        = models.CharField("Nombre del problema", max_length=200, unique=True)
    codigo_error  = models.CharField("Código de error", max_length=50, unique=True, null=True, blank=True)
    solucion      = models.TextField("Solución", null=True, blank=True)
    imagen        = models.ImageField("Imagen de error",upload_to="problemas_comunes/",null=True, blank=True)
    fecha_creado      = models.DateTimeField("Creado el", auto_now_add=True)
    fecha_actualizado = models.DateTimeField("Actualizado el", auto_now=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = "Problema Común"
        verbose_name_plural = "Problemas Comunes"

    def __str__(self):
        return f"{self.nombre} ({self.codigo_error})"


class Ticket(models.Model):
    titulo           = models.CharField("Título", max_length=200)
    descripcion      = models.TextField("Descripción", blank=True)
    creado_por       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Creado por",
        related_name="tickets_creados",
        on_delete=models.CASCADE
    )
    asignado_a       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Asignado a",
        related_name="tickets_asignados",
        null=True, blank=True,
        on_delete=models.SET_NULL
    )
    estado           = models.ForeignKey(
        EstadoTicket,
        verbose_name="Estado",
        on_delete=models.PROTECT
    )

    # ← Aquí va la relación a Sucursal del ticket
    sucursal = models.ForeignKey('soporte.Sucursal',verbose_name="Sucursal del ticket",on_delete=models.PROTECT,db_column='sucursalid_ticket'
    )

    usuario_ip = models.CharField(
        "IP del usuario",
        max_length=20,
        null=True,
        blank=True
    )

    categoria = models.ForeignKey(
        CategoriaProblema,
        verbose_name="Categoría del problema",
        null=True, blank=True,
        on_delete=models.PROTECT,
        related_name='tickets_por_categoria'
    )
    
    problema = models.ForeignKey(
        ProblemaComun,
        verbose_name="Problema común",
        null=True, blank=True,
        on_delete=models.PROTECT,
        related_name='tickets_por_problema'
    )
    
    imagen_error     = models.ImageField(
        "Imagen del error",
        upload_to="tickets/",
        null=True, blank=True
    )

    motivo_anulacion = models.TextField("Motivo de anulación", null=True, blank=True)
    motivo_reapertura  = models.TextField("Motivo de reapertura",  null=True, blank=True)

    fecha_creado     = models.DateTimeField("Fecha de creación", auto_now_add=True)
    fecha_actualizado= models.DateTimeField("Fecha de actualización", auto_now=True)

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"
        ordering = ['-fecha_creado']

    def __str__(self):
        return f"{self.titulo} ({self.estado.nombre})"

    def get_absolute_url(self):
        # Ajusta el nombre de la URL según tu urls.py
        from django.urls import reverse
        return reverse('soporte:detail_ticket', args=[self.pk])
    
    

class Sucursal(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField("Nombre de la Sucursal", max_length=100, unique=True, null=True, blank=True)

    class Meta:
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"
        ordering = ['id']

    def __str__(self):
        return self.nombre

class TicketImage(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        related_name='imagenes',
        on_delete=models.CASCADE,
        verbose_name="Ticket"
    )
    imagen = models.ImageField(
        "Imagen",
        upload_to="tickets/images/"
    )

    def __str__(self):
        return f"Imagen de ticket #{self.ticket.id}"


class Respuesta_pred(models.Model):
    respuesta = models.CharField("Título", max_length=2000)

    def __str__(self):
        return self.respuesta