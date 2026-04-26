# Informe: Corrección de Importaciones - Visualización de Horario

## 🐛 Error Reportado

```
ModuleNotFoundError at /planificacion/generar/7/1/
No module named 'planificacion.models'
Exception Location: planificacion\views.py, line 1017, in generar_horario_view
```

## 🔍 Análisis

Los modelos no están en `planificacion/models.py`, sino en **`academico/models.py`**:

| Modelo | Ubicación Real |
|--------|---------------|
| `Asignacion` | `academico.models` |
| `ActividadPlan` | `academico.models` |
| `FranjaHoraria` | `academico.models` |
| `AnioAcademico` | `academico.models` |
| `Asignatura` | `academico.models` |
| `Grupo` | `academico.models` |

## 🔧 Correcciones Realizadas

### 1. `planificacion/views.py`

**Problema:** Import local erróneo + import duplicado
```python
# ANTES (línea 1017):
from .models import Asignacion

# DESPUÉS: Eliminado - ahora está en import de línea 27
```

**Problema:** Import parcial en la vista
```python
# ANTES (línea 1014):
from academico.models import AnioAcademico, FranjaHoraria

# DESPUÉS: Eliminado - ahora está en import global
```

**Solución:** Consolidar todos los imports al inicio del archivo
```python
# Línea 27-35 - Import global corregido:
from academico.models import (
    ActividadPlan,
    AnioAcademico,
    Asignacion,        # ← AGREGADO
    Asignatura,
    FranjaHoraria,     # ← AGREGADO
    Grupo,
    TipoActividad,
)
```

### 2. `planificacion/horario_table.py`

**Problema:** Import local erróneo
```python
# ANTES (línea 93):
from .models import Asignacion

# DESPUÉS (línea 93):
from academico.models import Asignacion
```

### 3. `planificacion/scheduler.py`

**Estado:** ✅ Ya estaba correcto
```python
from academico.models import (
    ActividadPlan,
    AnioAcademico,
    Asignacion,
    ...
)
```

---

## ✅ Verificación

```bash
python manage.py check
# Resultado: System check identified no issues (0 silenced)
```

---

## 🧪 Prueba de Integración End-to-End

### Paso 1: Iniciar servidor
```bash
python manage.py runserver
```

### Paso 2: Acceder a generación de horario
```
http://127.0.0.1:8000/planificacion/generar/7/1/
```

### Paso 3: Esperado
- ✅ El scheduler se ejecuta sin error de importación
- ✅ Se genera el horario (normal o relajado)
- ✅ Se construye la tabla de visualización
- ✅ Se muestra el horario con:
  - Celdas normales (blanco)
  - Celdas virtuales (amarillo - sin local/franja)
  - Celdas con conflicto (rojo - profesor superpuesto)

---

## 📊 Estructura de Datos del Horario

### Flujo de Generación → Visualización

```
1. generar_horario_view()
   └── ejecuta scheduler.generar_horario(anio_id, semana)
       └── Guarda Asignacion en BD
   
2. Construye tabla de visualización
   └── asignaciones = Asignacion.objects.filter(...)
   └── tabla_horario = construir_tabla_horario(asignaciones, franjas)
   └── tabla_horario = detectar_conflictos_profesor(tabla_horario)
   
3. Renderiza template
   └── template recibe: tabla_horario, dias_semana, resultado
```

### Datos Pasados al Template

```python
return render(request, 'planificacion/generar_resultado.html', {
    'anio': anio,
    'semana': semana,
    'resultado': resultado,
    'tabla_horario': tabla_horario,  # ← Nueva estructura
    'dias_semana': [(0, 'Lunes'), ...],
})
```

### Estructura de `tabla_horario`

```
TablaHorario
├── anio_nombre: "3° año (Mañana)"
├── semana: 1
├── dias: ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
├── filas: [FilaHorario, FilaHorario, ...]
│   ├── franja_nombre: "Franja 1"
│   ├── hora_inicio: "08:00"
│   ├── hora_fin: "09:30"
│   └── celdas: {0: [CeldaHorario], 1: [...], ...}
│       └── CeldaHorario
│           ├── asignatura: "Álgebra"
│           ├── tipo_actividad: "C"
│           ├── grupo: "G1"
│           ├── local: "A101"
│           ├── es_virtual: False
│           └── es_conflicto: False
└── estadisticas: {...}
```

---

## 📋 Resumen de Cambios

| Archivo | Línea | Cambio |
|---------|-------|--------|
| `views.py` | 27-35 | Agregar `Asignacion` y `FranjaHoraria` al import global |
| `views.py` | 1016-1018 | Eliminar imports locales duplicados/erróneos |
| `horario_table.py` | 93 | Corregir `from .models` → `from academico.models` |

---

## 🎯 Resultado Esperado

**Antes:**
```
❌ ModuleNotFoundError: No module named 'planificacion.models'
```

**Después:**
```
✅ Horario generado exitosamente para 3° año (Mañana) semana 1. 
   280 actividades asignadas.
   
   [Tabla de horario mostrada con franjas horarias en filas 
    y días de la semana en columnas]
```

---

## 📝 Notas para Template

El template `generar_resultado.html` debe recibir y usar:

```html
{% if tabla_horario %}
  <table class="table table-bordered">
    <thead>
      <tr>
        <th>Franja</th>
        {% for dia_num, dia_nombre in dias_semana %}
          <th>{{ dia_nombre }}</th>
        {% endfor %}
      </tr>
    </thead>
    <tbody>
      {% for fila in tabla_horario.filas %}
        <tr>
          <td>{{ fila.franja_nombre }}<br>
              <small>{{ fila.hora_inicio }} - {{ fila.hora_fin }}</small>
          </td>
          {% for dia_num, dia_nombre in dias_semana %}
            <td>
              {% for celda in fila.celdas|get_item:dia_num %}
                <div class="{% if celda.es_virtual %}bg-warning{% endif %}
                            {% if celda.es_conflicto %}bg-danger{% endif %}">
                  {{ celda.asignatura }} ({{ celda.tipo_actividad }})
                  <br><small>{{ celda.local }}</small>
                </div>
              {% endfor %}
            </td>
          {% endfor %}
        </tr>
      {% endfor %}
    </tbody>
  </table>
{% endif %}
```
