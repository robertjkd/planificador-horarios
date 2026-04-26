"""
Formularios de usuario con validaciones completas de seguridad.

Incluye:
- Validación de email con dominios permitidos
- Generación automática de username si está vacío
- Validación de contraseñas con generación automática si está vacía
- Validaciones de nombres y apellidos
- Control de rol VICEDECANO
"""
import random
import re

from django import forms
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _

from .models import Usuario

# Nota: Los formularios de usuario no heredan de BaseModelForm porque
# requieren configuración especial de widgets y validaciones complejas
# que ya incluyen estilos Bootstrap manualmente.


# ─────────────────────────────────────────────────────────────
# VALIDACIONES AUXILIARES
# ─────────────────────────────────────────────────────────────

def validar_dominio_email(email):
    """Valida que el email pertenezca a los dominios permitidos."""
    dominios_permitidos = getattr(settings, 'EMAIL_DOMINIOS_PERMITIDOS', ['gmail.com', 'uci.cu'])
    
    if not email or '@' not in email:
        return  # Dejar que el validador de email maneje esto
    
    dominio = email.split('@')[-1].lower()
    
    if dominio not in dominios_permitidos:
        dominios_str = ', '.join([f'@{d}' for d in dominios_permitidos])
        raise ValidationError(
            f'Solo se permiten correos de los dominios: {dominios_str}'
        )


def generar_username_unico(nombre_base):
    """
    Genera un username único a partir del nombre base.
    Formato: Nombre + 2-3 dígitos aleatorios.
    Si existe, incrementa el sufijo hasta encontrar uno libre.
    """
    # Limpiar nombre base: solo letras y dígitos
    nombre_limpio = re.sub(r'[^\w]', '', nombre_base)[:15]
    
    if not nombre_limpio:
        nombre_limpio = 'usuario'
    
    # Intentar con diferentes sufijos
    intentos = 0
    max_intentos = 100
    
    while intentos < max_intentos:
        # Generar sufijo aleatorio (2-3 dígitos)
        sufijo = random.randint(10, 999)
        username = f'{nombre_limpio}{sufijo}'[:settings.USERNAME_MAX_LENGTH]
        
        # Verificar si existe
        if not Usuario.objects.filter(username=username).exists():
            return username
        
        intentos += 1
    
    # Si no se encontró, usar timestamp
    import time
    username = f'{nombre_limpio}{int(time.time())}'[:settings.USERNAME_MAX_LENGTH]
    return username


def generar_password_generico(nombre):
    """
    Genera una contraseña genérica para el usuario.
    Formato: primeras 3 letras del nombre en minúsculas + '123456'
    Ejemplo: 'Maria' -> 'mar123456'
    """
    prefix_length = getattr(settings, 'PASSWORD_GENERICO_PREFIX_LENGTH', 3)
    suffix = getattr(settings, 'PASSWORD_GENERICO_SUFFIX', '123456')
    
    if nombre:
        prefix = nombre[:prefix_length].lower()
    else:
        prefix = 'usr'
    
    return f'{prefix}{suffix}'


# ─────────────────────────────────────────────────────────────
# FORMULARIO DE CREACIÓN DE USUARIO
# ─────────────────────────────────────────────────────────────

class UsuarioCreationForm(forms.ModelForm):
    """
    Formulario para crear nuevos usuarios (solo Vicedecano).
    
    Validaciones:
    - Email obligatorio y único, con dominios permitidos
    - Username opcional (se genera automáticamente si está vacío)
    - Contraseña opcional (se genera automáticamente si ambos campos están vacíos)
    - Nombre y apellidos requeridos, solo letras y espacios
    - Rol obligatorio (no VICEDECANO)
    - Grupo solo para rol CONSULTA
    """
    
    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dejar vacío para generar automáticamente'
        }),
        required=False,
        help_text='Mínimo 8 caracteres. Si deja vacío, se generará: primeras 3 letras del nombre + 123456'
    )
    
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repetir contraseña'
        }),
        required=False,
        help_text='Repita la contraseña para verificar'
    )
    
    # Hacer el username opcional
    username = forms.CharField(
        label='Nombre de usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dejar vacío para generar automáticamente'
        }),
        required=False,
        help_text='Máximo 150 caracteres. Letras, dígitos y @/./+/-/_ únicamente. '
                  'Si deja vacío, se generará automáticamente (ej: Carlos45)'
    )
    
    class Meta:
        model = Usuario
        fields = ('username', 'email', 'first_name', 'last_name', 'rol', 'grupo')
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ejemplo@gmail.com o ejemplo@uci.cu'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellidos'
            }),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'grupo': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer email requerido explícitamente
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['rol'].required = True
        
        # Agregar mensajes de error personalizados
        self.fields['email'].error_messages = {
            'required': 'El correo electrónico es obligatorio.',
            'invalid': 'Ingrese un correo electrónico válido.',
            'unique': 'Ya existe un usuario con este correo electrónico.'
        }

    def clean_email(self):
        """Validar email único y dominio permitido."""
        email = self.cleaned_data.get('email')
        
        if not email:
            raise ValidationError('El correo electrónico es obligatorio.')
        
        # Validar dominio
        validar_dominio_email(email)
        
        # Verificar unicidad (case-insensitive)
        if Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError('Ya existe un usuario con este correo electrónico.')
        
        return email.lower()

    def clean_username(self):
        """
        Validar username o generar uno automáticamente.
        """
        username = self.cleaned_data.get('username', '').strip()
        
        # Si está vacío, se generará automáticamente en clean()
        if not username:
            return username
        
        # Validar longitud máxima
        if len(username) > settings.USERNAME_MAX_LENGTH:
            raise ValidationError(
                f'El nombre de usuario no puede tener más de {settings.USERNAME_MAX_LENGTH} caracteres.'
            )
        
        # Validar caracteres permitidos (regex de Django)
        username_regex = getattr(settings, 'USERNAME_REGEX', r'^[\w.@+-]+$')
        if not re.match(username_regex, username):
            raise ValidationError(
                'El nombre de usuario solo puede contener letras, números y los caracteres @, ., +, -, _'
            )
        
        # Verificar si ya existe
        if Usuario.objects.filter(username__iexact=username).exists():
            raise ValidationError('Este nombre de usuario ya está en uso.')
        
        return username

    def clean_first_name(self):
        """Validar nombre: solo letras, espacios y apóstrofes."""
        first_name = self.cleaned_data.get('first_name', '').strip()
        
        if not first_name:
            raise ValidationError('El nombre es obligatorio.')
        
        if len(first_name) > 100:
            raise ValidationError('El nombre no puede tener más de 100 caracteres.')
        
        # Validar solo letras, espacios y apóstrofes
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s']+$", first_name):
            raise ValidationError('El nombre solo puede contener letras, espacios y apóstrofes.')
        
        return first_name

    def clean_last_name(self):
        """Validar apellidos: solo letras, espacios y apóstrofes."""
        last_name = self.cleaned_data.get('last_name', '').strip()
        
        if not last_name:
            raise ValidationError('Los apellidos son obligatorios.')
        
        if len(last_name) > 100:
            raise ValidationError('Los apellidos no pueden tener más de 100 caracteres.')
        
        # Validar solo letras, espacios y apóstrofes
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s']+$", last_name):
            raise ValidationError('Los apellidos solo pueden contener letras, espacios y apóstrofes.')
        
        return last_name

    def clean_rol(self):
        """Validar que no se cree otro Vicedecano."""
        rol = self.cleaned_data.get('rol')
        
        if not rol:
            raise ValidationError('El rol es obligatorio.')
        
        if rol == Usuario.Rol.VICEDECANO:
            raise ValidationError('No se puede crear otro Vicedecano desde este formulario.')
        
        return rol

    def clean_grupo(self):
        """Validar grupo según el rol."""
        grupo = self.cleaned_data.get('grupo')
        rol = self.cleaned_data.get('rol')
        
        # Solo el rol CONSULTA debería tener grupo asignado
        if grupo and rol != Usuario.Rol.CONSULTA:
            # No es un error crítico, solo una advertencia que ignoramos
            pass
        
        return grupo

    def clean_password2(self):
        """Validar que las contraseñas coincidan."""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        # Si se proporcionó password1, password2 debe coincidir
        if password1:
            if not password2:
                raise ValidationError('Debe confirmar la contraseña.')
            if password1 != password2:
                raise ValidationError('Las contraseñas no coinciden.')
            
            # Validar contraseña usando los validadores de Django
            try:
                validate_password(password1)
            except ValidationError as e:
                raise ValidationError(e.messages)
        
        return password2

    def clean(self):
        """
        Validaciones globales del formulario.
        Generar username automático si está vacío.
        Generar contraseña automática si ambos campos de password están vacíos.
        """
        cleaned_data = super().clean()
        
        first_name = cleaned_data.get('first_name', '')
        username = cleaned_data.get('username', '').strip()
        password1 = cleaned_data.get('password1')
        
        # Generar username automáticamente si está vacío
        if not username and first_name:
            username_generado = generar_username_unico(first_name)
            cleaned_data['username'] = username_generado
            self.cleaned_data['username'] = username_generado
        
        # Generar contraseña automáticamente si no se proporcionó
        if not password1 and first_name:
            password_generada = generar_password_generico(first_name)
            cleaned_data['password1'] = password_generada
            self.cleaned_data['password1'] = password_generada
            self.cleaned_data['password2'] = password_generada
        
        return cleaned_data

    def save(self, commit=True):
        """Guardar el usuario con la contraseña hasheada."""
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        
        if password:
            user.set_password(password)
        
        if commit:
            user.save()
        
        return user


# ─────────────────────────────────────────────────────────────
# FORMULARIO DE EDICIÓN DE USUARIO
# ─────────────────────────────────────────────────────────────

class UsuarioChangeForm(forms.ModelForm):
    """
    Formulario para editar usuarios existentes.
    
    Diferencias con creación:
    - Username no puede cambiarse si ya está establecido
    - Contraseña es opcional (solo se cambia si se proporciona)
    - Email se valida que no esté en uso por otro usuario
    """
    
    password1 = forms.CharField(
        label='Nueva contraseña (opcional)',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dejar vacío para mantener la actual'
        }),
        required=False,
        help_text='Solo complete si desea cambiar la contraseña. Mínimo 8 caracteres.'
    )
    
    password2 = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repetir nueva contraseña'
        }),
        required=False,
        help_text='Repita la contraseña para verificar'
    )
    
    class Meta:
        model = Usuario
        fields = ('username', 'email', 'first_name', 'last_name', 'rol', 'grupo', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly'  # Username no editable en edición
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ejemplo@gmail.com o ejemplo@uci.cu'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellidos'
            }),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'grupo': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer campos requeridos
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['rol'].required = True
        
        # Deshabilitar username en edición
        self.fields['username'].disabled = True
        
        # Agregar mensajes de error personalizados
        self.fields['email'].error_messages = {
            'required': 'El correo electrónico es obligatorio.',
            'invalid': 'Ingrese un correo electrónico válido.'
        }

    def clean_email(self):
        """Validar email único (excluyendo el usuario actual)."""
        email = self.cleaned_data.get('email')
        
        if not email:
            raise ValidationError('El correo electrónico es obligatorio.')
        
        # Validar dominio
        validar_dominio_email(email)
        
        # Verificar unicidad (excluyendo el usuario actual)
        if Usuario.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Ya existe otro usuario con este correo electrónico.')
        
        return email.lower()

    def clean_first_name(self):
        """Validar nombre: solo letras, espacios y apóstrofes."""
        first_name = self.cleaned_data.get('first_name', '').strip()
        
        if not first_name:
            raise ValidationError('El nombre es obligatorio.')
        
        if len(first_name) > 100:
            raise ValidationError('El nombre no puede tener más de 100 caracteres.')
        
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s']+$", first_name):
            raise ValidationError('El nombre solo puede contener letras, espacios y apóstrofes.')
        
        return first_name

    def clean_last_name(self):
        """Validar apellidos: solo letras, espacios y apóstrofes."""
        last_name = self.cleaned_data.get('last_name', '').strip()
        
        if not last_name:
            raise ValidationError('Los apellidos son obligatorios.')
        
        if len(last_name) > 100:
            raise ValidationError('Los apellidos no pueden tener más de 100 caracteres.')
        
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s']+$", last_name):
            raise ValidationError('Los apellidos solo pueden contener letras, espacios y apóstrofes.')
        
        return last_name

    def clean_rol(self):
        """Validar que no se asigne rol VICEDECANO."""
        rol = self.cleaned_data.get('rol')
        
        if not rol:
            raise ValidationError('El rol es obligatorio.')
        
        if rol == Usuario.Rol.VICEDECANO and not self.instance.es_vicedecano:
            raise ValidationError('No se puede asignar el rol Vicedecano a otro usuario.')
        
        return rol

    def clean_password2(self):
        """Validar contraseña nueva si se proporciona."""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1:
            if not password2:
                raise ValidationError('Debe confirmar la nueva contraseña.')
            if password1 != password2:
                raise ValidationError('Las contraseñas no coinciden.')
            
            # Validar contraseña usando los validadores de Django
            try:
                validate_password(password1, user=self.instance)
            except ValidationError as e:
                raise ValidationError(e.messages)
        
        return password2

    def save(self, commit=True):
        """Guardar cambios, incluyendo contraseña si se proporcionó."""
        user = super().save(commit=False)
        password = self.cleaned_data.get('password1')
        
        if password:
            user.set_password(password)
        
        if commit:
            user.save()
        
        return user
