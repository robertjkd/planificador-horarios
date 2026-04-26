# Planificador de Horarios Académicos

Sistema web Django 5.0 para la planificación automática de horarios académicos utilizando OR-Tools CP-SAT. Permite importar balances de carga, generar horarios automáticamente con restricciones complejas, visualizarlos en formato tabular y exportarlos en múltiples formatos.

## Características Principales

- **Importación de balance de carga**: Soporte para CSV y Excel (.xlsx) con formato matriz o columnar
- **Generación automática de horarios**: Motor OR-Tools CP-SAT con restricciones duras y blandas
- **Visualización tabular**: Horarios organizados por día con columnas por grupo
- **Edición manual**: Modificación de asignaciones con validación de restricciones
- **Exportación multi-formato**: PDF, Excel (.xlsx) y CSV
- **Control de acceso basado en roles**: Vicedecano, Planificador, Consulta
- **Gestión de recursos académicos**: Años, grupos, asignaturas, profesores, locales, franjas horarias

## Stack Tecnológico

- **Backend**: Python 3.11, Django 5.0.4
- **Base de datos**: PostgreSQL 16 (producción) / SQLite3 (desarrollo)
- **Optimización**: OR-Tools 9.8.3296 (CP-SAT)
- **Procesamiento de datos**: pandas 2.2.1, openpyxl 3.1.2
- **Generación de PDF**: xhtml2pdf 0.2.7
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Testing**: pytest, pytest-django
- **Configuración**: django-environ 0.11.2

## Arquitectura de la Aplicación

El proyecto está organizado en las siguientes aplicaciones Django:

- **`usuarios`**: Modelo de usuario personalizado (`Usuario`) con sistema de roles (RBAC)
- **`academico`**: Modelos de recursos académicos (AñoAcademico, Grupo, Asignatura, Profesor, Local, FranjaHoraria, AsignacionProfesor)
- **`horario`**: Modelos de planificación (ActividadPlan, Asignacion), motor de scheduler (`scheduler.py`), visualización y exportación
- **`planificacion`**: Vistas de gestión de recursos, importación de balance, generación y modificación manual de horarios

### Flujo de Datos

1. **Importación**: Balance de carga (CSV/Excel) → `ActividadPlan`
2. **Configuración**: Recursos académicos → Base de datos
3. **Generación**: `ActividadPlan` + Recursos → OR-Tools CP-SAT → `Asignacion`
4. **Visualización**: `Asignacion` → Tabla horario (web)
5. **Exportación**: `Asignacion` → PDF/Excel/CSV

## Roles de Usuario

### Vicedecano (Administrador)
- Importar balance de carga
- CRUD completo de usuarios
- Asignar roles (solo PLANIFICADOR o CONSULTA)
- Visualizar cualquier horario
- Exportar horarios

### Planificador Académico
- CRUD de recursos académicos (Año, Grupo, Local, FranjaHoraria, Asignatura, Profesor, AsignacionProfesor)
- Ejecutar generación automática de horarios
- Modificar manualmente asignaciones
- Visualizar horarios de todos los grupos
- Exportar horarios

### Consulta (Estudiante/Profesor)
- Visualizar horario (filtrado por grupo o profesor)
- Descargar/exportar horario visible

## Requisitos Previos

- Python 3.11+
- PostgreSQL 16 (para producción) o SQLite3 (para desarrollo)
- pip (gestor de paquetes Python)
- git (para clonar el repositorio)

## Instalación y Configuración Local

### 1. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd planificador-de-horaios
```

### 2. Crear Entorno Virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Copiar el archivo de ejemplo y crear `.env`:

```bash
cp .env.example .env
```

Editar `.env` según el motor de base de datos deseado:

#### Opción A: SQLite (Desarrollo Rápido)

```env
DB_ENGINE=sqlite
DB_NAME=db.sqlite3
DEBUG=True
SECRET_KEY=tu-secret-key-generada
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Ventajas**: No requiere configuración de servidor de base de datos, ideal para desarrollo rápido.
**Limitaciones**: No recomendado para producción con múltiples usuarios concurrentes.

#### Opción B: PostgreSQL (Producción)

```env
DB_ENGINE=postgresql
DB_NAME=planificador_db
DB_USER=postgres
DB_PASSWORD=123456
DB_HOST=localhost
DB_PORT=5432
DEBUG=True
SECRET_KEY=tu-secret-key-generada
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Ventajas**: Robusto, soporta concurrencia, recomendado para producción.
**Requisitos**: PostgreSQL debe estar instalado y configurado.

### 5. Configurar PostgreSQL (Solo si DB_ENGINE=postgresql)

```bash
# Crear base de datos
createdb planificador_db

# O usando psql
psql -U postgres
CREATE DATABASE planificador_db;
\q
```

### 6. Ejecutar Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

**Nota**: Las migraciones funcionan tanto con SQLite como con PostgreSQL. No se requieren migraciones separadas.

### 7. Verificar Configuración de Base de Datos (Opcional)

```bash
python manage.py check_db_config
```

Este comando verifica la configuración de base de datos y emite advertencias si se está usando SQLite en producción (DEBUG=False).

### 8. Crear Superusuario (Vicedecano)

```bash
python manage.py createsuperuser
```

Sigue las instrucciones para crear el usuario administrador inicial. Este usuario tendrá rol VICEDECANO por defecto.

### 9. Cargar Datos Iniciales (Opcional)

Para cargar datos de prueba (años académicos, grupos, locales, etc.):

```bash
python manage.py loaddata fixtures/initial_data.json
```

O desde el shell de Django:

```bash
python manage.py shell
```

```python
from academico.models import AnioAcademico, Grupo, Local, FranjaHoraria, Asignatura, Profesor
from usuarios.models import Usuario

# Crear año académico
anio = AnioAcademico.objects.create(nombre="1er Año", turno="M")

# Crear grupos
Grupo.objects.create(nombre="G1", anio=anio, cantidad_alumnos=30)
Grupo.objects.create(nombre="G2", anio=anio, cantidad_alumnos=28)

# Crear locales
Local.objects.create(codigo="A101", nombre="Aula 101", tipo="A", capacidad=40)
Local.objects.create(codigo="S201", nombre="Salón 201", tipo="S", capacidad=120)
Local.objects.create(codigo="LAB1", nombre="Laboratorio 1", tipo="L", capacidad=30)

# Crear franjas horarias
FranjaHoraria.objects.create(dia_semana=0, hora_inicio="08:00", hora_fin="09:20", turno="M")
FranjaHoraria.objects.create(dia_semana=0, hora_inicio="09:30", hora_fin="10:50", turno="M")
```

## Ejecutar el Servidor de Desarrollo

```bash
python manage.py runserver
```

El servidor estará disponible en `http://127.0.0.1:8000/`

## Uso del Sistema

### Acceso al Panel de Administración

El panel de administración de Django está disponible en `/admin/`. Úsalo para gestionar rápidamente los modelos académicos.

### Flujo de Trabajo Típico

#### 1. Importar Balance de Carga (Vicedecano)

1. Acceder como Vicedecano
2. Navegar a `/planificacion/importar-balance/`
3. Seleccionar año académico
4. Subir archivo CSV o Excel
5. Configurar opciones:
   - **Eliminar actividades previas**: Limpia `ActividadPlan` del año antes de importar
   - **Crear asignaturas automáticamente**: Crea asignaturas inexistentes

**Formato CSV** (columnas: asignatura, semana, dia, actividad):
```csv
asignatura,semana,dia,actividad
Álgebra,1,1,C
Álgebra,1,2,CP
Programación,1,1,L
```

**Formato Excel matriz** (encabezados: Asignatura, S1D1, S1D2, …):
```
Asignatura | S1D1 | S1D2 | S1D3
Álgebra    | C    | CP   |
Programación| L   | L    |
```

#### 2. Configurar Recursos (Planificador)

Antes de generar horarios, asegúrate de tener configurados:
- Locales con tipo y capacidad adecuada
- Profesores asignados a asignaturas vía `AsignacionProfesor`
- Franjas horarias por turno
- Grupos con cantidad de alumnos

#### 3. Generar Horario Automático (Planificador)

1. Navegar a `/planificacion/generar/`
2. Seleccionar año académico y semana
3. El sistema ejecuta OR-Tools CP-SAT (aprox. 30 segundos)
4. Revisa el resultado y estadísticas

#### 4. Modificar Manualmente (Planificador)

1. En la vista del horario, hacer clic en una celda (solo visible para Planificadores)
2. Modal con formulario para cambiar franja, local o profesor
3. El sistema valida restricciones antes de guardar

#### 5. Visualizar y Exportar (Todos los roles)

1. Navegar a `/horario/`
2. Seleccionar año y semana
3. Aplicar filtros opcionales (grupo, profesor)
4. Usar botones de exportación: PDF, Excel, CSV

### Creación de Usuarios

Solo el Vicedecano puede crear usuarios y asignar roles:

1. Acceder como Vicedecano
2. Navegar a `/usuarios/crear/` o usar el admin
3. El sistema no permite crear otros usuarios con rol VICEDECANO (protección contra escalada de privilegios)

## Pruebas

Ejecutar las pruebas con pytest:

```bash
# Instalar dependencias de desarrollo
pip install pytest pytest-django

# Ejecutar todas las pruebas
pytest

# Ejecutar pruebas de una app específica
pytest academico/tests/

# Ejecutar con cobertura
pytest --cov=academico --cov=horario --cov=planificacion
```

### Pruebas con Diferentes Motores de Base de Datos

Para probar con SQLite (por defecto):

```bash
pytest
```

Para probar con PostgreSQL:

```bash
# En Windows (PowerShell)
$env:DB_ENGINE="postgresql"; pytest

# En Linux/Mac
DB_ENGINE=postgresql pytest
```

O crea un archivo `.env.test` con la configuración de PostgreSQL y ejecuta:

```bash
export DJANGO_SETTINGS_MODULE=planificador.settings
python -c "import os; os.environ['DB_ENGINE']='postgresql'"
pytest
```

## Despliegue en Producción

### Recomendaciones

1. **Servidor WSGI**: Usar Gunicorn
   ```bash
   pip install gunicorn
   gunicorn planificador.wsgi:application --bind 0.0.0.0:8000
   ```

2. **Servidor Web**: Configurar Nginx como reverse proxy
   - Servir archivos estáticos
   - Terminar SSL/TLS
   - Configurar cabeceras de seguridad

3. **Configuración Django** (`settings.py`):
   ```python
   DEBUG = False
   ALLOWED_HOSTS = ['tu-dominio.com']
   SECURE_SSL_REDIRECT = True
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   STATIC_ROOT = '/var/www/static/'
   ```

4. **Archivos estáticos**:
   ```bash
   python manage.py collectstatic
   ```

5. **Base de datos**: Usar PostgreSQL en producción con credenciales seguras
   - Configurar `DB_ENGINE=postgresql` en `.env`
   - SQLite solo para desarrollo (DEBUG=True)

6. **Variables de entorno**: Nunca incluir `SECRET_KEY` o credenciales en el código
   - Usar archivo `.env` (incluido en `.gitignore`)
   - Referencia: `.env.example`

## Estructura del Proyecto

```
planificador-de-horaios/
├── manage.py
├── requirements.txt
├── README.md
├── SEGURIDAD.md
├── planificador/              # Configuración del proyecto
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── usuarios/                  # Modelo Usuario personalizado y autenticación
│   ├── __init__.py
│   ├── models.py              # Usuario con campo rol
│   ├── views.py               # Login, logout, CRUD usuarios
│   ├── forms.py               # UsuarioCreationForm, UsuarioChangeForm
│   ├── urls.py
│   └── admin.py
├── academico/                 # Modelos académicos
│   ├── __init__.py
│   ├── models.py              # AnioAcademico, Grupo, Asignatura, Profesor, Local, FranjaHoraria, AsignacionProfesor, ActividadPlan, Asignacion
│   ├── views.py               # CRUD de recursos académicos
│   ├── forms.py               # Formularios para modelos académicos
│   ├── urls.py
│   └── admin.py
├── horario/                   # Visualización y exportación de horarios
│   ├── __init__.py
│   ├── models.py              # (vacío, modelos en academico)
│   ├── views.py               # ver_horario, exportar_horario, editar_asignacion
│   ├── forms.py               # EditarAsignacionForm
│   ├── urls.py
│   ├── scheduler.py           # Motor OR-Tools CP-SAT
│   ├── templatetags/          # Filtros de template
│   │   ├── __init__.py
│   │   └── horario_filters.py
│   └── admin.py
├── planificacion/             # Gestión de planificación
│   ├── __init__.py
│   ├── views.py               # importar_balance, generar_horario
│   ├── forms.py               # ImportarBalanceForm
│   ├── permissions.py         # Decoradores y mixins de RBAC
│   ├── urls.py
│   ├── mixins.py              # Mixins para CBV
│   └── management/
│       └── commands/
│           └── importar_balance.py
└── templates/                 # Plantillas HTML
    ├── base.html
    ├── home.html
    ├── usuarios/
    │   ├── login.html
    │   └── usuario_form.html
    ├── academico/
    │   └── (templates CRUD)
    ├── planificacion/
    │   ├── importar_balance.html
    │   ├── seleccionar_generacion.html
    │   └── generar_resultado.html
    └── horario/
        ├── horario.html
        ├── seleccionar_horario.html
        ├── modal_editar_asignacion.html
        └── pdf_horario.html
```

## Tipos de Actividad

- **C, CE**: Conferencia → 1 registro, `grupo=None`, `requiere_local=True`
- **CP**: Clase Práctica → Replicada por cada grupo, `requiere_local=True`
- **L**: Laboratorio → Replicada por cada grupo, `requiere_local=True`
- **S**: Seminario → Replicada por cada grupo, `requiere_local=True`
- **T, TE**: Taller → Replicada por cada grupo, `requiere_local=True`
- **PP**: Práctica Profesional → Replicada por cada grupo, `requiere_local=True`
- **E**: Educación Física → Replicada por cada grupo, `requiere_local=True`, local debe ser tipo O (Polideportivo)
- **NP**: No Presencial → 1 registro, `grupo=None`, `requiere_local=False`

## Reglas de Presentación

- **Educación Física**: Se muestra solo con la abreviatura de la asignatura (sin tipo ni local)
- **Conferencias**: Se expanden a todas las columnas de grupo en la visualización
- **Celdas vacías**: Donde no hay asignación

## Restricciones del Scheduler

### Restricciones Duras
- Cada actividad asignada exactamente una vez
- Sin conflictos de grupo (incluyendo conferencias)
- Sin conflictos de profesor
- Sin conflictos de local
- Capacidad suficiente del local
- Compatibilidad tipo local-actividad
- Turno correcto
- Día correcto

### Restricciones Blandas (con pesos)
- Minimizar huecos en horario de grupo (PESO_HUECO_GRUPO = 10)
- Distribuir carga diaria de asignatura (PESO_CARGA_DIARIA = 5)
- Evitar fatiga de profesor (más de 3 franjas consecutivas) (PESO_FATIGA_PROFESOR = 7)
- Minimizar cambios de edificio (PESO_CAMBIO_EDIFICIO = 3)

## Cambiar Entre Motores de Base de Datos

### De SQLite a PostgreSQL

1. Editar `.env`:
   ```env
   DB_ENGINE=postgresql
   DB_NAME=planificador_db
   DB_USER=postgres
   DB_PASSWORD=123456
   DB_HOST=localhost
   DB_PORT=5432
   ```

2. Crear la base de datos en PostgreSQL:
   ```bash
   createdb planificador_db
   ```

3. Ejecutar migraciones:
   ```bash
   python manage.py migrate
   ```

### De PostgreSQL a SQLite

1. Editar `.env`:
   ```env
   DB_ENGINE=sqlite
   DB_NAME=db.sqlite3
   ```

2. Ejecutar migraciones:
   ```bash
   python manage.py migrate
   ```

**Nota**: Los datos no se transfieren automáticamente entre motores. Para migrar datos, usa `python manage.py dumpdata` y `python manage.py loaddata`.

## Compatibilidad de Modelos

Todos los modelos del proyecto son compatibles con SQLite y PostgreSQL:

- **Sin campos exclusivos de PostgreSQL**: No se usan `ArrayField`, `HStoreField`, `JSONField` específicos de PostgreSQL
- **Índices estándar**: Todos los índices son `models.Index` estándar (compatibles con ambos motores)
- **Restricciones**: `CheckConstraint` y `unique_together` son compatibles con ambos motores
- **Migraciones**: Las migraciones funcionan en ambos motores sin modificaciones

## Licencia

Este proyecto es propiedad de la institución educativa. Todos los derechos reservados.

## Créditos

Desarrollado para el sistema de gestión académica de la facultad.

- **Backend**: Django 5.0.4, OR-Tools CP-SAT
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Base de datos**: PostgreSQL 16

## Soporte

Para reportar problemas o solicitar mejoras, contactar al equipo de desarrollo.
