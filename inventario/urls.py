from django.urls import path
from . import views


app_name = "inventario"

urlpatterns = [
    path("impresoras/", views.impresora_list, name="impresora_list"),
    path("impresoras/nueva/", views.impresora_create, name="impresora_create"),
    path("impresoras/<int:pk>/", views.impresora_detail, name="impresora_detail"),
    path("impresoras/<int:pk>/editar/", views.impresora_edit, name="impresora_edit"),
    path("impresoras/<int:pk>/eliminar/", views.impresora_delete, name="impresora_delete"),

    # públicas:
    path("impresoras/<int:pk>/detail/", views.impresora_public_detail, name="impresora_public_detail"),
    path("impresoras/<int:pk>/qr.png", views.impresora_qr, name="impresora_qr"),
]




