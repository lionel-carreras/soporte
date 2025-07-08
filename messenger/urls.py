from django.urls import path
from . import views

# urls de la app messenger que lleva mensajes entre usuarios
app_name = 'messenger'

urlpatterns = [
    path('', views.inbox,   name='inbox'),
    path('sent/', views.sent,  name='sent'),
    path('view/<int:pk>/', views.detail,  name='detail'),
    path('new/',  views.compose, name='compose'),
    path('conv/<int:user_id>/', views.conversation, name='conversation'),
]

