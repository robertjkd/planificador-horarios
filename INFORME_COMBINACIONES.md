# Informe: Corrección de "No hay combinaciones válidas"

## 🔍 Diagnóstico del Problema

El error "No hay combinaciones válidas de actividad-local-franja" ocurre cuando ninguna actividad puede asignarse a ningún local en ninguna franja horaria. Las causas más comunes son:

1. **Capacidad insuficiente** de locales para conferencias (requieren suma de todos los alumnos del año)
2. **Capacidad insuficiente** del polideportivo para Educación Física
3. **Tipo de local incorrecto** en el mapeo (ej: actividad busca Laboratorio pero no hay ninguno)
4. **Sin franjas horarias** para el día requerido por la actividad

---

## 🛠️ Cambios Implementados

### 1. Diagnóstico Detallado en Scheduler (`planificacion/scheduler.py`)

Se agregó un sistema completo de diagnóstico que muestra:
- Locales disponibles por tipo con sus capacidades
- Alumnos totales del año (para conferencias)
- Para cada actividad sin opciones: por qué fue rechazada (tipo, capacidad, ed. física)

**Ejemplo de salida en logs:**
```
============================================================
DIAGNÓSTICO: Actividades sin combinaciones válidas
============================================================
Actividad ID 123: Álgebra | Tipo: C | Conf. | Sem1 Dia0
  Capacidad requerida: 150
  Tipos de local permitidos: ['S']
  Locales evaluados: 14
  Rechazados por tipo: 12
  Rechazados por capacidad: 2  ← ¡PROBLEMA! Los salones tienen capacidad < 150
  Rechazados Ed. Física: 0
  Franjas disponibles día 0: 4
============================================================
```

### 2. Capacidades Aumentadas en Seed (`academico/management/commands/seed_data.py`)

**Antes:**
- Salones: 2 con capacidad 150 (insuficiente para 150 alumnos, sin margen)
- Polideportivo: 1 con capacidad 100 (insuficiente para 1er/2do año con 150 alumnos)
- Aulas: 8 con capacidad 35

**Ahora:**
- Salones: 3 con capacidad 200 (margen para 150 alumnos + profesores)
- Polideportivos: 2 con capacidad 200 cada uno (POLI1 y POLI2)
- Aulas: 8 con capacidad 40
- Laboratorios: 3 con capacidad 40

### 3. Lógica de Educación Física Mejorada

**Antes:** Educación física (tipo 'E') requería obligatoriamente un local con 'POLI' en el código.

**Ahora:** 
- Si existe al menos un polideportivo (código contiene 'POLI'), usa solo esos
- Si no hay polideportivo específico, acepta cualquier local de tipo 'O' (Otro)

Esto permite flexibilidad si el usuario no tiene polideportivos nombrados específicamente.

### 4. Logs de Capacidades Iniciales

Al inicio de la generación, ahora se muestra:
```
Locales disponibles: 16
  Tipo A: 8 locales, capacidades: [40, 40, 40, 40, 40, 40, 40, 40]
  Tipo L: 3 locales, capacidades: [40, 40, 40]
  Tipo O: 2 locales, capacidades: [200, 200]
  Tipo S: 3 locales, capacidades: [200, 200, 200]
Alumnos totales en el año: 150 (para conferencias)
Grupos y alumnos: G1=30, G2=30, G3=30, G4=30, G5=30
```

---

## 🧪 Instrucciones para Actualizar Datos

### Opción A: Recrear todos los datos (recomendado para desarrollo)

```bash
# Eliminar base de datos y recrear
rm db.sqlite3  # o eliminar PostgreSQL database
python manage.py migrate
python manage.py seed_data --clear
```

Esto creará los locales con las **nuevas capacidades**.

### Opción B: Actualizar locales existentes (para producción)

Si no puedes recrear la base de datos, actualiza las capacidades manualmente:

```python
# Ejecutar en shell de Django (python manage.py shell)
from academico.models import Local

# Aumentar capacidad de salones
for local in Local.objects.filter(tipo='S'):
    local.capacidad = 200
    local.save()
    print(f"Actualizado {local.codigo}: capacidad = {local.capacidad}")

# Crear polideportivos adicionales si no existen
Local.objects.get_or_create(
    codigo='POLI1',
    defaults={'nombre': 'Polideportivo 1', 'tipo': 'O', 'capacidad': 200}
)
Local.objects.get_or_create(
    codigo='POLI2',
    defaults={'nombre': 'Polideportivo 2', 'tipo': 'O', 'capacidad': 200}
)

# Actualizar aulas
for local in Local.objects.filter(tipo='A'):
    local.capacidad = 40
    local.save()
```

---

## 📋 Verificación

Después de actualizar los datos, ejecutar:

```bash
python manage.py runserver
```

1. Ir a `/planificacion/generar/`
2. Seleccionar un año y semana
3. Click en "Generar horario"
4. Revisar los logs de la consola

**Resultado esperado:**
```
Iniciando planificación: anio_id=1, semana=1
Año académico: 1° año (Mañana) (turno=M)
Grupos encontrados: 5
Franjas horarias para turno M: 4
Actividades cargadas: 343
Locales disponibles: 16
  Tipo A: 8 locales, capacidades: [40, 40, 40, 40, 40, 40, 40, 40]
  Tipo L: 3 locales, capacidades: [40, 40, 40]
  Tipo O: 2 locales, capacidades: [200, 200]
  Tipo S: 3 locales, capacidades: [200, 200, 200]
Alumnos totales en el año: 150
Grupos y alumnos: G1=30, G2=30, G3=30, G4=30, G5=30
Combinaciones permitidas: 16464  ← ¡ÉXITO! Hay combinaciones válidas
...
✅ Horario generado exitosamente
```

---

## 🔧 Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `planificacion/scheduler.py` | Diagnóstico detallado (líneas 119-130, 198-201, 203-284) |
| `academico/management/commands/seed_data.py` | Capacidades aumentadas (líneas 193-202) |

---

## ⚠️ Notas Importantes

1. **Si aún hay errores**: Los logs ahora mostrarán exactamente qué actividad falla y por qué (tipo, capacidad, etc.)

2. **Capacidad mínima recomendada**:
   - Conferencias: 200 (para años con 5 grupos × 30 = 150 alumnos)
   - Aulas: 40 (para grupos de 30 + margen)
   - Laboratorios: 40 (para grupos de 30)
   - Polideportivos: 200 (para Ed. Física de años grandes)

3. **Mapeo de tipos de actividad a locales**:
   - `C`, `CE`, `EC` → `S` (Salón)
   - `L` → `L` (Laboratorio)
   - `CP`, `S`, `T`, `TE`, `PP` → `A` o `S` (Aula o Salón)
   - `E` → `O` (Otro/Polideportivo)
