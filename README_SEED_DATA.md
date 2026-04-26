# 🌱 Seed Data - Datos Iniciales del Sistema

Este comando de Django pobla la base de datos con datos realistas y completos para pruebas inmediatas del planificador de horarios.

---

## 📋 Requisitos Previos

- Django 5.0.4+ instalado
- Base de datos configurada (SQLite o PostgreSQL)
- Migraciones aplicadas: `python manage.py migrate`

---

## 🚀 Uso

### Crear datos iniciales (idempotente)
```bash
python manage.py seed_data
```

Este comando puede ejecutarse múltiples veces sin duplicar datos.

### Limpiar y recrear todo
```bash
python manage.py seed_data --clear
```

Elimina todos los datos existentes (excepto usuarios admin si existen) y crea nuevos.

---

## 📊 Datos Creados

### 1. Usuarios de Prueba
| Usuario | Email | Contraseña | Rol | Grupo |
|---------|-------|------------|-----|-------|
| `vicedecano` | vicedecano@uci.cu | Admin1234 | VICEDECANO | - |
| `planificador` | planificador@uci.cu | Plan1234 | PLANIFICADOR | - |
| `estudiante` | estudiante@uci.cu | Estud1234 | CONSULTA | G1 (1er año) |

### 2. Años Académicos
- **1er año** - Turno Mañana
- **2do año** - Turno Tarde
- **3er año** - Turno Mañana
- **4to año** - Turno Tarde

### 3. Grupos
| Año | Cantidad | Alumnos/grupo |
|-----|----------|---------------|
| 1er | 5 grupos (G1-G5) | 30 |
| 2do | 5 grupos (G1-G5) | 30 |
| 3er | 4 grupos (G1-G4) | 25 |
| 4to | 4 grupos (G1-G4) | 25 |

**Total: 18 grupos**

### 4. Locales (14 totales)
- **8 Aulas**: A201-A208 (capacidad 35)
- **2 Salones**: S401-S402 (capacidad 150)
- **3 Laboratorios**: LAB1-LAB3 (capacidad 30)
- **1 Polideportivo**: POLI (capacidad 100)

### 5. Franjas Horarias
**Turno Mañana** (8 franjas):
- 8:00 - 9:20
- 9:30 - 10:50
- 11:00 - 12:20
- 12:30 - 13:50

**Turno Tarde** (8 franjas):
- 12:00 - 13:20
- 13:30 - 14:50
- 15:00 - 16:20
- 16:30 - 17:50

### 6. Profesores (19)
Juan Pérez, María García, Carlos López, Ana Martínez, Luis Rodríguez, Carmen Sánchez, Pedro Ramírez, Laura Torres, Miguel Castro, Sofía Flores, José Ortiz, Isabel Ruiz, Francisco Morales, Patricia Vega, Antonio Herrera, Elena Domínguez, Ricardo Cruz, Marta Reyes, Fernando Aguilar.

### 7. Asignaturas (30 totales)

**1er año (7):**
- Filosofía (FILO)
- Álgebra (ALG)
- Matemática Discreta I (MD1)
- Introducción a la Programación I (IP1)
- Educación Física I (EF1)
- Seguridad Nacional (SN)
- Introducción a las Ciencias Informáticas I (ICI1)

**2do año (7):**
- Economía Política (EP)
- Matemática II (MAT2)
- Estructura de Datos I (ED1)
- Física (FIS)
- Educación Física III (EF3)
- Fundamentos de Gestión de Organizaciones (FGO)
- Proyecto de Investigación y Desarrollo I (PID1)

**3er año (8):**
- Teoría Política (TP)
- Probabilidades y Estadística (PE)
- Sistema de Base de Datos II (SBD2)
- Ingeniería de Software I (IS1)
- Metodología de la Investigación Científica (MIC)
- Sistema Operativo (SO)
- Proyecto de Investigación y Desarrollo II (PID2)
- Proyecto de Investigación y Desarrollo III (PID3)

**4to año (8):**
- Investigación de Operaciones (IO)
- Inteligencia Artificial (IA)
- Ingeniería de Software II (IS2)
- Redes y Seguridad Informática I (RSI1)
- Proyecto de Investigación y Desarrollo IV (PID4)
- Programación Web (PW)
- Optativa I (OPT1)
- Optativa II (OPT2)

### 8. Asignaciones Profesor (44+)
Cada asignatura tiene 1-2 profesores asignados. Las asignaturas tipo conferencia (Álgebra, Filosofía, etc.) se asignan sin grupo específico.

---

## ✅ Checklist para Generar Horario

Después de ejecutar `seed_data`, sigue estos pasos para generar un horario de prueba:

### Paso 1: Iniciar sesión
1. Ir a `http://127.0.0.1:8000/`
2. Iniciar sesión con:
   - **Vicedecano**: `vicedecano` / `Admin1234`
   - **Planificador**: `planificador` / `Plan1234`

### Paso 2: Preparar datos de planificación
1. **Asignar aulas a grupos** (opcional pero recomendado):
   - Ir a "Asignaciones Aula-Grupo"
   - Asignar aulas a cada grupo (ej: G1→A201, G2→A202, etc.)

2. **Verificar asignaciones de profesores**:
   - Ir a "Asignaciones Profesor"
   - Confirmar que cada asignatura tiene profesor asignado

### Paso 3: Importar balance de carga
1. Ir a "Importar Balance"
2. Seleccionar el **1er año** (Mañana)
3. Crear actividades de prueba para cada asignatura:
   - Tipo: Conferencia (C), Clase Práctica (CP), Laboratorio (L), Taller (T)
   - Semanas: 1-16
   - Franjas: asignar según disponibilidad

### Paso 4: Generar horario
1. Ir a "Generar Horario"
2. Seleccionar:
   - **Año**: 1er año
   - **Semana**: 1
   - **Turno**: Mañana
3. Click en "Generar Horario"
4. El sistema usará OR-Tools para optimizar asignaciones

### Paso 5: Verificar horario generado
1. Ir a "Horarios" → "Vista General"
2. Verificar que:
   - ✅ No hay conflictos de profesor
   - ✅ No hay conflictos de grupo
   - ✅ No hay conflictos de aula
   - ✅ Las actividades están distribuidas en las franjas disponibles

### Paso 6: Exportar o ajustar
- Exportar a Excel si es necesario
- Ajustar manualmente actividades con conflictos (si los hay)

---

## 🔧 Solución de Problemas

### Error: "No module named 'academico'"
Asegúrate de estar en el directorio raíz del proyecto donde está `manage.py`.

### Error: "table does not exist"
Ejecuta las migraciones primero:
```bash
python manage.py migrate
```

### Datos duplicados
El comando usa `get_or_create` para evitar duplicados. Si ves duplicados:
```bash
python manage.py seed_data --clear
```

---

## 📝 Notas para Desarrolladores

### Estructura del comando
```
academico/
└── management/
    └── commands/
        └── seed_data.py
```

### Idempotencia
Cada modelo usa `get_or_create()` con campos únicos:
- `Usuario`: `username`
- `AnioAcademico`: `numero`
- `Grupo`: `nombre` + `anio`
- `Local`: `codigo`
- `FranjaHoraria`: `turno` + `orden`
- `Profesor`: `nombre`
- `Asignatura`: `nombre` + `anio`
- `AsignacionProfesor`: `profesor` + `asignatura`

### Extender el comando
Para agregar más datos, edita el archivo `seed_data.py` y añade:
1. Nuevos métodos `crear_XXX()`
2. Llámalo desde `handle()` en el orden correcto de dependencias

---

## 🎯 Ejemplo de Flujo Completo

```bash
# 1. Migrar base de datos
python manage.py migrate

# 2. Crear datos iniciales
python manage.py seed_data

# 3. Iniciar servidor
python manage.py runserver

# 4. Abrir navegador en http://127.0.0.1:8000/
# 5. Iniciar sesión como vicedecano / Admin1234
# 6. Ir a Importar Balance → seleccionar 1er año
# 7. Generar horario para semana 1
```

---

## 📞 Soporte

Si encuentras problemas, verifica:
1. Estás usando Python 3.11+
2. Django 5.0.4+ está instalado
3. Las dependencias de `requirements.txt` están instaladas
4. La base de datos está accesible
