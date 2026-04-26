# Recursos Virtuales (Overflow) - Sistema de Fallback

## 📋 Descripción

El sistema de **recursos virtuales** garantiza que el generador de horarios pueda producir un resultado funcional incluso cuando los datos iniciales (locales y franjas) no cubren todas las actividades planificadas.

Cuando una actividad no puede asignarse a ningún local real (por capacidad insuficiente, tipo incompatible, o falta de franjas), el sistema crea automáticamente:

1. **Local Virtual**: Un local "fantasma" con capacidad ilimitada (9999) que puede albergar cualquier actividad
2. **Franjas Virtuales**: Franjas horarias temporales para días que no tienen franjas reales

Las asignaciones virtuales se detectan y marcan para revisión manual posterior.

---

## 🎯 ¿Cuándo se Activan?

El sistema se activa automáticamente cuando:
- Una actividad no tiene ningún local compatible (tipo incorrecto o capacidad insuficiente)
- Una actividad requiere un día para el cual no existen franjas horarias
- Hay más actividades que recursos reales disponibles

**Ejemplo de log cuando se activan recursos virtuales:**
```
⚠️  40 actividades sin opciones reales. Creando recursos virtuales...
Creado local virtual: LOCAL VIRTUAL (OVERFLOW) (capacidad=9999)
  Actividad 123 (Álgebra) → Local virtual + Franja -10
✅ Creadas 40 combinaciones virtuales
```

---

## 🔧 Implementación Técnica

### Clases de Recursos Virtuales

```python
class LocalVirtual:
    """Local "fantasma" para albergar actividades sin opciones reales."""
    pk = -1  # ID negativo para identificación
    codigo = 'VIRTUAL-OVERFLOW'
    nombre = 'LOCAL VIRTUAL (OVERFLOW)'
    tipo = 'S'  # Salón (compatible con la mayoría de actividades)
    capacidad = 9999
    es_virtual = True

class FranjaVirtual:
    """Franja horaria "fantasma" para días sin franjas reales."""
    pk = -(dia * 10 + orden)  # IDs negativos únicos
    turno = 'M'  # o 'T' según el año
    orden = 1-4
    hora_inicio = 08:00
    hora_fin = 20:00
    dia_semana = 0-4
    es_virtual = True
```

### Función Principal

```python
def crear_recursos_virtuales(anio, franjas_existentes, locales_existentes, actividades):
    """
    Crea recursos virtuales para garantizar que todas las actividades 
    tengan al menos una opción de asignación.
    """
```

### Flujo de Trabajo

1. **Detección**: El scheduler detecta actividades sin combinaciones válidas
2. **Creación**: Se crean automáticamente el local virtual y franjas virtuales necesarias
3. **Ampliación**: Se añaden estos recursos a las listas de locales y franjas disponibles
4. **Asignación**: El solver CP-SAT asigna las actividades conflictivas a los recursos virtuales
5. **Marcado**: Las asignaciones virtuales se detectan y se marcan en el resultado
6. **Advertencia**: El usuario recibe una advertencia clara sobre las asignaciones virtuales

---

## ⚠️ Comportamiento en Base de Datos

### ¿Qué se guarda?

Las asignaciones virtuales **no se guardan completamente** en la base de datos:

- `actividad_plan`: ✅ Se guarda (referencia a la actividad real)
- `profesor`: ✅ Se guarda si existe
- `local`: ❌ Se guarda como `NULL` (no existe en BD)
- `franja`: ❌ Se guarda como `NULL` (no existe en BD)

Esto significa que en el horario visual, las actividades virtuales aparecerán **sin local ni franja asignados**, lo cual es una señal clara de que requieren revisión manual.

### ¿Por qué no guardar los recursos virtuales?

- Los locales y franjas virtuales no existen físicamente
- Guardarlos requeriría crear registros "falsos" en la base de datos
- Al guardar como NULL, el sistema puede detectar fácilmente qué actividades necesitan atención

---

## 📊 Mensajes al Usuario

### Éxito con Recursos Virtuales

```
Horario generado exitosamente para 1° año (Mañana) semana 1. 
343 actividades asignadas. 
⚠️ 40 actividades quedaron en LOCALES VIRTUALES y requieren revisión manual.
```

### En la Interfaz Web

Las actividades sin local/franja asignados se muestran:
- Con fondo rojo o amarillo en la tabla horaria
- Con leyenda "⚠️ PENDIENTE: Asignar local y franja real"
- En una sección separada "Actividades por Revisar"

---

## 🔍 Identificación de Actividades Virtuales

Para encontrar actividades que usaron recursos virtuales:

```python
# En Python/Django
from planificacion.models import Asignacion

# Actividades sin local (usaron local virtual)
pendientes = Asignacion.objects.filter(local__isnull=True)

# Actividades sin franja (usaron franja virtual)
pendientes = Asignacion.objects.filter(franja__isnull=True)

# Ambas
pendientes = Asignacion.objects.filter(local__isnull=True, franja__isnull=True)
```

```sql
-- En SQL
SELECT a.*, ap.semana, asig.nombre as asignatura
FROM planificacion_asignacion a
JOIN planificacion_actividadplan ap ON a.actividad_plan_id = ap.id
JOIN academico_asignatura asig ON ap.asignatura_id = asig.id
WHERE a.local_id IS NULL OR a.franja_id IS NULL;
```

---

## 🛠️ Corrección Manual de Actividades Virtuales

### Opción 1: Crear Recursos Reales

1. **Si es problema de capacidad**: Crear locales más grandes o aumentar capacidad de existentes
2. **Si es problema de tipo**: Crear locales del tipo faltante (Laboratorios, Salones, etc.)
3. **Si es problema de franjas**: Crear franjas horarias para los días faltantes

### Opción 2: Modificar Actividades

1. Cambiar el tipo de actividad a uno compatible con locales existentes
2. Ajustar el día de la semana a uno con franjas disponibles
3. Dividir actividades grandes en sesiones más pequeñas

### Opción 3: Aceptar Temporalmente

Las actividades virtuales funcionan como marcadores de posición:
- El horario se genera completamente
- Las actividades virtuales se pueden asignar manualmente después
- No bloquean el proceso de planificación

---

## 📈 Estadísticas

El resultado de la planificación incluye estadísticas sobre recursos virtuales:

```python
{
    'tiempo_segundos': 1.5,
    'valor_objetivo': 245.0,
    'actividades_asignadas': 343,
    'combinaciones_exploradas': 16464,
    'asignaciones_virtuales': 40,      # ← Número de actividades virtuales
    'requiere_revision': True,          # ← True si hay virtuales
}
```

---

## 🧪 Prueba de Funcionamiento

1. Ejecutar seed de datos (que provoca error de capacidad):
   ```bash
   python manage.py seed_data
   ```

2. Importar balance de carga con muchas actividades

3. Generar horario:
   - Ir a `/planificacion/generar/`
   - Seleccionar año y semana
   - Click en "Generar"

4. Verificar resultado:
   - Mensaje de éxito con advertencia de virtuales
   - Logs muestran creación de recursos virtuales
   - Horario generado con algunas asignaciones NULL

5. Revisar actividades pendientes:
   ```python
   Asignacion.objects.filter(local__isnull=True)
   ```

---

## ⚙️ Configuración Avanzada

Para ajustar el comportamiento de recursos virtuales, editar en `scheduler.py`:

```python
# Capacidad del local virtual (default: 9999)
LocalVirtual.capacidad = 9999

# Horario de franjas virtuales (default: 08:00-20:00)
FranjaVirtual.hora_inicio = time(8, 0)
FranjaVirtual.hora_fin = time(20, 0)

# Tipo de local virtual (default: 'S' - Salón)
# 'S' = Salón (compatible con C, CE, CP, S, T, TE, PP)
# 'O' = Otro (compatible con E - Educación Física)
LocalVirtual.tipo = 'S'
```

---

## 📝 Notas de Desarrollo

- Los recursos virtuales se crean **en memoria**, no en BD
- Los IDs negativos (`pk < 0`) identifican recursos virtuales
- Las asignaciones virtuales no se guardan completamente (local/franja = NULL)
- El sistema prioriza recursos reales; virtuales son último recurso
- Las actividades con opciones reales nunca usan recursos virtuales
