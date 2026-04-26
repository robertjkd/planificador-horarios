# Informe de Corrección: Importación → Generación de Horario

## 📋 Resumen Ejecutivo

Se han implementado mejoras completas al flujo de importación de balance y generación de horarios para hacerlo robusto, informativo y tolerante a errores.

---

## 🔍 Causas Identificadas y Soluciones

### 1. Código "EC" no reconocido
**Problema:** El balance de carga contenía el código "EC" (Especial de Conferencia) que no estaba mapeado.

**Solución:**
- Agregado `EC` a `TIPOS_CONFERENCIA` en `views.py`
- Agregado mapeo `EC → CE` en `MAPEO_CODIGOS_ALTERNATIVOS`
- Agregado `EC` a `TIPO_LOCAL_POR_ACTIVIDAD` en `scheduler.py`

### 2. Mensajes de error poco informativos
**Problema:** Los errores no indicaban la asignatura afectada ni los tipos válidos disponibles.

**Solución:**
- Mensajes ahora incluyen: `Fila X, Asignatura "Y": error... Tipos válidos: A, B, C`
- Logs de warning con contexto completo

### 3. Falta de visibilidad en el proceso
**Problema:** No se sabía qué actividades se estaban procesando ni cuántas se encontraron.

**Solución:**
- Logs detallados en cada paso del proceso
- Resumen final con desglose por tipo de actividad
- Pre-flight checks en el scheduler mostrando primeras 5 actividades

---

## 📝 Cambios Implementados

### 1. `planificacion/views.py`

#### Nuevos imports
```python
import tempfile
import uuid
```

#### Nuevas constantes de mapeo (líneas 48-79)
```python
# Tipos de actividad que se crean una sola vez (sin grupo)
TIPOS_CONFERENCIA = {'C', 'CE', 'EC'}  # EC = Especial de Conferencia

# Mapeo de códigos alternativos/normalizados a códigos oficiales
MAPEO_CODIGOS_ALTERNATIVOS = {
    'EC': 'CE',      # Especial de Conferencia → Conferencia Especial
    'CONF': 'C',     # Conferencia abreviada
    'CLASE': 'CP',   # Clase → Clase Práctica
    'LAB': 'L',      # Laboratorio abreviado
    # ... etc
}


def _normalizar_codigo_actividad(codigo: str) -> str:
    """Normaliza códigos alternativos a oficiales."""
    if not codigo:
        return ''
    codigo = codigo.strip().upper()
    return MAPEO_CODIGOS_ALTERNATIVOS.get(codigo, codigo)
```

#### Mejoras en `importar_balance()`
- Normalización automática de códigos: `tipo = _normalizar_codigo_actividad(tipo_raw)`
- Mensajes de error con contexto de asignatura
- Logs de warning para códigos no reconocidos
- Resumen final detallado con desglose por tipo

#### Mejoras en `importar_balance_view()`
- Guarda archivo temporalmente para reprocesamiento en confirmación
- Ejecuta `importar_balance()` real al confirmar (antes solo mostraba mensaje)
- Registra auditoría del importe real
- Limpia archivo temporal después de procesar

#### Mejoras en `importar_balance_preview()`
- Usa misma normalización de códigos que la importación real
- Mensajes de error mejorados con tipos válidos

### 2. `planificacion/scheduler.py`

#### Nuevos mapeos (línea 44)
```python
TIPO_LOCAL_POR_ACTIVIDAD = {
    # ... mapeos existentes ...
    'EC': ['S'],      # Especial de Conferencia → Salón
}
```

#### Pre-flight checks mejorados (líneas 131-150)
```python
# Pre-flight: mostrar primeras N actividades para debugging
if actividades:
    logger.info('Primeras 5 actividades a planificar:')
    for i, act in enumerate(actividades[:5], 1):
        grupo_str = f'G{act.grupo.nombre}' if act.grupo else 'Conf.'
        logger.info('  %s. %s | %s | %s | Sem%s | Dia%s',
            i, act.asignatura.nombre, act.tipo_actividad,
            grupo_str, act.semana, act.dia_semana
        )

# Verificar actividades con tipos no mapeados
actividades_sin_tipo_local = [a for a in actividades 
                              if a.tipo_actividad not in TIPO_LOCAL_POR_ACTIVIDAD]
```

#### Logs de debugging detallados (líneas 91-125)
- Cantidad de actividades sin filtrar
- Cantidad con `requiere_local=True/False`
- Query parameters recibidos

---

## 🧪 Pruebas Recomendadas

### 1. Verificar normalización de códigos
```bash
python manage.py shell
```
```python
from planificacion.views import _normalizar_codigo_actividad

# Pruebas
assert _normalizar_codigo_actividad('EC') == 'CE'
assert _normalizar_codigo_actividad('ec') == 'CE'
assert _normalizar_codigo_actividad('CONF') == 'C'
assert _normalizar_codigo_actividad('LAB') == 'L'
assert _normalizar_codigo_actividad('C') == 'C'  # Sin cambio
print("✅ Normalización correcta")
```

### 2. Probar importación con códigos alternativos
1. Crear archivo Excel de prueba con códigos:
   - `EC` (debe normalizarse a `CE`)
   - `CONF` (debe normalizarse a `C`)
   - `LAB` (debe normalizarse a `L`)
2. Subir a Importar Balance
3. Verificar que se procesan sin errores

### 3. Verificar flujo completo
```bash
# 1. Seed data
python manage.py seed_data

# 2. Iniciar servidor
python manage.py runserver
```

1. Ir a `/planificacion/importar-balance/`
2. Seleccionar 1er año
3. Subir balance con código "EC"
4. Confirmar importación
5. Ver mensaje: "¡Importación exitosa! Actividades creadas: X..."
6. Ir a `/planificacion/generar/`
7. Seleccionar 1er año, semana 1
8. Click "Generar horario"
9. Verificar que el scheduler encuentra actividades:
   ```
   Query de actividades: asignatura__anio=1, semana=1, requiere_local=True
   Actividades con requiere_local=True: 25
   Primeras 5 actividades a planificar:
     1. Álgebra | CE | Conf. | Sem1 | Dia0
     ...
   ```

---

## 📊 Ejemplo de Salida Esperada

### Importación exitosa
```
=== RESUMEN IMPORTACIÓN ===
Año: 1° año (Mañana)
Asignaturas procesadas: 7
Actividades creadas: 363
Actividades omitidas (duplicadas): 0
Filas vacías: 12
Errores: 0
Desglose por tipo:
  C (Conferencia): 28 actividades
  CE (Conferencia Especial): 14 actividades
  CP (Clase Práctica): 245 actividades
  L (Laboratorio): 56 actividades
  NP (No Presencial): 20 actividades
===========================
```

### Importación con errores
```
=== RESUMEN IMPORTACIÓN ===
Año: 1° año (Mañana)
Asignaturas procesadas: 7
Actividades creadas: 362
Errores: 1
Desglose por tipo:
  ...
Errores encontrados:
  - Fila 156, Asignatura "Filosofía": tipo "XYZ" (normalizado: "XYZ") no reconocido. Tipos válidos: C, CE, CP, E, L, NP, PP, S, T, TE
===========================
```

### Scheduler encontrando actividades
```
Iniciando planificación: anio_id=1, semana=1
Año académico: 1° año (Mañana) (turno=M)
Grupos encontrados: 5
Franjas horarias para turno M: 20
Query de actividades: asignatura__anio=1, semana=1, requiere_local=True
Actividades sin filtrar requiere_local: 363
Actividades con requiere_local=True: 343
Actividades con requiere_local=False: 20
Actividades cargadas: 343
Locales disponibles: 14
Primeras 5 actividades a planificar:
  1. Álgebra | CE | Conf. | Sem1 | Dia0
  2. Álgebra | CP | G1 | Sem1 | Dia0
  3. Álgebra | CP | G2 | Sem1 | Dia0
  4. Álgebra | CP | G3 | Sem1 | Dia0
  5. Álgebra | CP | G4 | Sem1 | Dia0
  ... y 338 actividades más
```

---

## 🎯 Beneficios de los Cambios

1. **Tolerancia a errores**: La importación continúa a pesar de errores individuales
2. **Códigos alternativos**: Se normalizan automáticamente variantes comunes
3. **Visibilidad total**: Logs en cada paso del proceso
4. **Mensajes claros**: Errores indican asignatura, fila y solución sugerida
5. **Pre-flight checks**: El scheduler verifica actividades antes de optimizar
6. **No duplicación**: Idempotencia garantizada con verificación de duplicados

---

## 🔧 Archivos Modificados

| Archivo | Líneas Modificadas |
|---------|-------------------|
| `planificacion/views.py` | 15-17 (imports), 48-79 (mapeos), 419-705 (normalización), 774-800 (logs) |
| `planificacion/scheduler.py` | 44 (EC mapping), 91-125 (logs), 131-150 (pre-flight) |

---

## ⚠️ Notas Importantes

1. **EC ahora se mapea a CE**: Si el código "EC" debe mantenerse como tipo distinto (no como alias de CE), modificar el mapeo en `MAPEO_CODIGOS_ALTERNATIVOS`.

2. **Archivos temporales**: La importación ahora guarda archivos temporalmente en el directorio temporal del sistema. Se limpian automáticamente después de procesar.

3. **Logs de DEBUG**: Para ver todos los logs de debugging, configurar en `settings.py`:
   ```python
   LOGGING = {
       # ...
       'loggers': {
           'planificacion': {
               'level': 'DEBUG',
               'handlers': ['console'],
           },
       },
   }
   ```
