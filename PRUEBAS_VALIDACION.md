# Guía de Pruebas Manuales - Validaciones de Formularios

## 1. Formulario de Usuario (Crear/Editar)

### 1.1 Validación de Email

| Escenario | Datos de entrada | Resultado esperado |
|-----------|------------------|-------------------|
| Email válido @gmail.com | `usuario@gmail.com` | ✅ Aceptado |
| Email válido @uci.cu | `estudiante@uci.cu` | ✅ Aceptado |
| Email dominio no permitido | `test@yahoo.com` | ❌ "Solo se permiten correos de los dominios @gmail.com o @uci.cu" |
| Email vacío | `` | ❌ "El correo electrónico es obligatorio" |
| Email duplicado | Email existente en BD | ❌ "Ya existe un usuario con este correo" |
| Email inválido formato | `correo-sin-arroba` | ❌ "Ingrese un correo electrónico válido" |

### 1.2 Validación de Username

| Escenario | Datos de entrada | Resultado esperado |
|-----------|------------------|-------------------|
| Username vacío (auto-generado) | `` + Nombre: "Carlos" | ✅ Genera: `Carlos45` |
| Username manual válido | `carlos_martinez` | ✅ Aceptado |
| Username duplicado | Username existente | ❌ "Este nombre de usuario ya está en uso" |
| Username caracteres inválidos | `carlos@123` | ❌ "Solo puede contener letras, números y los caracteres @, ., +, -, _" |
| Username muy largo | 151 caracteres | ❌ "No puede tener más de 150 caracteres" |

### 1.3 Validación de Contraseña

| Escenario | Datos de entrada | Resultado esperado |
|-----------|------------------|-------------------|
| Password vacío (auto-generado) | `` + Nombre: "Maria" | ✅ Genera: `mar123456` |
| Password manual válida | `Segura123!` | ✅ Aceptada (8+ chars, no común) |
| Password muy corta | `abc123` | ❌ "La contraseña debe tener al menos 8 caracteres" |
| Password solo numérica | `12345678` | ❌ "La contraseña no puede ser completamente numérica" |
| Password común | `password123` | ❌ "La contraseña es demasiado común" |
| Passwords no coinciden | `Pass1234` vs `Pass1235` | ❌ "Las contraseñas no coinciden" |

### 1.4 Validación de Nombre y Apellidos

| Escenario | Datos de entrada | Resultado esperado |
|-----------|------------------|-------------------|
| Nombre válido | `José María` | ✅ Aceptado |
| Nombre con apóstrofe | `O'Connor` | ✅ Aceptado |
| Nombre con números | `Juan123` | ❌ "Solo puede contener letras, espacios y apóstrofes" |
| Nombre corto | `A` | ❌ "Debe tener al menos 3 caracteres" |
| Nombre vacío | `` | ❌ "El nombre es obligatorio" |
| Apellido válido | `García López` | ✅ Aceptado |

### 1.5 Validación de Rol

| Escenario | Datos de entrada | Resultado esperado |
|-----------|------------------|-------------------|
| Rol PLANIFICADOR | `PLANIFICADOR` | ✅ Aceptado |
| Rol CONSULTA | `CONSULTA` | ✅ Aceptado |
| Rol VICEDECANO (crear) | `VICEDECANO` | ❌ "No se puede crear otro Vicedecano" |
| Rol VICEDECANO (editar otro) | `VICEDECANO` en usuario normal | ❌ "No se puede asignar el rol Vicedecano" |
| Rol vacío | `` | ❌ "El rol es obligatorio" |

---

## 2. Formularios Académicos

### 2.1 Formulario Grupo

| Escenario | Datos de entrada | Resultado esperado |
|-----------|------------------|-------------------|
| Nombre válido | `1.1` | ✅ Aceptado |
| Nombre con espacios | `Grupo A` | ✅ Aceptado |
| Nombre caracteres inválidos | `Grupo@#$` | ❌ "Solo puede contener letras, números, espacios, puntos y guiones" |
| Cantidad alumnos válida | `25` | ✅ Aceptado |
| Cantidad cero | `0` | ❌ "Debe haber al menos 1 alumno" |
| Cantidad excesiva | `100` | ❌ "No puede haber más de 50 alumnos" |

### 2.2 Formulario Local

| Escenario | Datos de entrada | Resultado esperado |
|-----------|------------------|-------------------|
| Código válido | `A-101` | ✅ Aceptado |
| Código minúsculas | `a-101` | ✅ Convertido a `A-101` |
| Código caracteres inválidos | `A@101` | ❌ "Solo puede contener letras mayúsculas, números y guiones" |
| Capacidad válida | `30` | ✅ Aceptado |
| Capacidad cero | `0` | ❌ "La capacidad mínima es 1" |
| Capacidad excesiva | `500` | ❌ "La capacidad máxima es 200" |

### 2.3 Formulario Franja Horaria

| Escenario | Datos de entrada | Resultado esperado |
|-----------|------------------|-------------------|
| Horas válidas | 08:00 - 09:30 | ✅ Aceptado |
| Hora fin = hora inicio | 08:00 - 08:00 | ❌ "La hora de fin debe ser posterior a la hora de inicio" |
| Hora fin < hora inicio | 09:00 - 08:00 | ❌ "La hora de fin debe ser posterior a la hora de inicio" |
| Solapamiento | Franja existente 08:00-09:30, nueva 08:30-10:00 | ❌ "Se solapa con la existente" |

### 2.4 Formulario Asignatura

| Escenario | Datos de entrada | Resultado esperado |
|-----------|------------------|-------------------|
| Nombre válido | `Matemática Superior` | ✅ Aceptado |
| Abreviatura válida | `MAT` | ✅ Aceptado |
| Abreviatura minúsculas | `mat` | ✅ Convertido a `MAT` |
| Abreviatura muy corta | `M` | ❌ "Debe tener al menos 2 caracteres" |
| Abreviatura caracteres inválidos | `MAT-01` | ❌ "Solo puede contener letras mayúsculas y números" |

### 2.5 Formulario Asignación Profesor

| Escenario | Datos de entrada | Resultado esperado |
|-----------|------------------|-------------------|
| Tipo actividad válido | `C`, `CP`, `L`, etc. | ✅ Aceptado |
| Tipo actividad inválido | `XYZ` | ❌ "Tipo de actividad no válido" |
| Tipo actividad vacío | `` | ❌ "El tipo de actividad es obligatorio" |
| Sin profesor | `` | ❌ "Este campo es obligatorio" |
| Sin asignatura | `` | ❌ "Este campo es obligatorio" |

---

## 3. Ejecución de Pruebas

### Comando para probar formulario de usuario:
```bash
# Iniciar shell de Django
python manage.py shell

# Probar validaciones
from usuarios.forms import UsuarioCreationForm

# Test 1: Email dominio inválido
form = UsuarioCreationForm(data={
    'first_name': 'Juan',
    'last_name': 'Pérez',
    'email': 'test@yahoo.com',
    'rol': 'PLANIFICADOR'
})
print(form.is_valid())  # False
print(form.errors['email'])  # ['Solo se permiten correos...']

# Test 2: Generación automática
form = UsuarioCreationForm(data={
    'first_name': 'Maria',
    'last_name': 'García',
    'email': 'maria@gmail.com',
    'rol': 'PLANIFICADOR'
    # username y password vacíos -> auto-generados
})
print(form.is_valid())  # True
user = form.save()
print(user.username)  # Ej: Maria87
print(form.cleaned_data['password1'])  # mar123456
```

### Pruebas de integración (vista web):
1. Acceder como Vicedecano a `/usuarios/crear/`
2. Dejar username vacío, llenar nombre y email válido
3. Verificar mensaje de éxito con username generado
4. Probar email inválido y verificar error en rojo
5. Probar password débil y verificar mensaje de validador

---

## 4. Lista de Verificación (Checklist)

- [ ] Email con @gmail.com es aceptado
- [ ] Email con @uci.cu es aceptado
- [ ] Email con @yahoo.com es rechazado
- [ ] Email duplicado muestra error
- [ ] Username vacío genera automáticamente
- [ ] Username duplicado muestra error
- [ ] Password vacía genera automáticamente
- [ ] Password corta (< 8 chars) es rechazada
- [ ] Password solo numérica es rechazada
- [ ] Nombre con números es rechazado
- [ ] Rol VICEDECANO no puede crearse
- [ ] Campos requeridos muestran asterisco (*)
- [ ] Errores aparecen en español
- [ ] Errores tienen estilo Bootstrap (rojo)
- [ ] Franjas horarias solapadas son rechazadas
- [ ] Capacidad de local fuera de rango es rechazada
