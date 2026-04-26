# 📋 PLAN: Celdas Editables en Horario

## 🎯 Objetivo
Permitir editar las asignaciones directamente desde la tabla del horario mediante:
- Click en celda para abrir modal de edición
- Cambiar local, franja horaria, o profesor
- Guardar cambios vía AJAX sin recargar página

---

## 📊 Análisis del Código Actual

### 1. Vista `ver_horario` en `horario/views.py`
- **Línea 25-170**: Muestra el horario en formato tabla HTML
- **Contexto enviado**: `horario`, `franjas_por_dia`, `grupos`, `anio`, `semana`
- **Template**: `horario/horario.html`

### 2. Template `horario/horario.html`
- Renderiza tabla con celdas por día/franja/grupo
- Cada celda muestra: asignatura, tipo, local, profesor
- **No tiene JavaScript** para interactividad

### 3. URLs en `horario/urls.py`
- Existen endpoints para horario, PDF, y APIs
- **Falta endpoint** para actualizar asignación

---

## 🛠️ Implementación Paso a Paso

### PASO 1: Crear Endpoint AJAX para Edición

**Archivo:** `horario/urls.py`
```python
path('api/asignacion/<int:pk>/editar/', views.api_editar_asignacion, name='api_editar_asignacion'),
```

**Archivo:** `horario/views.py`
```python
@require_http_methods(["POST"])
@login_required
def api_editar_asignacion(request, pk):
    """
    API para editar una asignación existente.
    Recibe: local_id, franja_id, profesor_id (opcionales)
    Retorna: JSON con éxito/error
    """
    asignacion = get_object_or_404(Asignacion, pk=pk)
    
    try:
        data = json.loads(request.body)
        
        # Actualizar campos si se proporcionan
        if 'local_id' in data:
            asignacion.local_id = data['local_id']
        if 'franja_id' in data:
            asignacion.franja_id = data['franja_id']
        if 'profesor_id' in data:
            asignacion.profesor_id = data['profesor_id']
        
        asignacion.manual = True  # Marcar como editada manualmente
        asignacion.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Asignación actualizada correctamente',
            'asignacion_id': asignacion.pk
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
```

---

### PASO 2: Crear Endpoint para Obtener Opciones

**Archivo:** `horario/views.py`
```python
@login_required
def api_opciones_edision(request):
    """
    Retorna listas de locales, franjas y profesores disponibles.
    """
    locales = list(Local.objects.values('id', 'codigo', 'nombre'))
    franjas = list(FranjaHoraria.objects.values('id', 'hora_inicio', 'hora_fin', 'orden'))
    profesores = list(Profesor.objects.values('id', 'nombre'))
    
    return JsonResponse({
        'locales': locales,
        'franjas': franjas,
        'profesores': profesores
    })
```

**URL:** `path('api/opciones-edicion/', views.api_opciones_edicion, name='api_opciones_edicion')`

---

### PASO 3: Modificar Template - Agregar HTML para Modal

**Archivo:** `templates/horario/horario.html`

Agregar al final del template (antes de `{% endblock %}`):
```html
<!-- Modal de Edición de Celda -->
<div class="modal fade" id="editarCeldaModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Editar Asignación</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <form id="formEditarCelda">
                    <input type="hidden" id="asignacion_id">
                    
                    <div class="mb-3">
                        <label class="form-label">Asignatura</label>
                        <input type="text" class="form-control" id="asignatura_nombre" readonly>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Grupo</label>
                        <input type="text" class="form-control" id="grupo_nombre" readonly>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Local</label>
                        <select class="form-select" id="local_select">
                            <!-- Opciones cargadas vía JS -->
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Franja Horaria</label>
                        <select class="form-select" id="franja_select">
                            <!-- Opciones cargadas vía JS -->
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Profesor</label>
                        <select class="form-select" id="profesor_select">
                            <!-- Opciones cargadas vía JS -->
                        </select>
                    </div>
                </form>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="button" class="btn btn-primary" id="btnGuardarCambios">Guardar Cambios</button>
            </div>
        </div>
    </div>
</div>
```

---

### PASO 4: Agregar JavaScript para Interactividad

**Archivo:** `templates/horario/horario.html`

Agregar en `{% block scripts %}` o al final:
```html
<script>
// Variables globales con datos del servidor
const opciones = {
    locales: [],
    franjas: [],
    profesores: []
};

// 1. Cargar opciones al iniciar
document.addEventListener('DOMContentLoaded', function() {
    cargarOpcionesEdicion();
    
    // Configurar clicks en celdas editables
    document.querySelectorAll('.celda-horario').forEach(celda => {
        celda.addEventListener('click', function() {
            const asignacionId = this.dataset.asignacionId;
            if (asignacionId) {
                abrirModalEdicion(asignacionId, this.dataset);
            }
        });
    });
    
    // Botón guardar
    document.getElementById('btnGuardarCambios').addEventListener('click', guardarCambios);
});

// 2. Cargar opciones vía AJAX
async function cargarOpcionesEdicion() {
    try {
        const response = await fetch('/horario/api/opciones-edicion/');
        const data = await response.json();
        opciones.locales = data.locales;
        opciones.franjas = data.franjas;
        opciones.profesores = data.profesores;
        
        // Poblar selects del modal
        poblarSelect('local_select', opciones.locales, 'codigo');
        poblarSelect('franja_select', opciones.franjas, 'hora_inicio', f => `${f.hora_inicio}-${f.hora_fin}`);
        poblarSelect('profesor_select', opciones.profesores, 'nombre');
    } catch (error) {
        console.error('Error cargando opciones:', error);
    }
}

// 3. Poblar selects
function poblarSelect(selectId, items, textField, formatFn = null) {
    const select = document.getElementById(selectId);
    select.innerHTML = '<option value="">-- Seleccionar --</option>';
    items.forEach(item => {
        const text = formatFn ? formatFn(item) : item[textField];
        select.innerHTML += `<option value="${item.id}">${text}</option>`;
    });
}

// 4. Abrir modal con datos de la celda
function abrirModalEdicion(asignacionId, dataset) {
    document.getElementById('asignacion_id').value = asignacionId;
    document.getElementById('asignatura_nombre').value = dataset.asignatura || '';
    document.getElementById('grupo_nombre').value = dataset.grupo || '';
    
    // Seleccionar valores actuales
    document.getElementById('local_select').value = dataset.localId || '';
    document.getElementById('franja_select').value = dataset.franjaId || '';
    document.getElementById('profesor_select').value = dataset.profesorId || '';
    
    const modal = new bootstrap.Modal(document.getElementById('editarCeldaModal'));
    modal.show();
}

// 5. Guardar cambios vía AJAX
async function guardarCambios() {
    const asignacionId = document.getElementById('asignacion_id').value;
    
    const data = {
        local_id: document.getElementById('local_select').value || null,
        franja_id: document.getElementById('franja_select').value || null,
        profesor_id: document.getElementById('profesor_select').value || null
    };
    
    try {
        const response = await fetch(`/horario/api/asignacion/${asignacionId}/editar/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Cerrar modal y recargar página
            bootstrap.Modal.getInstance(document.getElementById('editarCeldaModal')).hide();
            location.reload(); // Recargar para ver cambios
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Error de conexión: ' + error);
    }
}

// Helper: obtener cookie CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
</script>
```

---

### PASO 5: Modificar Celda HTML para Incluir Data Attributes

**Archivo:** `templates/horario/horario.html`

Modificar el renderizado de celdas:
```html
<td class="celda-horario {% if asignacion %}tiene-asignacion{% else %}vacia{% endif %}">
    {% if asignacion %}
    <div class="contenido-celda"
         data-asignacion-id="{{ asignacion.id }}"
         data-asignatura="{{ asignacion.actividad_plan.asignatura.nombre }}"
         data-grupo="{{ asignacion.actividad_plan.grupo.nombre|default:'Conferencia' }}"
         data-local-id="{{ asignacion.local.id }}"
         data-franja-id="{{ asignacion.franja.id }}"
         data-profesor-id="{{ asignacion.profesor.id|default:'' }}">
        
        <strong>{{ asignacion.actividad_plan.asignatura.abreviatura }}</strong><br>
        <small>{{ asignacion.local.codigo }}</small><br>
        <small class="text-muted">{{ asignacion.profesor.nombre|default:'Sin profesor' }}</small>
    </div>
    {% else %}
    <div class="celda-vacia">-</div>
    {% endif %}
</td>
```

---

### PASO 6: Agregar CSS para Indicar Editable

```css
.celda-horario {
    cursor: pointer;
    transition: background-color 0.2s;
}

.celda-horario:hover {
    background-color: #e3f2fd; /* Azul claro al pasar mouse */
    box-shadow: inset 0 0 0 2px #2196f3;
}

.celda-horario.tiene-asignacion:hover::after {
    content: "✏️ Editar";
    position: absolute;
    top: 2px;
    right: 2px;
    font-size: 10px;
    background: #2196f3;
    color: white;
    padding: 2px 4px;
    border-radius: 3px;
}
```

---

## 📋 Resumen de Cambios

| Archivo | Cambios | Líneas Aprox |
|---------|---------|--------------|
| `horario/urls.py` | Agregar 2 endpoints | +2 líneas |
| `horario/views.py` | Crear 2 vistas API | +80 líneas |
| `templates/horario/horario.html` | Modal + JS + data attributes | +150 líneas |
| `static/horario/css/horario.css` | Estilos para celdas editables | +30 líneas |

---

## ✅ Verificación

1. Generar horario
2. Ir a `/horario/?anio_id=7&semana=1`
3. **Click en celda** → Abre modal
4. **Cambiar local/franja/profesor**
5. **Guardar** → Se actualiza sin recargar (o recarga automática)

---

## ⚠️ Consideraciones de Seguridad

- Solo usuarios con rol `planificador` o `vicedecano` pueden editar
- Validar que el local tenga capacidad suficiente
- Validar que el profesor no tenga conflicto de horario
- Registrar auditoría de cambios manuales

---

## 🚀 Próximos Pasos (Futuro)

- Drag & drop para mover asignaciones entre celdas
- Validación en tiempo real de conflictos
- Undo/Redo de cambios
- Edición inline sin modal (directo en celda)
