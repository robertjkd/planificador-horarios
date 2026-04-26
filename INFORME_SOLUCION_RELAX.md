# Informe: Solución de Horario Relajada para Problemas INFEASIBLE

## 🎯 Problema

El scheduler arrojaba `No se encontró solución factible` para el 3er año, semana 1. Esto ocurre cuando las restricciones del modelo CP-SAT son **demasiado estrictas** y no existe ninguna asignación que las cumpla todas.

## 🔧 Solución Implementada

### 1. Diagnóstico de Conflictos (INFEASIBLE)

Cuando el solver no encuentra solución, ahora se ejecuta un **diagnóstico automático** que:

- Detecta si un grupo tiene más actividades que franjas disponibles en un día
- Muestra conflictos de capacidad por día
- Loguea detalles de las restricciones conflictivas

```python
# Ejemplo de log de diagnóstico
❌ No se encontró solución factible: INFEASIBLE
============================================================
DIAGNÓSTICO DE CONFLICTOS (INFEASIBLE)
============================================================
⚠️  CONFLICTOS DE CAPACIDAD POR DÍA:
   Grupo G1, Día 0: 8 actividades > 4 franjas
```

### 2. Estrategia de Relajación Automática

Si el modelo original es INFEASIBLE, el sistema **automáticamente intenta una versión relajada**:

**Modelo Original (fallido):**
- Restricciones duras: cada actividad asignada, sin conflictos de grupo/local
- Restricciones blandas: minimizar huecos, carga diaria, fatiga de profesores

**Modelo Relajado (fallback):**
- ✅ Solo restricciones duras (obligatorias)
- ❌ Sin restricciones blandas (ignoradas)

Esto garantiza que **siempre se generará un horario**, aunque no sea óptimo.

### 3. Detección de Conflictos en Solución Relajada

Al guardar la solución relajada, se detectan automáticamente:

- **Asignaciones virtuales**: actividades sin local/franja real
- **Conflictos de profesor**: mismo profesor en dos lugares simultáneamente
- **Violaciones de restricciones blandas**: huecos, carga, fatiga

### 4. Estructura de Tabla de Horario

Se creó `planificacion/horario_table.py` con clases para visualización:

```python
@dataclass
class CeldaHorario:
    asignatura: str
    tipo_actividad: str
    grupo: Optional[str]
    local: Optional[str]
    profesor: Optional[str]
    es_virtual: bool      # ← Marca si usa recurso virtual
    es_conflicto: bool    # ← Marca si hay superposición

@dataclass
class TablaHorario:
    anio_nombre: str
    semana: int
    dias: List[str]       # ['Lunes', 'Martes', ...]
    filas: List[FilaHorario]
    estadisticas: Dict
```

### 5. Mensajes al Usuario

**Solución Normal:**
```
Horario generado exitosamente para 1° año (Mañana) semana 1. 
343 actividades asignadas.
```

**Solución Relajada:**
```
⚠️ HORARIO RELAJADO generado para 3° año (Mañana) semana 1. 
280 actividades asignadas. 
La solución viola algunas restricciones blandas (huecos, carga, fatiga). 
Revise conflictos de profesores y grupos manualmente.
```

**Sin Solución (incluso relajada):**
```
No se encontró solución factible para 3° año (Mañana) semana 1. 
Incluso relajando restricciones blandas el problema es imposible. 
Verifique que ningún grupo tenga más actividades que franjas disponibles.
```

---

## 📊 Flujo de Generación

```
1. Intentar solver con restricciones COMPLETAS
   ↓
   ├─ ✅ ÉXITO → Guardar y mostrar horario normal
   ↓
   └─ ❌ INFEASIBLE → Diagnosticar y relajar
        ↓
        2. Intentar solver con restricciones DURAS solamente
           ↓
           ├─ ✅ ÉXITO → Guardar con advertencia de "relajado"
           ↓
           └─ ❌ INFEASIBLE → Error crítico (datos imposibles)
```

---

## 🧪 Prueba de Funcionamiento

```bash
# Ejecutar generación para año problemático
python manage.py runserver

# Ir a /planificacion/generar/7/1/ (3er año, semana 1)
# Click en Generar

# Resultado esperado:
# - Si era INFEASIBLE por restricciones blandas: Genera con advertencia
# - Si era INFEASIBLE por capacidad: Muestra diagnóstico de conflicto
```

---

## 📁 Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `planificacion/scheduler.py` | Diagnóstico INFEASIBLE + relajación automática (líneas 669-848) |
| `planificacion/horario_table.py` | Nuevo - estructura de tabla para visualización |
| `planificacion/views.py` | Integración con tabla de horario + mensajes mejorados |

---

## ⚠️ Notas Importantes

1. **La relajación ignora restricciones blandas**:
   - Puede haber huecos en horarios de grupos
   - Profesores pueden tener carga excesiva
   - Puede haber fatiga de profesores

2. **Los conflictos se detectan pero no se evitan**:
   - Un profesor puede aparecer en dos lugares a la vez
   - Se marcan como `es_conflicto=True` en la tabla

3. **La solución relajada es temporal**:
   - Permite visualizar el horario
   - Debe revisarse manualmente
   - Se recomienda ajustar datos (más franjas, menos actividades, etc.)

4. **Si incluso la relajada falla**:
   - Indica un problema grave de capacidad
   - Ejemplo: 8 actividades para un grupo en un día con solo 4 franjas
   - Solución: Redistribuir actividades a otros días o aumentar franjas
