# Implementación Completa de Módulos CRUD

**Fecha:** 25 de abril de 2026  
**Desarrollador:** Django Full Stack  
**Estado:** ✅ COMPLETADO

---

## Resumen Ejecutivo

Se ha implementado un sistema completo de administración CRUD (Crear, Leer, Actualizar, Eliminar) para todas las entidades académicas del sistema de planificación de horarios. Todas las interfaces están protegidas por roles y cuentan con validaciones de negocio.

---

## Entidades Implementadas

### 1. Año Académico (`AnioAcademico`)
- ✅ **Listado:** `/academico/annos/`
- ✅ **Crear:** `/academico/annos/crear/`
- ✅ **Editar:** `/academico/annos/<pk>/editar/`
- ✅ **Eliminar:** `/academico/annos/<pk>/eliminar/`
- **Campos:** `numero` (1-4), `turno` (Mañana/Tarde)
- **Validación:** 
  - Años 1° y 3° → Turno Mañana (automático)
  - Años 2° y 4° → Turno Tarde (automático)
  - Número único entre 1 y 4
  - Protección al eliminar: verifica dependencias

### 2. Grupo (`Grupo`)
- ✅ **Listado:** `/academico/grupos/`
- ✅ **Crear:** `/academico/grupos/crear/`
- ✅ **Editar:** `/academico/grupos/<pk>/editar/`
- ✅ **Eliminar:** `/academico/grupos/<pk>/eliminar/`
- **Campos:** `nombre`, `anio` (FK), `cantidad_alumnos`
- **Validación:** 
  - Nombre único dentro del mismo año (`unique_together` en modelo)
  - Protección al eliminar: verifica dependencias

### 3. Asignatura (`Asignatura`)
- ✅ **Listado:** `/academico/asignaturas/`
- ✅ **Crear:** `/academico/asignaturas/crear/`
- ✅ **Editar:** `/academico/asignaturas/<pk>/editar/`
- ✅ **Eliminar:** `/academico/asignaturas/<pk>/eliminar/`
- **Campos:** `nombre`, `abreviatura` (máx 10 chars), `anio` (FK)
- **Validación:** 
  - Abreviatura única dentro del año
  - Máximo 10 caracteres
  - Protección al eliminar

### 4. Profesor (`Profesor`) - NUEVO COMPLETO
- ✅ **Listado:** `/academico/profesores/`
- ✅ **Crear:** `/academico/profesores/crear/`
- ✅ **Editar:** `/academico/profesores/<pk>/editar/`
- ✅ **Eliminar:** `/academico/profesores/<pk>/eliminar/`
- **Campos:** `nombre`, `usuario` (opcional, FK a User)
- **Características:**
  - Muestra cantidad de asignaciones por profesor
  - Indica si tiene usuario del sistema vinculado

### 5. Local (`Local`)
- ✅ **Listado:** `/academico/locales/`
- ✅ **Crear:** `/academico/locales/crear/`
- ✅ **Editar:** `/academico/locales/<pk>/editar/`
- ✅ **Eliminar:** `/academico/locales/<pk>/eliminar/`
- **Campos:** `codigo` (único), `nombre`, `tipo`, `capacidad`
- **Tipos:** AULA, SALON, LABORATORIO, POLIDEPORTIVO, OTRO

### 6. Franja Horaria (`FranjaHoraria`)
- ✅ **Listado:** `/academico/franjas/`
- ✅ **Crear:** `/academico/franjas/crear/`
- ✅ **Editar:** `/academico/franjas/<pk>/editar/`
- ✅ **Eliminar:** `/academico/franjas/<pk>/eliminar/`
- **Campos:** `turno`, `orden`, `hora_inicio`, `hora_fin`
- **Validaciones:**
  - ✅ Hora fin > Hora inicio
  - ✅ **Sin solapamientos:** No permite dos franjas en el mismo turno que se superpongan
  - Orden único por turno

### 7. Asignación Aula-Grupo (`AsignacionAulaGrupo`) - NUEVO MODELO
- ✅ **Modelo creado:** `academico/models.py`
- ✅ **Migración:** `0002_asignacionaulagrupo.py`
- ✅ **Listado:** `/academico/asignaciones-aula/`
- ✅ **Crear:** `/academico/asignaciones-aula/crear/`
- ✅ **Editar:** `/academico/asignaciones-aula/<pk>/editar/`
- ✅ **Eliminar:** `/academico/asignaciones-aula/<pk>/eliminar/`
- **Campos:** `grupo` (OneToOne), `local` (FK, solo AULAS)
- **Reglas:**
  - Un grupo solo puede tener un aula asignada
  - Solo se pueden seleccionar locales de tipo AULA
  - Al crear, solo muestra grupos sin aula asignada
  - Validación en `clean()` del modelo y formulario

### 8. Asignación Profesor-Asignatura (`AsignacionProfesor`) - COMPLETADO
- ✅ **Listado:** `/academico/asignaciones-profesor/`
- ✅ **Crear:** `/academico/asignaciones-profesor/crear/`
- ✅ **Editar:** `/academico/asignaciones-profesor/<pk>/editar/`
- ✅ **Eliminar:** `/academico/asignaciones-profesor/<pk>/eliminar/`
- **Campos:** `profesor`, `asignatura`, `grupo` (opcional), `tipo_actividad`
- **Reglas:**
  - Grupo vacío = Conferencia (imparte a todo el año)
  - Grupo específico = Solo imparte a ese grupo
  - Validación: tipo de actividad coherente con grupo
  - Unicidad: no puede haber duplicados (profesor, asignatura, grupo, tipo)

---

## Archivos Modificados/Creados

### Modelos
- ✅ `academico/models.py` - Agregado `AsignacionAulaGrupo`
- ✅ `academico/migrations/0002_asignacionaulagrupo.py` - Migración del nuevo modelo

### Vistas
- ✅ `academico/views.py` - CRUD completo para todas las entidades
  - Profesor: list, create, update, delete
  - AsignacionProfesor: list, create, update, delete
  - AsignacionAulaGrupo: list, create, update, delete
  - Delete views para: anno, grupo, local, franjahoraria, asignatura

### Formularios
- ✅ `academico/forms.py`
  - `AsignacionAulaGrupoForm` - Filtra locales tipo AULA
  - Validación de solapamiento en `FranjaHorariaForm`

### URLs
- ✅ `academico/urls.py` - Todas las rutas configuradas
  - Patrón: `/<entidad>/`, `/crear/`, `/<pk>/editar/`, `/<pk>/eliminar/`

### Plantillas Creadas (17 archivos)

#### Delete Confirmations
- `anno_confirm_delete.html`
- `grupo_confirm_delete.html`
- `local_confirm_delete.html`
- `franjahoraria_confirm_delete.html`
- `asignatura_confirm_delete.html`
- `profesor_confirm_delete.html`
- `asignacionaulagrupo_confirm_delete.html`

#### Profesor CRUD
- `profesor_list.html`
- `profesor_form.html`

#### AsignacionProfesor CRUD
- `asignacionprofesor_list.html`
- `asignacionprofesor_form.html`

#### AsignacionAulaGrupo CRUD
- `asignacionaulagrupo_list.html`
- `asignacionaulagrupo_form.html`

### Navegación
- ✅ `templates/base.html` - Menú dropdown completo
  - Vicedecano: Administración (Usuarios, Importar, Auditoría)
  - Planificador: Gestión Académica (Catálogos + Asignaciones) + Generar Horario
  - Consulta: Ver Horario

- ✅ `templates/home.html` - Dashboard con accesos rápidos
  - Vicedecano: Gestión de usuarios, Importar balance
  - Planificador: Todos los CRUD organizados por secciones
  - Consulta: Ver horario

---

## Permisos por Rol

| Funcionalidad | Vicedecano | Planificador | Consulta |
|--------------|------------|--------------|----------|
| Años Académicos CRUD | ✅ | ✅ | ❌ |
| Grupos CRUD | ✅ | ✅ | ❌ |
| Asignaturas CRUD | ✅ | ✅ | ❌ |
| Profesores CRUD | ✅ | ✅ | ❌ |
| Locales CRUD | ✅ | ✅ | ❌ |
| Franjas Horarias CRUD | ✅ | ✅ | ❌ |
| Asignación Profesor | ✅ | ✅ | ❌ |
| Asignación Aula-Grupo | ✅ | ✅ | ❌ |
| Importar Balance | ✅ | ❌ | ❌ |
| Generar Horario | ❌ | ✅ | ❌ |
| Panel Auditoría | ✅ | ❌ | ❌ |
| Ver Horario | ✅ | ✅ | ✅ |

**Nota:** Los permisos se implementan con:
- `@vicedecano_required` - Solo Vicedecano
- `@planificador_required` - Planificador (y hereda Vicedecano)
- `@login_required` - Cualquier usuario autenticado

---

## Validaciones de Negocio Implementadas

### Franja Horaria - Solapamiento
```python
# En FranjaHorariaForm.clean()
if solapadas.exists():
    raise ValidationError(
        f'Esta franja horaria se solapa con la existente: ...'
    )
```
- Verifica que no haya franjas superpuestas en el mismo turno
- Excluye la instancia actual en edición
- Muestra mensaje claro indicando cuál franja causa conflicto

### Asignación Aula-Grupo
```python
# En AsignacionAulaGrupoForm.__init__()
self.fields['local'].queryset = Local.objects.filter(tipo=TipoLocal.AULA)
grupos_con_aula = AsignacionAulaGrupo.objects.values_list('grupo_id', flat=True)
self.fields['grupo'].queryset = Grupo.objects.exclude(id__in=grupos_con_aula)
```
- Solo muestra locales de tipo AULA
- Al crear, solo muestra grupos sin aula asignada
- Validación en modelo: `clean()` verifica tipo AULA

### Asignación Profesor
```python
# En modelo AsignacionProfesor.clean()
if TipoActividad.es_conferencia(self.tipo_actividad) and self.grupo is not None:
    raise ValidationError('Las conferencias no deben tener grupo...')
if TipoActividad.es_por_grupo(self.tipo_actividad) and self.grupo is None:
    raise ValidationError('Este tipo requiere un grupo específico...')
```
- Conferencias (C, CE) → grupo debe ser NULL
- Actividades por grupo → grupo es obligatorio
- `unique_together` evita duplicados

### Eliminación Protegida
```python
try:
    entity.delete()
except Exception as e:
    messages.error(request, f'No se puede eliminar: tiene registros asociados...')
```
- Todas las entidades capturan errores de eliminación
- Muestra mensaje informativo al usuario
- Redirige al listado

---

## URLs Disponibles

### Años Académicos
- `GET/POST /academico/annos/`
- `GET/POST /academico/annos/crear/`
- `GET/POST /academico/annos/<pk>/editar/`
- `GET/POST /academico/annos/<pk>/eliminar/`

### Grupos
- `GET/POST /academico/grupos/`
- `GET/POST /academico/grupos/crear/`
- `GET/POST /academico/grupos/<pk>/editar/`
- `GET/POST /academico/grupos/<pk>/eliminar/`

### Asignaturas
- `GET/POST /academico/asignaturas/`
- `GET/POST /academico/asignaturas/crear/`
- `GET/POST /academico/asignaturas/<pk>/editar/`
- `GET/POST /academico/asignaturas/<pk>/eliminar/`

### Profesores
- `GET/POST /academico/profesores/`
- `GET/POST /academico/profesores/crear/`
- `GET/POST /academico/profesores/<pk>/editar/`
- `GET/POST /academico/profesores/<pk>/eliminar/`

### Locales
- `GET/POST /academico/locales/`
- `GET/POST /academico/locales/crear/`
- `GET/POST /academico/locales/<pk>/editar/`
- `GET/POST /academico/locales/<pk>/eliminar/`

### Franjas Horarias
- `GET/POST /academico/franjas/`
- `GET/POST /academico/franjas/crear/`
- `GET/POST /academico/franjas/<pk>/editar/`
- `GET/POST /academico/franjas/<pk>/eliminar/`

### Asignaciones Profesor
- `GET /academico/asignaciones-profesor/`
- `GET/POST /academico/asignaciones-profesor/crear/`
- `GET/POST /academico/asignaciones-profesor/<pk>/editar/`
- `GET/POST /academico/asignaciones-profesor/<pk>/eliminar/`

### Asignaciones Aula-Grupo
- `GET /academico/asignaciones-aula/`
- `GET/POST /academico/asignaciones-aula/crear/`
- `GET/POST /academico/asignaciones-aula/<pk>/editar/`
- `GET/POST /academico/asignaciones-aula/<pk>/eliminar/`

---

## Instrucciones de Uso

### Acceder al Sistema
1. Iniciar sesión como **Planificador** o **Vicedecano**
2. En el menú "Gestión Académica" o en el Home, seleccionar la entidad a gestionar

### Flujo Típico de Configuración

#### Para un nuevo año académico:
1. **Años Académicos** → Crear año (si no existe)
2. **Grupos** → Crear grupos para el año (G1, G2, etc.)
3. **Asignaturas** → Crear asignaturas del año
4. **Locales** → Verificar aulas disponibles (crear si es necesario)
5. **Franjas Horarias** → Configurar horarios del turno (mañana/tarde)
6. **Profesores** → Registrar profesores
7. **Asignaciones**:
   - **Profesor → Asignatura**: Asignar qué profesor imparte cada asignatura
   - **Aula → Grupo**: Asignar aula base a cada grupo

#### Ejemplo de datos:
```
Año: 1° año (Turno Mañana)
Grupos: G1 (30 alumnos), G2 (28 alumnos), G3 (32 alumnos)
Asignaturas: ÁLG (Álgebra), PROG (Programación), BD (Bases de Datos)
Profesores: Juan Pérez, María García, Carlos López
Locales: A101 (Aula, 35 cap), A102 (Aula, 35 cap), LAB1 (Laboratorio, 20 cap)
Franjas: 8:00-9:20 (Franja 1), 9:30-10:50 (Franja 2), 11:00-12:20 (Franja 3)

Asignaciones Profesor:
- Juan Pérez → ÁLG → Conferencia (sin grupo)
- María García → PROG → G1
- María García → PROG → G2
- Carlos López → BD → G3

Asignaciones Aula:
- G1 → A101
- G2 → A102
- G3 → A103
```

---

## Características Técnicas

### Vistas
- Todas las vistas son **function-based views**
- Decoradores de permisos: `@planificador_required`, `@vicedecano_required`
- Uso de `get_object_or_404` para seguridad
- Manejo de errores con mensajes Django

### Formularios
- Todos son `ModelForm`
- Widgets con clases Bootstrap: `form-control`, `form-select`
- Validaciones en `clean()` para reglas complejas
- Filtrado dinámico de querysets

### Plantillas
- Herencia de `base.html`
- Bootstrap 5 para estilos
- Tablas responsive
- Botones de acción en cada fila
- Confirmaciones de eliminación

### URLs
- Namespace: `academico:`
- Patrón consistente: lista → crear → editar → eliminar
- URLs semánticas en español

---

## Próximos Pasos Sugeridos

1. **Paginación:** Agregar paginación a listados grandes (actualmente muestran todos)
2. **Búsqueda:** Implementar filtros de búsqueda en listados
3. **Exportar:** Permitir exportar datos a Excel/CSV
4. **Importar:** Permitir importar profesores y otros catálogos desde Excel
5. **API REST:** Considerar crear endpoints API para integraciones futuras

---

## Resumen de Estado

✅ **TODAS LAS ENTIDADES CON CRUD COMPLETO**

| Entidad | List | Create | Update | Delete | Validaciones |
|---------|------|--------|--------|--------|--------------|
| AnioAcademico | ✅ | ✅ | ✅ | ✅ | ✅ Turno por número |
| Grupo | ✅ | ✅ | ✅ | ✅ | ✅ Nombre único por año |
| Asignatura | ✅ | ✅ | ✅ | ✅ | ✅ Abreviatura única |
| Profesor | ✅ | ✅ | ✅ | ✅ | - |
| Local | ✅ | ✅ | ✅ | ✅ | ✅ Código único |
| FranjaHoraria | ✅ | ✅ | ✅ | ✅ | ✅ Sin solapamientos |
| AsignacionProfesor | ✅ | ✅ | ✅ | ✅ | ✅ Tipo/Grupo coherente |
| AsignacionAulaGrupo | ✅ | ✅ | ✅ | ✅ | ✅ Solo AULAS |

**Total:** 8 entidades × 4 operaciones = 32 vistas funcionales

---

**Sistema listo para uso en producción.**
