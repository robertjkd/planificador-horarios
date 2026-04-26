# Modelo de Datos - Sistema de Planificación de Horarios

**Documento Técnico - Arquitectura de Datos**  
**Rol:** Ingeniero Backend  
**Fecha:** 26 de abril de 2026  
**Stack:** Django 5.0.4 + PostgreSQL/SQLite

---

## 1. RESUMEN EJECUTIVO

El sistema gestiona la planificación horaria de una facultad universitaria con 4 años académicos, cada uno con grupos de estudiantes, asignaturas, profesores y locales. El modelo está diseñado para soportar:

- **Importación de balance de carga** (formato Excel/CSV)
- **Generación automática de horarios** mediante solver CP-SAT
- **Asignación de recursos** (profesores, locales, franjas horarias)
- **Auditoría de cambios** y control de acceso por roles

---

## 2. DIAGRAMA ENTIDAD-RELACIÓN (ERD)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MODELO DE DATOS                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐         ┌──────────────────────┐
│   AnioAcademico      │         │      Profesor        │
├──────────────────────┤         ├──────────────────────┤
│ PK id                │         │ PK id                │
│ numero (1-4) UQ      │         │ nombre               │
│ turno (M/T)          │         │ FK usuario (opt)     │
└──────┬───────────────┘         └──────┬───────────────┘
       │                                │
       │ 1:N                            │ 1:N
       ▼                                ▼
┌──────────────────────┐         ┌──────────────────────┐
│       Grupo          │         │ AsignacionProfesor  │
├──────────────────────┤         ├──────────────────────┤
│ PK id                │◄────────│ PK id                │
│ FK anio              │   1:1   │ FK profesor          │
│ nombre               │         │ FK asignatura        │
│ cantidad_alumnos     │         │ FK grupo (opt)       │
└──────┬───────────────┘         │ tipo_actividad       │
       │                         └──────┬───────────────┘
       │ 1:N                            │ N:1
       ▼                                ▼
┌──────────────────────┐         ┌──────────────────────┐
│    Asignatura        │         │    Asignatura        │
├──────────────────────┤         └──────────────────────┘
│ PK id                │
│ FK anio              │
│ nombre               │         ┌──────────────────────┐
│ abreviatura (10ch)   │         │ AsignacionAulaGrupo │
└──────┬───────────────┘         ├──────────────────────┤
       │                         │ PK id                │
       │ 1:N                     │ FK grupo (UQ)        │◄────┐
       ▼                         │ FK local             │     │
┌──────────────────────┐         └──────────────────────┘     │
│    ActividadPlan     │                                       │
├──────────────────────┤                                       │
│ PK id                │                                       │
│ FK asignatura        │                                       │
│ FK anio (denorm)     │                                       │
│ FK grupo (opt)       │                                       │
│ tipo_actividad       │                                       │
│ semana               │                                       │
│ dia_semana           │                                       │
│ orden_secuencia      │                                       │
│ FK local_asignado    │◄──────────────────────────────────────┘
│ FK profesor_asignado │
│ tipo_asignacion      │
│ estado               │
└──────────────────────┘

┌──────────────────────┐         ┌──────────────────────┐
│   FranjaHoraria      │         │       Local          │
├──────────────────────┤         ├──────────────────────┤
│ PK id                │         │ PK id                │
│ turno (M/T)          │         │ codigo UQ            │
│ orden                │         │ nombre               │
│ hora_inicio          │         │ tipo (AULA/SALON/    │
│ hora_fin             │         │      LAB/POLI/OTRO)  │
└──────────────────────┘         │ capacidad            │
                                 └──────────────────────┘

┌──────────────────────┐
│    Auditoria         │
├──────────────────────┤
│ PK id                │
│ FK usuario           │
│ accion               │
│ entidad_afectada     │
│ detalle              │
│ fecha                │
└──────────────────────┘

┌──────────────────────┐         ┌──────────────────────┐
│      Usuario         │◄────────│     Profesor        │
│  (AbstractUser)      │  1:1    │  (relacion opt)     │
├──────────────────────┤         └──────────────────────┘
│ PK id                │
│ username             │
│ rol (VICEDECANO/     │
│   PLANIFICADOR/      │
│   CONSULTA)          │
│ FK grupo (opt)       │◄──────┐
└──────────────────────┘       │
                                 │ N:1
┌──────────────────────┐       │
│       Grupo          │◄──────┘
└──────────────────────┘
```

---

## 3. ENUMERACIONES (Choices)

### 3.1 Turno
```python
class Turno(models.TextChoices):
    MANANA = 'M', 'Mañana'  # 1° y 3° año
    TARDE = 'T', 'Tarde'    # 2° y 4° año
```

### 3.2 TipoLocal
```python
class TipoLocal(models.TextChoices):
    AULA = 'AULA', 'Aula'
    SALON = 'SALON', 'Salón de Conferencia'
    LABORATORIO = 'LAB', 'Laboratorio'
    POLIDEPORTIVO = 'POLI', 'Polideportivo'
    OTRO = 'OTRO', 'Otro'
```

### 3.3 TipoActividad
```python
class TipoActividad(models.TextChoices):
    CONFERENCIA = 'C', 'Conferencia'              # UNA_SOLA_VEZ
    CONFERENCIA_ESPECIAL = 'CE', 'Conferencia Especial'  # UNA_SOLA_VEZ
    CLASE_PRACTICA = 'CP', 'Clase Práctica'       # POR_GRUPO
    LABORATORIO = 'L', 'Laboratorio'              # POR_GRUPO
    SEMINARIO = 'S', 'Seminario'                  # POR_GRUPO
    TALLER = 'T', 'Taller'                        # POR_GRUPO
    TALLER_EJERCICIOS = 'TE', 'Taller de Ejercicios'  # POR_GRUPO
    EDUCACION_FISICA = 'E', 'Educación Física'    # POR_GRUPO
    PRACTICA_PROFESIONAL = 'PP', 'Práctica Profesional'  # POR_GRUPO
    NO_PRESENCIAL = 'NP', 'No Presencial'         # UNA_SOLA_VEZ
```

**Reglas de negocio:**
- `es_conferencia()`: C, CE → grupo=None (imparte a todo el año)
- `es_por_grupo()`: CP, L, S, T, TE, E, PP → un registro por cada grupo
- `no_requiere_local()`: NP → no necesita local
- `tipo_local_requerido()`: Mapeo actividad → tipo local

### 3.4 DiaSemana
```python
class DiaSemana(models.IntegerChoices):
    LUNES = 0, 'Lunes'
    MARTES = 1, 'Martes'
    MIERCOLES = 2, 'Miércoles'
    JUEVES = 3, 'Jueves'
    VIERNES = 4, 'Viernes'
```

---

## 4. ENTIDADES DETALLADAS

### 4.1 AnioAcademico
**Tabla:** `academico_anioacademico`

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| id | AutoField | PK | Identificador único |
| numero | PositiveSmallIntegerField | UQ, Check(1-4) | 1°, 2°, 3° o 4° año |
| turno | CharField(1) | choices=Turno | M=Mañana, T=Tarde |

**Reglas de negocio:**
- 1° y 3° año → turno Mañana (validación en `clean()`)
- 2° y 4° año → turno Tarde (validación en `clean()`)
- Método `total_alumnos()`: Suma de alumnos de todos los grupos del año

**Relaciones:**
- 1:N → Grupo (related_name='grupos')
- 1:N → Asignatura (related_name='asignaturas')
- 1:N → ActividadPlan (related_name='actividades_plan')

---

### 4.2 Grupo
**Tabla:** `academico_grupo`

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| id | AutoField | PK | Identificador único |
| anio_id | ForeignKey | CASCADE, FK a AnioAcademico | Año académico |
| nombre | CharField(50) | - | Ej. G1, G2 |
| cantidad_alumnos | PositiveIntegerField | - | Para validar capacidad local |

**Constraints:**
- `unique_together`: (anio, nombre) → Un mismo año no puede tener dos grupos con mismo nombre

**Relaciones:**
- N:1 → AnioAcademico
- 1:1 → AsignacionAulaGrupo (opcional, related_name='aula_fija')
- 1:N → ActividadPlan (related_name='actividades_plan')
- 1:N → AsignacionProfesor (related_name='asignaciones_profesor')

---

### 4.3 Profesor
**Tabla:** `academico_profesor`

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| id | AutoField | PK | Identificador único |
| nombre | CharField(150) | - | Nombre completo |
| usuario_id | OneToOneField | SET_NULL, nullable | Vinculación con sistema (opcional) |

**Relaciones:**
- 1:1 → settings.AUTH_USER_MODEL (opcional, para rol CONSULTA)
- 1:N → AsignacionProfesor (related_name='asignaciones')

---

### 4.4 Asignatura
**Tabla:** `academico_asignatura`

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| id | AutoField | PK | Identificador único |
| nombre | CharField(150) | - | Nombre completo |
| abreviatura | CharField(10) | - | Para mostrar en horario compacto |
| anio_id | ForeignKey | CASCADE, FK a AnioAcademico | Año al que pertenece |

**Constraints:**
- `unique_together`: (anio, abreviatura) → Abreviatura única por año
- Index: (anio, abreviatura) → idx_asig_anio_abrev

**Relaciones:**
- N:1 → AnioAcademico
- 1:N → AsignacionProfesor (related_name='asignaciones_profesor')
- 1:N → ActividadPlan (related_name='actividades_plan')

---

### 4.5 Local
**Tabla:** `academico_local`

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| id | AutoField | PK | Identificador único |
| codigo | CharField(20) | UQ | S401, A201, LAB1, POLI |
| nombre | CharField(100) | blank=True | Descripción opcional |
| tipo | CharField(5) | choices=TipoLocal | AULA/SALON/LAB/POLI/OTRO |
| capacidad | PositiveIntegerField | - | Número de alumnos |

**Constraints:**
- Index: (tipo, capacidad) → idx_local_tipo_cap

**Relaciones:**
- 1:N → AsignacionAulaGrupo (related_name='asignaciones_grupo')
- 1:N → ActividadPlan (related_name='actividades_plan_local')

---

### 4.6 FranjaHoraria
**Tabla:** `academico_franjahoraria`

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| id | AutoField | PK | Identificador único |
| turno | CharField(1) | choices=Turno | M=Mañana, T=Tarde |
| orden | PositiveSmallIntegerField | - | Secuencia 1, 2, 3, 4... |
| hora_inicio | TimeField | - | HH:MM |
| hora_fin | TimeField | - | HH:MM |

**Constraints:**
- `unique_together`: (turno, orden) → Orden único por turno
- Index: (turno, orden) → idx_franja_turno_ord
- Validación: hora_fin > hora_inicio

---

### 4.7 AsignacionProfesor (Entidad de Relación)
**Tabla:** `academico_asignacionprofesor`

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| id | AutoField | PK | Identificador único |
| profesor_id | ForeignKey | CASCADE | Profesor asignado |
| asignatura_id | ForeignKey | CASCADE | Asignatura impartida |
| grupo_id | ForeignKey | CASCADE, nullable | NULL=Conferencia (todo el año) |
| tipo_actividad | CharField(3) | choices=TipoActividad | Modalidad que imparte |

**Constraints:**
- `unique_together`: (profesor, asignatura, grupo, tipo_actividad) → Evita duplicados
- Index: (asignatura, tipo_actividad, grupo) → idx_asignprof_asig_tipo_grp

**Reglas de validación (clean()):**
- Conferencia (C/CE) → grupo debe ser NULL
- Actividades por grupo → grupo es obligatorio

**Relaciones:**
- N:1 → Profesor
- N:1 → Asignatura
- N:1 → Grupo (opcional)

---

### 4.8 AsignacionAulaGrupo (Entidad de Relación)
**Tabla:** `academico_asignacionaulagrupo`

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| id | AutoField | PK | Identificador único |
| grupo_id | OneToOneField | CASCADE | Grupo asignado (único) |
| local_id | ForeignKey | CASCADE | Aula base |

**Constraints:**
- OneToOne en grupo → Un grupo solo puede tener un aula

**Reglas de validación (clean()):**
- El local debe ser de tipo AULA

**Relaciones:**
- 1:1 → Grupo (related_name='aula_fija')
- N:1 → Local (related_name='asignaciones_grupo')

---

### 4.9 ActividadPlan (Celdas del Horario)
**Tabla:** `academico_actividadplan`

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| id | AutoField | PK | Identificador único |
| asignatura_id | ForeignKey | CASCADE | Asignatura |
| tipo_actividad | CharField(3) | choices=TipoActividad | Modalidad |
| grupo_id | ForeignKey | CASCADE, nullable | NULL para conferencias |
| anio_id | ForeignKey | CASCADE | Denormalizado para filtros |
| semana | PositiveSmallIntegerField | - | Semana del balance (1-16) |
| dia_semana | IntegerField | choices=DiaSemana | 0=Lunes...4=Viernes |
| orden_secuencia | PositiveSmallIntegerField | - | Orden dentro del día |
| local_asignado_id | ForeignKey | CASCADE, nullable | Local asignado por solver |
| profesor_asignado_id | ForeignKey | CASCADE, nullable | Profesor asignado |
| tipo_asignacion | CharField | choices | MANUAL, SOLVER, IMPORTADA |
| estado | CharField | choices | PENDIENTE, ASIGNADA, CONFLICTO |

**Relaciones:**
- N:1 → Asignatura
- N:1 → AnioAcademico (denormalizado)
- N:1 → Grupo (opcional)
- N:1 → Local (asignado)
- N:1 → Profesor (asignado)

---

### 4.10 Auditoria
**Tabla:** `academico_auditoria`

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| id | AutoField | PK | Identificador único |
| usuario_id | ForeignKey | SET_NULL, nullable | Usuario que realizó la acción |
| accion | CharField(20) | choices=TipoAccionAuditoria | CREAR, EDITAR, ELIMINAR, IMPORTAR, GENERAR |
| entidad_afectada | CharField(50) | - | Nombre de la entidad |
| detalle | TextField | blank=True | JSON o descripción |
| fecha | DateTimeField | auto_now_add | Timestamp |

---

### 4.11 Usuario (Custom User)
**Tabla:** `usuarios_usuario` (extiende AbstractUser)

| Campo | Tipo | Constraints | Descripción |
|-------|------|-------------|-------------|
| id | AutoField | PK | Identificador único |
| username | CharField | UQ | Login |
| rol | CharField(12) | choices | VICEDECANO, PLANIFICADOR, CONSULTA |
| grupo_id | ForeignKey | SET_NULL, nullable | Para estudiantes (rol CONSULTA) |

**Relaciones:**
- N:1 → Grupo (opcional, para estudiantes)
- 1:1 → Profesor (opcional, related_name='usuario')

---

## 5. ÍNDICES DE BASE DE DATOS

| Tabla | Índice | Campos | Propósito |
|-------|--------|--------|-----------|
| Grupo | idx_grupo_anio_nombre | (anio, nombre) | Búsqueda por año y nombre |
| Local | idx_local_tipo_cap | (tipo, capacidad) | Filtrado por tipo y capacidad |
| FranjaHoraria | idx_franja_turno_ord | (turno, orden) | Ordenamiento por turno |
| Asignatura | idx_asig_anio_abrev | (anio, abreviatura) | Búsqueda por año y abreviatura |
| AsignacionProfesor | idx_asignprof_asig_tipo_grp | (asignatura, tipo_actividad, grupo) | Queries de asignación |
| ActividadPlan | idx_actplan_anio_semana_dia | (anio, semana, dia_semana) | Filtros de planificación |

---

## 6. RESTRICCIONES Y VALIDACIONES

### 6.1 Constraints de Base de Datos

```sql
-- AnioAcademico: número entre 1 y 4
CONSTRAINT anio_numero_1_a_4 CHECK (numero >= 1 AND numero <= 4)

-- Grupo: nombre único por año
UNIQUE (anio_id, nombre)

-- Asignatura: abreviatura única por año
UNIQUE (anio_id, abreviatura)

-- FranjaHoraria: orden único por turno
UNIQUE (turno, orden)

-- AsignacionProfesor: sin duplicados
UNIQUE (profesor_id, asignatura_id, grupo_id, tipo_actividad)

-- AsignacionAulaGrupo: un grupo solo un aula
UNIQUE (grupo_id)

-- Local: código único
UNIQUE (codigo)
```

### 6.2 Validaciones de Aplicación (clean())

| Entidad | Validación | Descripción |
|---------|------------|-------------|
| AnioAcademico | Turno coherente | 1,3→Mañana; 2,4→Tarde |
| Grupo | Capacidad > 0 | Cantidad de alumnos válida |
| FranjaHoraria | Horas coherentes | hora_fin > hora_inicio |
| FranjaHoraria | Sin solapamiento | No puede solaparse con otra del mismo turno |
| AsignacionProfesor | Grupo/Conferencia | Conferencias sin grupo; grupales con grupo |
| AsignacionAulaGrupo | Tipo AULA | Solo locales tipo AULA |
| ActividadPlan | Capacidad local | Capacidad >= alumnos del grupo |

---

## 7. RELACIONES CARDINALIDAD

```
AnioAcademico (1) ────< (N) Grupo
                (1) ────< (N) Asignatura
                (1) ────< (N) ActividadPlan

Grupo (1) ────< (N) AsignacionProfesor
      (1) ────< (N) ActividadPlan
      (1) ────1 (1) AsignacionAulaGrupo (opcional)

Profesor (1) ────< (N) AsignacionProfesor
         (1) ────< (N) ActividadPlan
         (1) ────1 (0..1) Usuario (opcional)

Asignatura (1) ────< (N) AsignacionProfesor
           (1) ────< (N) ActividadPlan

Local (1) ────< (N) AsignacionAulaGrupo
      (1) ────< (N) ActividadPlan

FranjaHoraria (1) ────< (N) [Implícito en solver]

Usuario (1) ────> (0..1) Grupo (para estudiantes)
```

---

## 8. FLUJOS DE DATOS PRINCIPALES

### 8.1 Importación de Balance de Carga
```
CSV/Excel → ImportarBalanceView → ActividadPlan (estado=IMPORTADA)
  ↓
Parsear filas → Crear ActividadPlan por cada celda
  ↓
Replicar por grupo (si es CP, L, S, T, TE, E, PP)
  ↓
Un solo registro (si es C, CE, NP)
```

### 8.2 Generación de Horario (Solver)
```
ActividadPlan (PENDIENTE) → CP-SAT Solver → Asignaciones
  ↓
Variables: local × franja × actividad
  ↓
Restricciones: capacidad, disponibilidad, no solapamiento
  ↓
ActividadPlan (ASIGNADA) con local_asignado y profesor_asignado
```

---

## 9. CONSIDERACIONES DE PERFORMANCE

### 9.1 QuerySets Optimizados
```python
# Uso de select_related para evitar N+1
ActividadPlan.objects.select_related(
    'asignatura', 'grupo', 'grupo__anio', 
    'local_asignado', 'profesor_asignado'
)

# Uso de prefetch_related para colecciones
AnioAcademico.objects.prefetch_related('grupos', 'asignaturas')
```

### 9.2 Denormalización
- `ActividadPlan.anio`: Denormalizado para filtros rápidos (ya se infiere por asignatura)

### 9.3 Índices Compuestos
- Todos los índices son compuestos para soportar filtros comunes
- Ordenamiento por campos frecuentes en queries

---

## 10. MIGRACIONES RELEVANTES

| Archivo | Descripción |
|---------|-------------|
| `0001_initial.py` | Modelos base (AnioAcademico, Grupo, Profesor, Local, FranjaHoraria, Asignatura, AsignacionProfesor, ActividadPlan, Auditoria) |
| `0002_asignacionaulagrupo.py` | Modelo AsignacionAulaGrupo (agregado recientemente) |

---

## 11. DIAGRAMA UML SIMPLIFICADO

```
┌────────────────────────────────────────────────────────────────┐
│                        ANIO ACADEMICO                          │
├────────────────────────────────────────────────────────────────┤
│ numero: int (1-4) ◄── UQ                                     │
│ turno: enum (M/T)                                              │
├────────────────────────────────────────────────────────────────┤
│ + total_alumnos(): int                                         │
└────────┬────────────────────────────────┬──────────────────────┘
         │ 1:N                            │ 1:N
         ▼                                ▼
┌────────────────┐              ┌────────────────┐
│     GRUPO      │              │  ASIGNATURA    │
├────────────────┤              ├────────────────┤
│ nombre: str    │              │ nombre: str    │
│ cant_alumnos: int             │ abrev: str(10) │
├────────────────┤              ├────────────────┤
│ + validar_capacidad()         │ + get_profesores()│
└────┬───────────┘              └─────┬──────────┘
     │ 1:1                            │ 1:N
     ▼                                ▼
┌────────────────┐              ┌────────────────┐
│AsignacionAula  │              │AsignacionProfesor│
├────────────────┤              ├────────────────┤
│                │              │ tipo_actividad │
└─────┬──────────┘              │ grupo: nullable│
      │ N:1                     └─────┬──────────┘
      ▼                               │
┌────────────────┐                    │ N:1
│     LOCAL      │                    ▼
├────────────────┤              ┌────────────────┐
│ codigo: str UQ │              │    PROFESOR    │
│ tipo: enum     │              ├────────────────┤
│ capacidad: int │              │ nombre: str    │
└────────────────┘              │ usuario: 1:1   │
                                └────────────────┘
```

---

**Fin del Documento Técnico**

*Generado por Ingeniero Backend - Sistema de Planificación de Horarios*
