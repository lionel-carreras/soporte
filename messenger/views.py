from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Message
from .forms import MessageForm
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

User = get_user_model()

def group_required(group_name):
    
    def in_group(u):
        return u.is_authenticated and u.groups.filter(name=group_name).exists()
    return user_passes_test(in_group, login_url='users:login')


@login_required
def inbox(request):
    mensajes = Message.objects.filter(receptor=request.user)
    return render(request, 'messenger/inbox.html', {'mensajes': mensajes})


@login_required
def sent(request):
    mensajes = Message.objects.filter(emisor=request.user)
    return render(request, 'messenger/sent.html', {'mensajes': mensajes})


@login_required
def detail(request, pk):
    msg = get_object_or_404(
        Message,
        Q(emisor=request.user) | Q(receptor=request.user),
        pk=pk
    )
    return render(request, 'messenger/detail.html', {'msg': msg})


@login_required
def compose(request):
    if request.method == 'POST':
        form = MessageForm(request.POST, user=request.user)
        if form.is_valid():
            m = form.save(commit=False)
            m.emisor = request.user
            m.save()
            messages.success(request, "Mensaje enviado.")
            return redirect('messenger:inbox')
    else:
        form = MessageForm(user=request.user)
    return render(request, 'messenger/compose.html', {'form': form})


@login_required
def conversation(request, user_id):
    other = get_object_or_404(User, pk=user_id, is_active=True)

    if request.method == 'POST':
        form = ReplyForm(request.POST)
        if form.is_valid():
            m = form.save(commit=False)
            m.emisor = request.user
            m.receptor = other
            m.save()
            return redirect('messenger:conversation', user_id=other.pk)
    else:
        form = ReplyForm()

    hilo = Message.objects.filter(
        Q(emisor=request.user, receptor=other) |
        Q(emisor=other, receptor=request.user)
    ).order_by('fecha_envio')

    return render(request, 'messenger/conversation.html', {
        'other': other,
        'hilo': hilo,
        'form': form,
    })

