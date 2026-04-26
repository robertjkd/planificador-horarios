# Cambios Realizados - Funcionalidades del Vicedecano

**Fecha:** 25 de abril de 2026

---

## 1. Flujo de Importación de Balance con Confirmación (2 Pasos)

### Antes:
- El Vicedecano subía el archivo y la importación se ejecutaba inmediatamente
- No había opción para revisar antes de guardar
- No había opción para cancelar

### Después:
- **Paso 1:** El Vicedecano selecciona el año y sube el archivo → Muestra **Vista Previa**
- **Paso 2:** Revisa el resumen con:
  - Asignaturas a procesar
  - Actividades a crear
  - Actividades omitidas (duplicadas)
  - Errores detectados
  - Desglose por tipo de actividad
  - Advertencias (ej: asignaturas que se crearán)
- **Botones:**
  - ✅ **Confirmar y Guardar** - Ejecuta la importación real
  - ❌ **Cancelar** - Vuelve al formulario sin importar

### Archivos Modificados:
- `planificacion/views.py` - Vista `importar_balance_view` con flujo de 2 pasos
- `templates/planificacion/importar_balance.html` - Template con vista previa y botones
- `planificacion/views.py` - Nueva función `importar_balance_preview()` (sin guardar en BD)

### Características:
- Los datos se almacenan temporalmente en la sesión del usuario
- El archivo no se guarda permanentemente hasta confirmar
- Se pueden detectar errores antes de afectar la base de datos
- Posibilidad de cancelar sin consecuencias

---

## 2. Eliminación de "Generar Horario" del Vicedecano

### Antes:
- El Vicedecano veía el botón "Generar Horario" en:
  - Home (`templates/home.html`)
  - Navbar (`templates/base.html`)

### Después:
- El Vicedecano **NO** ve la opción "Generar Horario"
- Solo el rol **Planificador** puede generar horarios
- El Vicedecano mantiene acceso a:
  - Importar Balance de Carga
  - Gestionar Usuarios
  - Panel de Auditoría

### Archivos Modificados:
- `templates/home.html` - Línea 20: Cambiado `{% if user.es_planificador or user.es_vicedecano %}` a `{% if user.es_planificador %}`
- `templates/base.html` - Línea 42: Cambiado `{% if user.es_planificador or user.es_vicedecano %}` a `{% if user.es_planificador %}`

---

## 3. Permisos por Rol Actualizados

| Funcionalidad | Vicedecano | Planificador | Consulta |
|--------------|------------|--------------|----------|
| Importar Balance | ✅ | ❌ | ❌ |
| Generar Horario | ❌ | ✅ | ❌ |
| Gestionar Usuarios | ✅ | ❌ | ❌ |
| Ver Horarios | ✅ | ✅ | ✅ (limitado) |
| Panel Auditoría | ✅ | ❌ | ❌ |

---

## Flujo de Importación de Balance (Detallado)

```
┌─────────────────────────────────────────────────────────────┐
│  1. VICEDECANO ACCEDE A IMPORTAR BALANCE                   │
│     /planificacion/importar-balance/                       │
│     → Muestra formulario con:                               │
│       - Selección de Año Académico                         │
│       - Archivo (CSV o Excel)                              │
│       - Opciones avanzadas (checkboxes)                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. COMPLETA FORMULARIO Y PRESIONA "VISTA PREVIA"           │
│     → Sube archivo                                          │
│     → Procesa sin guardar en BD                            │
│     → Genera estadísticas                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. VISTA PREVIA SE MUESTRA                                │
│     → Card amarillo con título "Vista Previa"              │
│     → Resumen de:                                          │
│       - Asignaturas a procesar                             │
│       - Actividades a crear                                │
│       - Duplicados (omitidos)                              │
│       - Errores encontrados                                │
│       - Desglose por tipo                                  │
│     → Botones:                                             │
│       [Cancelar]    [Confirmar y Guardar]                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
         ┌──────────────────┴──────────────────┐
         ↓                                     ↓
┌─────────────────┐               ┌─────────────────────────────┐
│ 4A. CANCELAR    │               │ 4B. CONFIRMAR               │
│ → Limpia sesión │               │ → Ejecuta importación real  │
│ → Muestra mensaje│              │ → Guarda en base de datos   │
│   "Cancelado"   │               │ → Registra auditoría        │
│ → Vuelve a     │               │ → Muestra resumen final     │
│   formulario    │               │   "Importación completada"  │
└─────────────────┘               └─────────────────────────────┘
```

---

## Cómo Probar los Cambios

### 1. Probar Flujo de Importación:
1. Iniciar sesión como **Vicedecano**
2. Ir a "Importar Balance"
3. Seleccionar un año académico
4. Subir archivo CSV o Excel
5. Verificar que aparece la **Vista Previa** con estadísticas
6. Probar botón **Cancelar** → Debe volver al formulario
7. Subir archivo nuevamente
8. Probar botón **Confirmar y Guardar** → Debe mostrar mensaje de éxito

### 2. Probar que Vicedecano NO ve "Generar Horario":
1. Iniciar sesión como **Vicedecano**
2. Verificar que en el Home NO aparece el card "Planificador" con botón "Generar Horario"
3. Verificar que en el Navbar NO aparece el enlace "Generar Horario"
4. Cerrar sesión
5. Iniciar sesión como **Planificador**
6. Verificar que SÍ aparece el botón "Generar Horario" en Home y Navbar

### 3. Verificar Seguridad de URLs:
- Intentar acceder a `/planificacion/generar/` como Vicedecano → Debe redirigir (403)
- Intentar acceder como Planificador → Debe funcionar

---

## Notas Técnicas

### Almacenamiento Temporal:
- Los datos de la vista previa se guardan en `request.session['importacion_preview']`
- Incluye: anio_id, nombre_archivo, opciones, y resumen calculado
- Se limpia automáticamente al:
  - Confirmar la importación
  - Cancelar
  - Salir de la página (GET request)

### Funciones Nuevas:
- `importar_balance_preview()` - Procesa archivo sin tocar BD, devuelve estadísticas
- Modificación de `importar_balance_view()` - Maneja el flujo de 2 pasos

### Sesiones Django:
- Requiere que las sesiones estén habilitadas (por defecto sí lo están)
- Los datos se almacenan del lado del servidor
- La sesión expira según configuración de Django

---

**Sistema listo para uso con las nuevas funcionalidades.**
