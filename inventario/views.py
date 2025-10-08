from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError
from .models import Impresora
from soporte.models import Sucursal
from django.db import models
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from django.utils.text import slugify
from io import BytesIO
import qrcode

def _bool(v):  # checkbox helper
    return bool(v) and v not in ("0", "false", "False")


# detail pública (sin login)
def impresora_public_detail(request, pk):
    imp = get_object_or_404(Impresora.objects.select_related("sucursal"), pk=pk)
    return render(request, "soporte/inventario/impresora_detail.html", {"imp": imp})


# QR PNG para la URL pública


def impresora_qr(request, pk):
    public_url = request.build_absolute_uri(
        reverse("inventario:impresora_public_detail", args=[pk])
    )
    img = qrcode.make(public_url)
    buf = BytesIO(); img.save(buf, format="PNG"); buf.seek(0)

    # nombre prolijo
    try:
        from .models import Impresora
        imp = Impresora.objects.only("marca", "modelo").get(pk=pk)
        base = f"qr_{slugify(imp.marca)}_{slugify(imp.modelo)}_{pk}"
    except Exception:
        base = f"qr_impresora_{pk}"

    resp = HttpResponse(buf.read(), content_type="image/png")
    resp["Cache-Control"] = "max-age=300"
    if request.GET.get("download"):
        resp["Content-Disposition"] = f'attachment; filename="{base}.png"'
    return resp


@login_required
def impresora_list(request):
    q          = (request.GET.get("q") or "").strip()
    suc_id     = request.GET.get("sucursal") or ""
    activa     = request.GET.get("activa")   or ""
    conexion   = request.GET.get("conexion") or ""
    propiedad  = request.GET.get("propiedad") or ""

    qs = (Impresora.objects
            .select_related("sucursal")
            .all()
            .order_by("sucursal__nombre", "marca", "modelo"))

    if q:
        qs = qs.filter(
            models.Q(marca__icontains=q) |
            models.Q(modelo__icontains=q) |
            models.Q(nro_serie__icontains=q) |
            models.Q(ip__icontains=q)
        )

    if suc_id:  # <-- aplicar filtro por sucursal si viene
        qs = qs.filter(sucursal_id=suc_id)

    if activa in ("0", "1"):
        qs = qs.filter(activa=(activa == "1"))
    if conexion in ("IP", "USB"):
        qs = qs.filter(conexion=conexion)
    if propiedad in ("PROPIA", "ALQUILER"):
        qs = qs.filter(propiedad=propiedad)

    page_obj = Paginator(qs, 20).get_page(request.GET.get("page"))

    return render(request, "soporte/inventario/impresora_list.html", {
        "page_obj": page_obj,
        "sucursales": Sucursal.objects.order_by("nombre"),
        "f": {  # preservar selección en el template
            "q": q, "sucursal": suc_id, "activa": activa,
            "conexion": conexion, "propiedad": propiedad
        },
        "choices": {
            "conexion": Impresora.CONEXION_CHOICES,
            "propiedad": Impresora.PROPIEDAD_CHOICES,
        }
    })


@login_required
def impresora_create(request):
    sucursales = Sucursal.objects.order_by("nombre")
    if request.method == "POST":
        data = request.POST
        marca       = (data.get("marca") or "").strip()
        modelo      = (data.get("modelo") or "").strip()
        nro_serie   = (data.get("nro_serie") or "").strip()
        sucursal_id = data.get("sucursal") or ""          # <-- lee del POST
        conexion    = data.get("conexion") or ""
        ip          = data.get("ip") or ""
        propiedad   = data.get("propiedad") or ""
        activa      = bool(data.get("activa"))
        ubicacion   = (data.get("ubicacion") or "").strip()
        notas       = (data.get("notas") or "").strip()

        # validación mínima
        if not (marca and modelo and nro_serie and sucursal_id and conexion and propiedad):
            messages.error(request, "Completá todos los campos obligatorios.")
            return render(request, "soporte/inventario/impresora_create.html", {"sucursales": sucursales})

        try:
            imp = Impresora(
                marca=marca, modelo=modelo, nro_serie=nro_serie,
                sucursal_id=sucursal_id,                    # <-- usar *_id
                conexion=conexion, ip=ip, propiedad=propiedad,
                activa=activa, ubicacion=ubicacion, notas=notas,
            )
            imp.save()
        except Exception as e:
            messages.error(request, f"Error: {getattr(e, 'message_dict', e)}")
            return render(request, "soporte/inventario/impresora_create.html", {"sucursales": sucursales})

        messages.success(request, "Impresora creada correctamente.")
        return redirect("inventario:impresora_list")

    return render(request, "soporte/inventario/impresora_create.html", {"sucursales": sucursales})

@login_required
@permission_required("inventario.change_impresora", raise_exception=True)
def impresora_edit(request, pk):
    imp = get_object_or_404(Impresora, pk=pk)
    sucursales = Sucursal.objects.order_by("nombre")

    if request.method == "POST":
        data = request.POST
        imp.marca     = (data.get("marca") or "").strip()
        imp.modelo    = (data.get("modelo") or "").strip()
        imp.nro_serie = (data.get("nro_serie") or "").strip()
        imp.sucursal_id = data.get("sucursal") or None
        imp.conexion  = data.get("conexion") or ""
        ip            = (data.get("ip") or "").strip()
        imp.ip        = ip or None
        imp.propiedad = data.get("propiedad") or ""
        imp.activa    = _bool(data.get("activa"))
        imp.ubicacion = (data.get("ubicacion") or "").strip()
        imp.notas     = (data.get("notas") or "").strip()

        try:
            imp.full_clean()
            imp.save()
        except IntegrityError:
            messages.error(request, "Ya existe una impresora con ese N° de serie.")
            return render(request, "soporte/inventario/impresora_edit.html", {"sucursales": sucursales, "imp": imp, "mode": "edit"})
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return render(request, "soporte/inventario/impresora_edit.html", {"sucursales": sucursales, "imp": imp, "mode": "edit"})

        messages.success(request, "Impresora actualizada.")
        return redirect("inventario:impresora_list")

    return render(request, "soporte/inventario/impresora_edit.html", {"sucursales": sucursales, "imp": imp, "mode": "edit"})

@login_required
@permission_required("inventario.delete_impresora", raise_exception=True)
def impresora_delete(request, pk):
    imp = get_object_or_404(Impresora, pk=pk)
    if request.method == "POST":
        imp.delete()
        messages.success(request, "Impresora eliminada.")
        return redirect("inventario:impresora_list")
    return render(request, "soporte/inventario/impresora_confirm_delete.html", {"imp": imp})


def impresora_detail(request, pk):
    imp = get_object_or_404(Impresora, pk=pk)
    return render(request, "soporte/inventario/impresora_detail.html", {"imp": imp})
