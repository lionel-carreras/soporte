from django.conf import settings
from django.db import models

class Message(models.Model):
    ticket      = models.ForeignKey(
        'soporte.Ticket',
        on_delete=models.CASCADE,
        related_name='mensajes',
        null=True,
        blank=True
    )
    contenido   = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    leido       = models.BooleanField(default=False)
    emisor      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mensajes_enviados'
    )
    receptor    = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mensajes_recibidos'
    )

    def __str__(self):
        return f"[{self.ticket.id}] {self.emisor} → {self.receptor}: {self.contenido[:20]}"
    

class Attachment(models.Model):
    message     = models.ForeignKey(
        'messenger.Message',
        on_delete=models.CASCADE,
        related_name='attachments'
    )
    file        = models.FileField(
        upload_to='attachments/',
        verbose_name="Archivo adjunto"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Adjunto {self.id} para mensaje {self.message.id}"