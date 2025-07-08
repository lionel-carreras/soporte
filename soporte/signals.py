from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import Ticket
from .webpubsub import send_notification
from messenger.models import Message
from django.urls import reverse


User = get_user_model()

@receiver(post_save, sender=Ticket)
def ticket_alert(sender, instance, created, **kwargs):
    # Generar ambas URLs
    url_usuario = reverse('soporte:detalle_ticket', args=[instance.pk])
    url_agente  = reverse('soporte:detail_ticket', args=[instance.pk])

    if created:
        msg = f"Nuevo ticket #{instance.id}: {instance.titulo}"
        agentes = User.objects.filter(groups__name='agente', is_active=True)
        for ag in agentes:
            send_notification(
                user_id=ag.id,
                message=msg,
                url=url_agente,
                notification_type='ticket'
            )
    else:
        msg = f"Ticket #{instance.id} estado: {instance.estado.nombre}"
        send_notification(
            user_id=instance.creado_por.id,
            message=msg,
            url=url_usuario,
            notification_type='ticket'
        )

@receiver(post_save, sender=Message)
def message_alert(sender, instance, created, **kwargs):
    if not created:
        return
    ticket = instance.ticket
    texto = f"📨 Nuevo mensaje en ticket #{ticket.id} de {instance.emisor.username}"

    # Elegir URL según si el receptor es agente o usuario
    if instance.receptor.groups.filter(name='agente').exists():
        url = reverse('soporte:detail_ticket', args=[ticket.pk])
    else:
        url = reverse('soporte:detalle_ticket', args=[ticket.pk])

    send_notification(
        user_id=instance.receptor.id,
        message=texto,
        url=url,
        notification_type='message'
    )