from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView



app_name = 'soporte'

urlpatterns = [
    #dashboard usuario
    path('dashboard/usuarios/', views.dashboard_usuario, name='dashboard_usuario'),
    #crear ticket usuario
    path('dashboard/crear_ticket/', views.ticket_create, name='ticket_create'),
    ########
    
    path('ticket/<int:ticket_id>/aceptar/',views.ticket_accept,name='ticket_accept'),
    
    #detalle ticket usuario
    path('ticket/<int:ticket_id>/', views.detalle_ticket, name='detalle_ticket'),
    # anular ticket usuario
    path('ticket/<int:ticket_id>/anular/',views.anular_ticket_usuario,name='ticket_anular_usuario'),
    #reabrir ticket usuario
    path('ticket/<int:ticket_id>/reabrir_user/', views.ticket_reopen_user, name='ticket_reopen_user'),
    
    ######
    
    #detalle ticket agente
    path('ticket_agente/<int:ticket_id>/', views.detail_ticket, name='detail_ticket'),
    #asignar ticket agente
    path('ticket/<int:ticket_id>/asignar/', views.ticket_assign, name='ticket_assign'),
    #resolver ticket agente
    path('ticket/<int:ticket_id>/resolver/', views.ticket_resolve, name='ticket_resolve'),
    #anular ticket agente
    path('agente/<int:ticket_id>/anular/',views.anular_ticket_agente,name='ticket_anular_agente'),
    #reabrir ticket agente
    path('ticket/<int:ticket_id>/reabrir_agente/', views.ticket_reopen, name='ticket_reopen'),
    #dashboard agente
    path('dashboard/agentes/', views.dashboard_agente, name='dashboard_agente'),
    #historico agente
    path('dashboard/agente/historico', views.ticket_historico, name='ticket_historico'),
    ########
    
    #logout
    path('logout/', LogoutView.as_view(next_page='users:login'), name='logout'),

    path('webpubsub/auth/', views.webpubsub_auth, name='webpubsub_auth'),

    #estadisticas superadmin
    path('dashboard/superadmin', views.superadmin_dashboard, name='dashboard_superadmin'),
    #crear ticket admin
    path('dashboard/admin/create_ticket/', views.create_ticket, name='create_ticket'),

]
