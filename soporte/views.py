

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Ticket, TicketImage, EstadoTicket, ProblemaComun, CategoriaProblema, Sucursal, Respuesta_pred
from django.utils import timezone
from datetime import timedelta, datetime
from .decorators import group_required
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib      import messages
from messenger.forms import MessageForm
from messenger.models import Message, Attachment
from azure.messaging.webpubsubservice import WebPubSubServiceClient
from azure.core.credentials import AzureKeyCredential
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Count
from users.models import CustomUser
from django.db.models import Count, F, ExpressionWrapper, DurationField, Avg, Q


User = get_user_model()


MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2 MB



def group_required(group_name):
    
    def in_group(u):
        return u.is_authenticated and u.groups.filter(name=group_name).exists()
    return user_passes_test(in_group, login_url='users:login')

@login_required
@group_required('usuario')
def dashboard_usuario(request):
    # 1) Sucursal del usuario
    sucursal = request.user.sucursal

    # 2) Obtener objetos EstadoTicket
    abierto   = EstadoTicket.objects.get(nombre='Abierto')
    reabierto = EstadoTicket.objects.get(nombre='Reabierto')
    asignado  = EstadoTicket.objects.get(nombre='Asignado')
    resuelto  = EstadoTicket.objects.get(nombre='Resuelto')

    # 3) Pendientes: sucursal == la suya, estado Abierto o Reabierto
    pendientes = (
        Ticket.objects
              .filter(sucursal=sucursal, estado__in=[abierto, reabierto])
              .select_related('estado', 'sucursal')
              .order_by('-fecha_creado')
    )

    # 4) Asignados: sucursal == la suya, estado Asignado
    asignados = (
        Ticket.objects
              .filter(sucursal=sucursal, estado=asignado)
              .select_related('estado', 'sucursal')
              .order_by('-fecha_creado')
    )

    # 5) Resueltos en las últimas 48 horas
    hace_48h = timezone.now() - timedelta(hours=48)
    resueltos = (
        Ticket.objects
              .filter(
                  sucursal=sucursal,
                  estado=resuelto,
                  fecha_actualizado__gte=hace_48h
              )
              .select_related('estado', 'sucursal')
              .order_by('-fecha_actualizado')
    )

    return render(request, 'soporte/usuarios/dashboard_usuario.html', {
        'pendientes': pendientes,
        'asignados':  asignados,
        'resueltos':  resueltos,
    })
    

@login_required
@group_required('agente')
def dashboard_agente(request):
    hoy = timezone.localdate()
    siete_dias_atras = hoy - timedelta(days=7)

    abiertos_id    = EstadoTicket.objects.get(nombre='Abierto').id
    reabiertos_id  = EstadoTicket.objects.get(nombre='Reabierto').id

    pendientes = (
        Ticket.objects
              .filter(Q(estado_id=abiertos_id) | Q(estado_id=reabiertos_id))
              .select_related('creado_por__sucursal', 'sucursal', 'estado')
              .order_by('-fecha_creado')
    )

    # Tickets asignados al agente actual (estado_id = 2)
    asignados = (
        Ticket.objects
            .filter(estado_id=2)  
            .select_related('creado_por__sucursal', 'sucursal', 'estado')
            .order_by('-fecha_creado')
    )

    # Tickets resueltos hoy (estado_id = 3, fecha_actualizado = hoy)
    resueltos = (
        Ticket.objects
              .filter(estado_id=3, fecha_actualizado__date=hoy)
              .select_related('creado_por__sucursal', 'sucursal', 'estado')
              .order_by('-fecha_actualizado')
    )

    # Traer todos los agentes (usuarios en grupo “agente”)
    agentes = User.objects.filter(groups__name='agente').order_by('username')

    return render(request, 'soporte/agentes/dashboard_agente.html', {
        'pendientes':  pendientes,
        'asignados': asignados,
        'resueltos': resueltos,
        'agentes':   agentes,
        
    })


@login_required
@group_required('agente')
def ticket_historico(request):
    
    hoy = timezone.localdate()
    siete_dias_atras = hoy - timedelta(days=7)

    # Obtener cadenas “YYYY-MM-DD” desde GET, o usar valores por defecto
    desde_str = request.GET.get('desde', siete_dias_atras.strftime('%Y-%m-%d'))
    hasta_str = request.GET.get('hasta',  hoy.strftime('%Y-%m-%d'))

    try:
        fecha_desde = datetime.strptime(desde_str, '%Y-%m-%d').date()
    except ValueError:
        fecha_desde = siete_dias_atras
        desde_str = fecha_desde.strftime('%Y-%m-%d')

    try:
        fecha_hasta = datetime.strptime(hasta_str, '%Y-%m-%d').date()
    except ValueError:
        fecha_hasta = hoy
        hasta_str = fecha_hasta.strftime('%Y-%m-%d')

    # Si el usuario puso fechas invertidas, corregir
    if fecha_desde > fecha_hasta:
        fecha_desde, fecha_hasta = fecha_hasta, fecha_desde
        desde_str = fecha_desde.strftime('%Y-%m-%d')
        hasta_str = fecha_hasta.strftime('%Y-%m-%d')

  
    resueltos = Ticket.objects.filter(
        asignado_a_id=request.user.id,
        estado_id=3,
        fecha_actualizado__date__gte=fecha_desde,
        fecha_actualizado__date__lte=fecha_hasta
    ).select_related( 'estado').order_by('-fecha_actualizado')


    anulados = Ticket.objects.filter(
        asignado_a_id=request.user.id,
        estado_id=5,
        fecha_actualizado__date__gte=fecha_desde,
        fecha_actualizado__date__lte=fecha_hasta
    ).select_related('estado').order_by('-fecha_actualizado')

    return render(request, 'soporte/agentes/historico_agente.html', {
        'resueltos':  resueltos,
        'anulados':   anulados,
        'desde':      desde_str,
        'hasta':      hasta_str,
    })



MAX_IMAGE_SIZE = 25 * 1024 * 1024  # 25 MB

@login_required
@group_required('usuario')
def ticket_create(request):
    categorias        = CategoriaProblema.objects.all().order_by('nombre')
    problemas         = ProblemaComun.objects.all().order_by('nombre')
    error             = ''
    descripcion_valor = ''

    if request.method == 'POST':
        categoria_id = request.POST.get('categoria')
        problema_id  = request.POST.get('problema')
        usuario_ip   = request.POST.get('ip', '').strip()
        descripcion  = request.POST.get('description', '').strip()
        imagenes     = request.FILES.getlist('imagenes')

        descripcion_valor = descripcion

        #  Validar tamaño
        for img in imagenes:
            if img.size > MAX_IMAGE_SIZE:
                error = "Cada imagen no puede superar los 25 MB."
                break

        if not error:
            #  Relaciones
            categoria      = CategoriaProblema.objects.filter(pk=categoria_id).first()
            problema       = ProblemaComun.objects.filter(pk=problema_id).first()
            estado_abierto = EstadoTicket.objects.get(nombre='Abierto')
            sucursal_sel   = request.user.sucursal  # ← sucursal del usuario

            #  Crear Ticket
            ticket = Ticket.objects.create(
                titulo        = problema.nombre if problema else "Sin título",
                descripcion   = descripcion,
                creado_por    = request.user,
                estado        = estado_abierto,
                sucursal      = sucursal_sel,
                usuario_ip    = usuario_ip,
                categoria     = categoria or (problema.categoria if problema else None),
                problema      = problema,
            )

            #  Guardar todas las imágenes
            for img in imagenes:
                TicketImage.objects.create(ticket=ticket, imagen=img)

            return redirect('soporte:dashboard_usuario')

    return render(request, 'soporte/usuarios/crear_ticket.html', {
        'categorias':        categorias,
        'problemas':         problemas,
        'error':             error,
        'descripcion_valor': descripcion_valor,
    })


    

@login_required
@group_required('agente')
def ticket_accept(request, ticket_id):
    """
    Al hacer POST en “Aceptar”, asigna el ticket al agente logeado (estado_id=2, asignado_a=request.user),
    actualiza la fecha y redirige de nuevo al Dashboard Agente.
    """
    if request.method != 'POST':
        return redirect('soporte:dashboard_agente')

    ticket = get_object_or_404(Ticket, pk=ticket_id)

    # Cambia estado a “Asignado” (estado_id = 2) y asigna al usuario de la sesión
    ticket.estado_id    = 2
    ticket.asignado_a   = request.user
    ticket.fecha_actualizado = timezone.now()
    ticket.save(update_fields=['estado_id', 'asignado_a', 'fecha_actualizado'])

    return redirect('soporte:dashboard_agente')

from django.contrib import messages


@login_required
@group_required('usuario')
def detalle_ticket(request, ticket_id):
    ticket   = get_object_or_404(Ticket, pk=ticket_id, creado_por=request.user)
    mensajes = ticket.mensajes.order_by('-fecha_envio')

    # 1) Si está cerrado o sin agente, muestro mensaje y corto
    if ticket.estado_id == 3:
        messages.info(request, "Este ticket está cerrado. No puedes enviar mensajes.")
        return render(request, 'soporte/usuarios/detalle_ticket.html', {
            'ticket':   ticket,
            'mensajes': mensajes,
        })

    if ticket.asignado_a is None:
        messages.warning(request, "Todavía no se ha asignado un agente a este ticket, no puedes enviar mensajes.")
        return render(request, 'soporte/usuarios/detalle_ticket.html', {
            'ticket':   ticket,
            'mensajes': mensajes,
        })

    # 2) Inicializo siempre el form (para que exista aunque no venga POST)
    form = MessageForm()

    # 3) Procesamiento POST
    if request.method == 'POST':
        # recojo tanto POST como FILES
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            texto = form.cleaned_data['contenido'].strip()
            archivos = request.FILES.getlist('attachments')

            # al menos texto o archivos
            if not texto and not archivos:
                messages.error(request, "Escribe algo o adjunta al menos un archivo.")
            else:
                # guardo el mensaje
                msg = form.save(commit=False)
                msg.ticket   = ticket
                msg.emisor   = request.user
                msg.receptor = ticket.asignado_a
                msg.save()

                # guardo cada adjunto
                for f in archivos:
                    Attachment.objects.create(message=msg, file=f)

                return redirect('soporte:detalle_ticket', ticket_id=ticket_id)

    # 4) Resto: pinto plantilla con el form (vací­o o con errores)
    return render(request, 'soporte/usuarios/detalle_ticket.html', {
        'ticket':   ticket,
        'mensajes': mensajes,
        'form':     form,
    })

@login_required
@group_required('agente')
def detail_ticket(request, ticket_id):
    ticket    = get_object_or_404(Ticket, pk=ticket_id)
    mensajes  = ticket.mensajes.order_by('-fecha_envio')
    is_agent  = request.user.groups.filter(name='agente').exists()
    respuestas = Respuesta_pred.objects.all()    # <–– añadí esta línea

    form = MessageForm()
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            texto    = form.cleaned_data['contenido'].strip()
            archivos = request.FILES.getlist('attachments')
            if not texto and not archivos:
                messages.error(request, "Escribe algo o adjunta al menos un archivo.")
            else:
                msg = form.save(commit=False)
                msg.ticket   = ticket
                msg.emisor   = request.user
                msg.receptor = ticket.creado_por
                msg.save()
                for f in archivos:
                    Attachment.objects.create(message=msg, file=f)
                return redirect('soporte:detail_ticket', ticket_id=ticket_id)

    return render(request, 'soporte/agentes/detail_ticket.html', {
        'ticket':    ticket,
        'mensajes':  mensajes,
        'form':      form,
        'is_agent':  is_agent,
        'respuestas': respuestas,   # <–– pásalas al template
    })

    
def logout_view(request):
    logout(request)
    return redirect(reverse(''))


@login_required
@group_required('agente')
def ticket_resolve(request, ticket_id):
    if request.method == 'POST':
        ticket = get_object_or_404(Ticket, pk=ticket_id)
        ticket.estado_id = 3
        ticket.fecha_actualizado = timezone.now()
        ticket.save(update_fields=['estado_id', 'fecha_actualizado'])
    return redirect('soporte:dashboard_agente')


@login_required
@group_required('agente')
def ticket_assign(request, ticket_id):
    if request.method == 'POST':
        ticket = get_object_or_404(Ticket, pk=ticket_id)
        agente_id = request.POST.get('agente_id')
        try:
            agente = User.objects.get(pk=agente_id, groups__name='agente')
        except User.DoesNotExist:
            return redirect('soporte:dashboard_agente')

        ticket.estado_id = 2
        ticket.asignado_a = agente
        ticket.fecha_actualizado = timezone.now()
        ticket.save(update_fields=['estado_id', 'asignado_a', 'fecha_actualizado'])
    return redirect('soporte:dashboard_agente')


@login_required
@group_required('usuario')
def anular_ticket_usuario(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id, creado_por=request.user)
    if ticket.estado_id not in (1, 2, 4):
        messages.error(request, "Solo puedes anular tickets abiertos o asignados.")
        return redirect('soporte:dashboard_usuario')
    motivo = request.POST.get('motivo', '').strip()
    if not motivo:
        messages.error(request, "Debes indicar un motivo de anulación.")
        return redirect('soporte:dashboard_usuario')
    ticket.motivo_anulacion = motivo
    ticket.estado_id = 5
    ticket.save()
    
    return redirect('soporte:dashboard_usuario')

@login_required
@group_required('agente')
def anular_ticket_agente(request, ticket_id):
    # Ya no filtramos por asignado_a
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    # Sólo permitimos anular si está Abierto (1) o Asignado (2)
    if ticket.estado_id not in (1, 2, 4):
        messages.error(request, "Solo puedes anular tickets abiertos o asignados.")
        return redirect('soporte:dashboard_agente')

    motivo = request.POST.get('motivo', '').strip()
    if not motivo:
        messages.error(request, "Debes indicar un motivo de anulación.")
        return redirect('soporte:dashboard_agente')

    ticket.motivo_anulacion = motivo
    ticket.estado_id = 5  # Anulado
    ticket.save()
    
    return redirect('soporte:dashboard_agente')



@login_required
def webpubsub_auth(request):
    user_id = request.user.id
    client = WebPubSubServiceClient(
        endpoint=settings.AZURE_WEBPUBSUB_ENDPOINT,
        credential=AzureKeyCredential(settings.AZURE_WEBPUBSUB_ACCESS_KEY),
        hub=settings.AZURE_WEBPUBSUB_HUB
    )
    token_data = client.get_client_access_token(
    user_id=str(user_id),
    
    roles=["webpubsub.joinLeaveGroup", "webpubsub.sendToGroup"],
    groups=[f"user_{user_id}"]
)
    
    return JsonResponse({"url": token_data["url"]})


# Solo superadmins:
def is_superadmin(u):
    return u.is_active and u.is_superuser



@user_passes_test(is_superadmin)
def superadmin_dashboard(request):
    # — filtros básicos
    start_date   = request.GET.get('start_date')
    end_date     = request.GET.get('end_date')
    agent_id     = request.GET.get('agent')
    user_id      = request.GET.get('user')
    sucursal_id  = request.GET.get('sucursal')
    categoria_id = request.GET.get('categoria')
    problema_id = request.GET.get('problema')

    qs = Ticket.objects.all()

    if start_date:
        qs = qs.filter(fecha_creado__date__gte=start_date)
    if end_date:
        qs = qs.filter(fecha_creado__date__lte=end_date)
    if agent_id:
        qs = qs.filter(asignado_a_id=agent_id)
    if user_id:
        qs = qs.filter(creado_por_id=user_id)
    if sucursal_id:
        qs = qs.filter(sucursal_id=sucursal_id)
    if categoria_id:
        qs = qs.filter(problema__categoria_id=categoria_id)
    if problema_id:
        qs = qs.filter(problema_id=problema_id)

    # — estadísticas de estado
    stats = {
        'totales':   qs.count(),
        'abiertos':  qs.filter(estado_id=1).count(),
        'asignados': qs.filter(estado_id=2).count(),
        'resueltos': qs.filter(estado_id=3).count(),
        'reabiertos':  qs.filter(estado_id=4).count(),
        'anulados':  qs.filter(estado_id=5).count(),
    }

    # — Top 5
    top_creadores = (
        CustomUser.objects
          .filter(tickets_creados__in=qs)
          .annotate(created_count=Count('tickets_creados'))
          .order_by('-created_count')[:5]
    )
    top_asignadores = (
        CustomUser.objects
          .filter(tickets_asignados__in=qs)
          .annotate(assigned_count=Count('tickets_asignados'))
          .order_by('-assigned_count')[:5]
    )
    top_resolutores = (
        CustomUser.objects
          .filter(tickets_asignados__in=qs.filter(estado_id=3))
          .annotate(resolved_count=Count('tickets_asignados'))
          .order_by('-resolved_count')[:5]
    )

    # — Motivos de anulación
    motivos_anulacion = (
        qs.filter(estado_id=4)
          .values('motivo_anulacion')
          .annotate(count=Count('id'))
          .order_by('-count')[:5]
    )

    # — Tiempo medio de resolución
    resolution_time = ExpressionWrapper(
        F('fecha_actualizado') - F('fecha_creado'),
        output_field=DurationField()
    )
    avg_resolution = (
        qs.filter(estado_id=3)
          .annotate(duration=resolution_time)
          .aggregate(avg_time=Avg('duration'))['avg_time']
    )

    # — Formatear para quitar los segundos
    if avg_resolution:
        total_sec = int(avg_resolution.total_seconds())
        days, rem = divmod(total_sec, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, _ = divmod(rem, 60)
        avg_resolution_str = f"{days}d {hours}h {minutes}m"
    else:
        avg_resolution_str = None
        
    # — Estadísticas “por categoría” y “por problema”:
    categorias_stats = (
      qs
        .exclude(problema__isnull=True)
        .values(categoria_nombre=F('problema__categoria__nombre'))
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    problemas_stats = (
        qs
        .exclude(problema__isnull=True)
        .values(problema_nombre=F('problema__nombre'))
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    # — Para los filtros:
    agentes    = CustomUser.objects.filter(groups__name='agente')
    usuarios = CustomUser.objects.filter(groups__name='usuario')
    sucursales = Sucursal.objects.all()
    categorias = CategoriaProblema.objects.all()
    problemas  = ProblemaComun.objects.all()

    context = {
      'stats':            stats,
      'top_creadores':    top_creadores,
      'top_asignadores':  top_asignadores,
      'top_resolutores':  top_resolutores,
      'motivos_anulacion': motivos_anulacion,
      'avg_resolution_str': avg_resolution_str,
      'categorias_stats': categorias_stats,
      'problemas_stats':  problemas_stats,
      'agentes':          agentes,
      'usuarios':         usuarios,
      'sucursales':       sucursales,
      'categorias':       categorias,
      'problemas':        problemas,
      'filtros': {
        'start_date': request.GET.get('start_date'),
        'end_date':   request.GET.get('end_date'),
        'agent_id':   request.GET.get('agent'),
        'user_id':    request.GET.get('user'),
        'sucursal_id':request.GET.get('sucursal'),
        'categoria_id': request.GET.get('categoria'),
        'problema_id':  request.GET.get('problema'),
      }
    }
    return render(request, 'soporte/admin/dashboard_superadmin.html', context)




@login_required
@group_required('superadmin')
def create_ticket(request):
    categorias        = CategoriaProblema.objects.all().order_by('nombre')
    problemas         = ProblemaComun.objects.all().order_by('nombre')
    sucursales        = Sucursal.objects.all().order_by('id')
    error             = ''
    descripcion_valor = ''

    if request.method == 'POST':
        categoria_id = request.POST.get('categoria')
        problema_id  = request.POST.get('problema')
        usuario_ip  = request.POST.get('ip')
        descripcion = request.POST.get('description', '').strip()
        imagen      = request.FILES.get('imagen')
        sucursal_id = request.POST.get('sucursal')      

        descripcion_valor = descripcion

        if imagen and imagen.size > MAX_IMAGE_SIZE:
            error = "La imagen no puede superar los 2 MB."
        else:
            categoria    = CategoriaProblema.objects.filter(pk=categoria_id).first()
            problema     = ProblemaComun.objects.filter(pk=problema_id).first()
            estado_abierto = EstadoTicket.objects.get(nombre='Abierto')
            sucursal_sel = Sucursal.objects.filter(pk=sucursal_id).first()

            if not sucursal_sel:
                error = "Seleccioná una sucursal válida."
            else:
                Ticket.objects.create(
                    titulo        = problema.nombre if problema else "Sin título",
                    descripcion   = descripcion,
                    creado_por    = request.user,
                    estado        = estado_abierto,
                    sucursal      = sucursal_sel,
                    usuario_ip      = usuario_ip,
                    imagen_error  = imagen,
                    categoria     = categoria if categoria else (problema.categoria if problema else None),
                    problema      = problema,
                )
                return redirect('soporte:dashboard_superadmin')

    return render(request, 'soporte/usuarios/crear_ticket.html', {
        'categorias':        categorias,
        'problemas':         problemas,
        'sucursales':        sucursales,
        'error':             error,
        'descripcion_valor': descripcion_valor,
    })

@login_required
@group_required('agente')
def ticket_reopen(request, ticket_id):
    if request.method == 'POST':
        ticket = get_object_or_404(Ticket, pk=ticket_id)
        motivo = request.POST.get('motivo', '').strip()
        if not motivo:
            messages.error(request, "Debes indicar un motivo de reapertura.")
        else:
            estado_reabierto = EstadoTicket.objects.get(nombre='Reabierto')
            ticket.estado            = estado_reabierto
            ticket.motivo_reapertura  = motivo
            ticket.asignado_a         = request.user
            ticket.fecha_actualizado  = timezone.now()
            ticket.save(update_fields=[
                'estado',
                'motivo_reapertura',
                'asignado_a',
                'fecha_actualizado',
            ])
            
    return redirect('soporte:dashboard_agente')



@login_required
@group_required('usuario') 
def ticket_reopen_user(request, ticket_id):
    if request.method == 'POST':
        ticket = get_object_or_404(Ticket, pk=ticket_id)
        motivo = request.POST.get('motivo', '').strip()
        if not motivo:
            messages.error(request, "Debes indicar un motivo de reapertura.")
        else:
            estado_abierto = EstadoTicket.objects.get(nombre='Reabierto')
            ticket.estado          = estado_abierto
            ticket.motivo_reapertura = motivo
            ticket.fecha_actualizado = timezone.now()
            ticket.save(update_fields=['estado','motivo_reapertura','fecha_actualizado'])
            messages.success(request, f"Ticket #{ticket.id} reabierto.")
    return redirect('soporte:dashboard_usuario')