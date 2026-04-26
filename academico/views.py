from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import datetime, timedelta
import base64
from .models import (
    AnioAcademico,
    Asignatura,
    Grupo,
    Local,
    FranjaHoraria,
    Profesor,
    AsignacionProfesor,
    AsignacionAulaGrupo,
    Auditoria,
    TipoAccionAuditoria,
)
from .forms import (
    AnioAcademicoForm,
    GrupoForm,
    AsignaturaForm,
    LocalForm,
    FranjaHorariaForm,
    ProfesorForm,
    AsignacionProfesorForm,
    AsignacionAulaGrupoForm,
)
from planificacion.permissions import vicedecano_required, planificador_required


@planificador_required
def anno_list(request):
    annos = AnioAcademico.objects.all()
    return render(request, 'academico/anno_list.html', {'annos': annos})


@planificador_required
def anno_create(request):
    if request.method == 'POST':
        form = AnioAcademicoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('academico:anno_list')
    else:
        form = AnioAcademicoForm()
    return render(request, 'academico/anno_form.html', {'form': form, 'action': 'Crear'})


@planificador_required
def anno_update(request, pk):
    anno = get_object_or_404(AnioAcademico, pk=pk)
    if request.method == 'POST':
        form = AnioAcademicoForm(request.POST, instance=anno)
        if form.is_valid():
            form.save()
            return redirect('academico:anno_list')
    else:
        form = AnioAcademicoForm(instance=anno)
    return render(request, 'academico/anno_form.html', {'form': form, 'action': 'Editar'})


@planificador_required
def grupo_list(request):
    grupos = Grupo.objects.select_related('anio').all()
    return render(request, 'academico/grupo_list.html', {'grupos': grupos})


@planificador_required
def grupo_create(request):
    if request.method == 'POST':
        form = GrupoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('academico:grupo_list')
    else:
        form = GrupoForm()
    return render(request, 'academico/grupo_form.html', {'form': form, 'action': 'Crear'})


@planificador_required
def grupo_update(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    if request.method == 'POST':
        form = GrupoForm(request.POST, instance=grupo)
        if form.is_valid():
            form.save()
            return redirect('academico:grupo_list')
    else:
        form = GrupoForm(instance=grupo)
    return render(request, 'academico/grupo_form.html', {'form': form, 'action': 'Editar'})


@planificador_required
def local_list(request):
    locales = Local.objects.all()
    return render(request, 'academico/local_list.html', {'locales': locales})


@planificador_required
def local_create(request):
    if request.method == 'POST':
        form = LocalForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('academico:local_list')
    else:
        form = LocalForm()
    return render(request, 'academico/local_form.html', {'form': form, 'action': 'Crear'})


@planificador_required
def local_update(request, pk):
    local = get_object_or_404(Local, pk=pk)
    if request.method == 'POST':
        form = LocalForm(request.POST, instance=local)
        if form.is_valid():
            form.save()
            return redirect('academico:local_list')
    else:
        form = LocalForm(instance=local)
    return render(request, 'academico/local_form.html', {'form': form, 'action': 'Editar'})


@planificador_required
def franjahoraria_list(request):
    franjas = FranjaHoraria.objects.all()
    return render(request, 'academico/franjahoraria_list.html', {'franjas': franjas})


@planificador_required
def franjahoraria_create(request):
    if request.method == 'POST':
        form = FranjaHorariaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('academico:franjahoraria_list')
    else:
        form = FranjaHorariaForm()
    return render(request, 'academico/franjahoraria_form.html', {'form': form, 'action': 'Crear'})


@planificador_required
def franjahoraria_update(request, pk):
    franja = get_object_or_404(FranjaHoraria, pk=pk)
    if request.method == 'POST':
        form = FranjaHorariaForm(request.POST, instance=franja)
        if form.is_valid():
            form.save()
            return redirect('academico:franjahoraria_list')
    else:
        form = FranjaHorariaForm(instance=franja)
    return render(request, 'academico/franjahoraria_form.html', {'form': form, 'action': 'Editar'})


@planificador_required
def asignatura_list(request):
    asignaturas = Asignatura.objects.select_related('anio').all()
    return render(request, 'academico/asignatura_list.html', {'asignaturas': asignaturas})


@planificador_required
def asignatura_create(request):
    if request.method == 'POST':
        form = AsignaturaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('academico:asignatura_list')
    else:
        form = AsignaturaForm()
    return render(request, 'academico/asignatura_form.html', {'form': form, 'action': 'Crear'})


@planificador_required
def asignatura_update(request, pk):
    asignatura = get_object_or_404(Asignatura, pk=pk)
    if request.method == 'POST':
        form = AsignaturaForm(request.POST, instance=asignatura)
        if form.is_valid():
            form.save()
            return redirect('academico:asignatura_list')
    else:
        form = AsignaturaForm(instance=asignatura)
    return render(request, 'academico/asignatura_form.html', {'form': form, 'action': 'Editar'})


@planificador_required
def asignacionprofesor_delete(request, pk):
    asignacion = get_object_or_404(AsignacionProfesor, pk=pk)
    if request.method == 'POST':
        asignacion.delete()
        return redirect('academico:asignatura_list')
    return render(request, 'academico/asignacionprofesor_confirm_delete.html', {'asignacion': asignacion})


# ─────────────────────────────────────────────────────────────
# PANEL DE AUDITORÍA (Solo Vicedecano)
# ─────────────────────────────────────────────────────────────

@vicedecano_required
def panel_auditoria(request):
    """
    Vista del panel de auditoría para el Vicedecano.
    Muestra registros de auditoría con filtros y paginación.
    """
    # Obtener parámetros de filtro
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    accion_filtro = request.GET.get('accion')
    usuario_filtro = request.GET.get('usuario')
    
    # Construir queryset base
    queryset = Auditoria.objects.all()
    
    # Aplicar filtros
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, '%Y-%m-%d')
            queryset = queryset.filter(fecha__gte=fecha_desde_dt)
        except ValueError:
            pass
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            # Incluir todo el día
            fecha_hasta_dt = fecha_hasta_dt + timedelta(days=1)
            queryset = queryset.filter(fecha__lt=fecha_hasta_dt)
        except ValueError:
            pass
    
    if accion_filtro:
        queryset = queryset.filter(accion=accion_filtro)
    
    if usuario_filtro:
        queryset = queryset.filter(usuario__username__icontains=usuario_filtro)
    
    # Ordenar por fecha descendente
    queryset = queryset.order_by('-fecha')
    
    # Paginación
    paginator = Paginator(queryset, 50)  # 50 registros por página
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Obtener datos para gráfico (conteo de acciones por día en los últimos 7 días)
    fecha_grafico = timezone.now() - timedelta(days=7)
    datos_grafico = (
        Auditoria.objects
        .filter(fecha__gte=fecha_grafico)
        .annotate(fecha_dia=TruncDate('fecha'))
        .values('fecha_dia')
        .annotate(count=Count('id'))
        .order_by('fecha_dia')
    )

    fechas_grafico = []
    conteos_grafico = []
    for d in datos_grafico:
        fechas_grafico.append(d['fecha_dia'].strftime('%Y-%m-%d'))
        conteos_grafico.append(d['count'])

    # Generar gráfico SVG inline (sin dependencias de terceros)
    grafico_svg = _generar_grafico_svg(fechas_grafico, conteos_grafico)
    grafico_base64 = base64.b64encode(grafico_svg.encode('utf-8')).decode('utf-8')

    context = {
        'page_obj': page_obj,
        'acciones': TipoAccionAuditoria.choices,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'accion_filtro': accion_filtro,
        'usuario_filtro': usuario_filtro,
        'grafico_base64': grafico_base64,
    }
    
    return render(request, 'academico/panel_auditoria.html', context)


# ─────────────────────────────────────────────────────────────
# CRUD PROFESOR
# ─────────────────────────────────────────────────────────────

@planificador_required
def profesor_list(request):
    profesores = Profesor.objects.all()
    return render(request, 'academico/profesor_list.html', {'profesores': profesores})


@planificador_required
def profesor_create(request):
    if request.method == 'POST':
        form = ProfesorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('academico:profesor_list')
    else:
        form = ProfesorForm()
    return render(request, 'academico/profesor_form.html', {'form': form, 'action': 'Crear'})


@planificador_required
def profesor_update(request, pk):
    profesor = get_object_or_404(Profesor, pk=pk)
    if request.method == 'POST':
        form = ProfesorForm(request.POST, instance=profesor)
        if form.is_valid():
            form.save()
            return redirect('academico:profesor_list')
    else:
        form = ProfesorForm(instance=profesor)
    return render(request, 'academico/profesor_form.html', {'form': form, 'action': 'Editar'})


@planificador_required
def profesor_delete(request, pk):
    profesor = get_object_or_404(Profesor, pk=pk)
    if request.method == 'POST':
        profesor.delete()
        return redirect('academico:profesor_list')
    return render(request, 'academico/profesor_confirm_delete.html', {'profesor': profesor})


# ─────────────────────────────────────────────────────────────
# CRUD ASIGNACION PROFESOR (completo)
# ─────────────────────────────────────────────────────────────

@planificador_required
def asignacionprofesor_list(request):
    asignaciones = AsignacionProfesor.objects.select_related('profesor', 'asignatura', 'grupo').all()
    return render(request, 'academico/asignacionprofesor_list.html', {'asignaciones': asignaciones})


@planificador_required
def asignacionprofesor_create(request):
    if request.method == 'POST':
        form = AsignacionProfesorForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('academico:asignacionprofesor_list')
    else:
        form = AsignacionProfesorForm()
    return render(request, 'academico/asignacionprofesor_form.html', {'form': form, 'action': 'Crear'})


@planificador_required
def asignacionprofesor_update(request, pk):
    asignacion = get_object_or_404(AsignacionProfesor, pk=pk)
    if request.method == 'POST':
        form = AsignacionProfesorForm(request.POST, instance=asignacion)
        if form.is_valid():
            form.save()
            return redirect('academico:asignacionprofesor_list')
    else:
        form = AsignacionProfesorForm(instance=asignacion)
    return render(request, 'academico/asignacionprofesor_form.html', {'form': form, 'action': 'Editar'})


# ─────────────────────────────────────────────────────────────
# CRUD ASIGNACION AULA A GRUPO
# ─────────────────────────────────────────────────────────────

@planificador_required
def asignacionaulagrupo_list(request):
    asignaciones = AsignacionAulaGrupo.objects.select_related('grupo', 'grupo__anio', 'local').all()
    return render(request, 'academico/asignacionaulagrupo_list.html', {'asignaciones': asignaciones})


@planificador_required
def asignacionaulagrupo_create(request):
    if request.method == 'POST':
        form = AsignacionAulaGrupoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('academico:asignacionaulagrupo_list')
    else:
        form = AsignacionAulaGrupoForm()
    return render(request, 'academico/asignacionaulagrupo_form.html', {'form': form, 'action': 'Crear'})


@planificador_required
def asignacionaulagrupo_update(request, pk):
    asignacion = get_object_or_404(AsignacionAulaGrupo, pk=pk)
    if request.method == 'POST':
        form = AsignacionAulaGrupoForm(request.POST, instance=asignacion)
        if form.is_valid():
            form.save()
            return redirect('academico:asignacionaulagrupo_list')
    else:
        form = AsignacionAulaGrupoForm(instance=asignacion)
    return render(request, 'academico/asignacionaulagrupo_form.html', {'form': form, 'action': 'Editar'})


@planificador_required
def asignacionaulagrupo_delete(request, pk):
    asignacion = get_object_or_404(AsignacionAulaGrupo, pk=pk)
    if request.method == 'POST':
        asignacion.delete()
        return redirect('academico:asignacionaulagrupo_list')
    return render(request, 'academico/asignacionaulagrupo_confirm_delete.html', {'asignacion': asignacion})


# ─────────────────────────────────────────────────────────────
# DELETE VIEWS PARA ENTIDADES EXISTENTES
# ─────────────────────────────────────────────────────────────

@planificador_required
def anno_delete(request, pk):
    anno = get_object_or_404(AnioAcademico, pk=pk)
    if request.method == 'POST':
        try:
            anno.delete()
            return redirect('academico:anno_list')
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'No se puede eliminar el año porque tiene registros asociados: {e}')
            return redirect('academico:anno_list')
    return render(request, 'academico/anno_confirm_delete.html', {'anno': anno})


@planificador_required
def grupo_delete(request, pk):
    grupo = get_object_or_404(Grupo, pk=pk)
    if request.method == 'POST':
        try:
            grupo.delete()
            return redirect('academico:grupo_list')
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'No se puede eliminar el grupo porque tiene registros asociados: {e}')
            return redirect('academico:grupo_list')
    return render(request, 'academico/grupo_confirm_delete.html', {'grupo': grupo})


@planificador_required
def local_delete(request, pk):
    local = get_object_or_404(Local, pk=pk)
    if request.method == 'POST':
        try:
            local.delete()
            return redirect('academico:local_list')
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'No se puede eliminar el local porque tiene registros asociados: {e}')
            return redirect('academico:local_list')
    return render(request, 'academico/local_confirm_delete.html', {'local': local})


@planificador_required
def franjahoraria_delete(request, pk):
    franja = get_object_or_404(FranjaHoraria, pk=pk)
    if request.method == 'POST':
        try:
            franja.delete()
            return redirect('academico:franjahoraria_list')
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'No se puede eliminar la franja porque tiene registros asociados: {e}')
            return redirect('academico:franjahoraria_list')
    return render(request, 'academico/franjahoraria_confirm_delete.html', {'franja': franja})


@planificador_required
def asignatura_delete(request, pk):
    asignatura = get_object_or_404(Asignatura, pk=pk)
    if request.method == 'POST':
        try:
            asignatura.delete()
            return redirect('academico:asignatura_list')
        except Exception as e:
            from django.contrib import messages
            messages.error(request, f'No se puede eliminar la asignatura porque tiene registros asociados: {e}')
            return redirect('academico:asignatura_list')
    return render(request, 'academico/asignatura_confirm_delete.html', {'asignatura': asignatura})


def _generar_grafico_svg(fechas, conteos):
    """
    Genera un gráfico de líneas SVG inline sin dependencias de terceros.
    Devuelve el string XML del SVG.
    """
    if not fechas:
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 200" '
            'width="100%" height="200">'
            '<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" '
            'font-size="16" fill="#666">No hay datos para mostrar</text></svg>'
        )

    # Dimensiones
    w, h = 800, 200
    pad_left, pad_right = 60, 30
    pad_top, pad_bottom = 30, 50
    gw = w - pad_left - pad_right
    gh = h - pad_top - pad_bottom

    max_c = max(conteos) if max(conteos) > 0 else 1
    n = len(fechas)
    step_x = gw / (n - 1) if n > 1 else gw

    # Coordenadas de puntos
    points = []
    for i, c in enumerate(conteos):
        x = pad_left + i * step_x
        y = pad_top + gh - (c / max_c) * gh
        points.append((x, y, c))

    # Construir path de la línea
    path_d = f"M {points[0][0]} {points[0][1]}"
    for x, y, _ in points[1:]:
        path_d += f" L {x} {y}"

    # Área bajo la curva (polígono cerrado)
    area_d = path_d + f" L {points[-1][0]} {pad_top + gh} L {points[0][0]} {pad_top + gh} Z"

    # Líneas de cuadrícula Y
    grid_lines = []
    for i in range(5):
        val = max_c * (i / 4)
        y = pad_top + gh - (i / 4) * gh
        grid_lines.append(
            f'<line x1="{pad_left}" y1="{y}" x2="{w - pad_right}" y2="{y}" '
            f'stroke="#e0e0e0" stroke-width="1"/>'
        )
        grid_lines.append(
            f'<text x="{pad_left - 10}" y="{y + 4}" text-anchor="end" '
            f'font-size="11" fill="#888">{int(val)}</text>'
        )

    # Líneas de cuadrícula X y etiquetas
    x_lines = []
    x_labels = []
    for i, f in enumerate(fechas):
        x = pad_left + i * step_x
        x_lines.append(
            f'<line x1="{x}" y1="{pad_top}" x2="{x}" y2="{pad_top + gh}" '
            f'stroke="#f0f0f0" stroke-width="1"/>'
        )
        # Rotar etiquetas si hay muchas
        rotate = ' transform="rotate(-45 ' + str(x) + ' ' + str(pad_top + gh + 15) + ')"' if n > 5 else ''
        x_labels.append(
            f'<text x="{x}" y="{pad_top + gh + 20}" text-anchor="middle" '
            f'font-size="10" fill="#666"{rotate}>{f[5:]}</text>'
        )

    # Puntos y tooltips (títulos SVG nativos)
    dots = []
    for x, y, c in points:
        dots.append(
            f'<circle cx="{x}" cy="{y}" r="4" fill="#0d6efd" stroke="white" stroke-width="2">'
            f'<title>{c} acciones</title></circle>'
        )

    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="{h}" style="font-family: sans-serif;">',
        f'<rect x="{pad_left}" y="{pad_top}" width="{gw}" height="{gh}" fill="#fafafa" stroke="#eee"/>',
        ''.join(grid_lines),
        ''.join(x_lines),
        f'<path d="{area_d}" fill="rgba(13,110,253,0.1)" stroke="none"/>',
        f'<path d="{path_d}" fill="none" stroke="#0d6efd" stroke-width="2" stroke-linejoin="round"/>',
        ''.join(dots),
        ''.join(x_labels),
        f'<text x="{w/2}" y="{h - 5}" text-anchor="middle" font-size="12" fill="#444">Últimos 7 días</text>',
        '</svg>',
    ]
    return ''.join(svg_parts)
