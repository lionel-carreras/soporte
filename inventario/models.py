from django.db import models

class Impresora(models.Model):
    CONEXION_CHOICES = [
        ("IP", "IP"),
        ("USB", "USB"),
    ]
    PROPIEDAD_CHOICES = [
        ("PROPIA", "Propia"),
        ("ALQUILER", "Alquiler"),
    ]

    marca      = models.CharField(max_length=80)
    modelo     = models.CharField(max_length=120)
    nro_serie  = models.CharField("N° de serie", max_length=120, unique=True)
    # referencia perezosa para evitar import circular
    sucursal   = models.ForeignKey('soporte.Sucursal', on_delete=models.PROTECT, related_name="impresoras")
    conexion   = models.CharField(max_length=3, choices=CONEXION_CHOICES)
    ip = models.CharField("IP / PC", max_length=120, blank=True, default="")
    propiedad  = models.CharField(max_length=8, choices=PROPIEDAD_CHOICES)
    activa     = models.BooleanField(default=True)

    # opcionales
    ubicacion  = models.CharField(max_length=120, blank=True, default="", help_text="Ej: Administración, Depósito")
    notas      = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sucursal__nombre", "marca", "modelo"]
        verbose_name = "Impresora"
        verbose_name_plural = "Impresoras"
        indexes = [
            models.Index(fields=["nro_serie"]),            # búsquedas por serie
            models.Index(fields=["ip"]),                   # búsquedas por IP
            models.Index(fields=["marca", "modelo"]),      # filtros comunes
            models.Index(fields=["sucursal", "activa"]),   # listados por suc/estado
        ]

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.nro_serie})"
