import re

from django import forms
from django.core.exceptions import ValidationError

from .models import (
    AnioAcademico,
    Grupo,
    Profesor,
    Local,
    FranjaHoraria,
    Asignatura,
    AsignacionProfesor,
    AsignacionAulaGrupo,
)
from .forms_base import BaseModelForm


class AnioAcademicoForm(BaseModelForm):
    """Formulario para crear/editar años académicos."""
    
    class Meta:
        model = AnioAcademico
        fields = ['numero', 'turno']
        widgets = {
            'numero': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'placeholder': 'Ej: 1, 2, 3, 4'
            }),
            'turno': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['numero'].error_messages = {
            'required': 'El número de año es obligatorio.',
            'invalid': 'Ingrese un número válido.',
            'min_value': 'El año debe ser al menos 1.',
            'max_value': 'El año no puede ser mayor que 10.',
        }


class GrupoForm(BaseModelForm):
    """Formulario para crear/editar grupos con validaciones."""
    
    class Meta:
        model = Grupo
        fields = ['nombre', 'anio', 'cantidad_alumnos']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1.1, 2.A, etc.'
            }),
            'anio': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_alumnos': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 50,
                'placeholder': 'Cantidad de estudiantes'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].required = True
        self.fields['cantidad_alumnos'].required = True
        self.fields['nombre'].error_messages = {
            'required': 'El nombre del grupo es obligatorio.',
        }
        self.fields['cantidad_alumnos'].error_messages = {
            'required': 'La cantidad de alumnos es obligatoria.',
            'min_value': 'Debe haber al menos 1 alumno.',
            'max_value': 'No puede haber más de 50 alumnos.',
        }

    def clean_nombre(self):
        """Validar que el nombre solo contenga caracteres permitidos."""
        nombre = self.cleaned_data.get('nombre', '').strip()
        
        if not nombre:
            raise ValidationError('El nombre del grupo es obligatorio.')
        
        if len(nombre) > 20:
            raise ValidationError('El nombre no puede tener más de 20 caracteres.')
        
        # Permitir letras, números, espacios, puntos y guiones
        if not re.match(r"^[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ\s\.\-]+$", nombre):
            raise ValidationError('El nombre solo puede contener letras, números, espacios, puntos y guiones.')
        
        return nombre

    def clean_cantidad_alumnos(self):
        """Validar rango de cantidad de alumnos."""
        cantidad = self.cleaned_data.get('cantidad_alumnos')
        
        if cantidad is None:
            raise ValidationError('La cantidad de alumnos es obligatoria.')
        
        if cantidad < 1:
            raise ValidationError('Debe haber al menos 1 alumno.')
        
        if cantidad > 50:
            raise ValidationError('No puede haber más de 50 alumnos.')
        
        return cantidad


class ProfesorForm(BaseModelForm):
    """Formulario para crear/editar profesores."""
    
    class Meta:
        model = Profesor
        fields = ['nombre', 'usuario']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo del profesor'
            }),
            'usuario': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].required = True
        self.fields['nombre'].error_messages = {
            'required': 'El nombre del profesor es obligatorio.',
        }

    def clean_nombre(self):
        """Validar que el nombre solo contenga letras, espacios y apóstrofes."""
        nombre = self.cleaned_data.get('nombre', '').strip()
        
        if not nombre:
            raise ValidationError('El nombre del profesor es obligatorio.')
        
        if len(nombre) > 100:
            raise ValidationError('El nombre no puede tener más de 100 caracteres.')
        
        if len(nombre) < 3:
            raise ValidationError('El nombre debe tener al menos 3 caracteres.')
        
        # Solo letras, espacios y apóstrofes
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s']+$", nombre):
            raise ValidationError('El nombre solo puede contener letras, espacios y apóstrofes.')
        
        return nombre


class LocalForm(BaseModelForm):
    """Formulario para crear/editar locales con validaciones."""
    
    class Meta:
        model = Local
        fields = ['codigo', 'nombre', 'tipo', 'capacidad']
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: A-101, LAB-01'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre descriptivo'
            }),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'capacidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 200,
                'placeholder': 'Capacidad máxima'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['codigo'].required = True
        self.fields['nombre'].required = True
        self.fields['capacidad'].required = True
        
        self.fields['codigo'].error_messages = {
            'required': 'El código del local es obligatorio.',
            'unique': 'Ya existe un local con este código.',
        }
        self.fields['capacidad'].error_messages = {
            'required': 'La capacidad es obligatoria.',
            'min_value': 'La capacidad mínima es 1.',
            'max_value': 'La capacidad máxima es 200.',
        }

    def clean_codigo(self):
        """Validar formato del código."""
        codigo = self.cleaned_data.get('codigo', '').strip().upper()
        
        if not codigo:
            raise ValidationError('El código del local es obligatorio.')
        
        if len(codigo) > 20:
            raise ValidationError('El código no puede tener más de 20 caracteres.')
        
        # Permitir letras, números, guiones y espacios
        if not re.match(r"^[A-Z0-9\-\s]+$", codigo):
            raise ValidationError('El código solo puede contener letras mayúsculas, números y guiones.')
        
        return codigo

    def clean_nombre(self):
        """Validar nombre del local."""
        nombre = self.cleaned_data.get('nombre', '').strip()
        
        if not nombre:
            raise ValidationError('El nombre del local es obligatorio.')
        
        if len(nombre) > 100:
            raise ValidationError('El nombre no puede tener más de 100 caracteres.')
        
        return nombre

    def clean_capacidad(self):
        """Validar rango de capacidad."""
        capacidad = self.cleaned_data.get('capacidad')
        
        if capacidad is None:
            raise ValidationError('La capacidad es obligatoria.')
        
        if capacidad < 1:
            raise ValidationError('La capacidad mínima es 1.')
        
        if capacidad > 200:
            raise ValidationError('La capacidad máxima es 200.')
        
        return capacidad


class FranjaHorariaForm(BaseModelForm):
    class Meta:
        model = FranjaHoraria
        fields = ['turno', 'orden', 'hora_inicio', 'hora_fin']
        widgets = {
            'turno': forms.Select(attrs={'class': 'form-select'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        turno = cleaned_data.get('turno')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        instance = self.instance

        # Validar que hora_fin > hora_inicio
        if hora_inicio and hora_fin:
            if hora_fin <= hora_inicio:
                raise forms.ValidationError(
                    'La hora de fin debe ser posterior a la hora de inicio.'
                )

        # Validar solapamiento con otras franjas del mismo turno
        if turno and hora_inicio and hora_fin:
            from django.db.models import Q
            solapadas = FranjaHoraria.objects.filter(turno=turno)
            
            # Excluir la instancia actual en caso de edición
            if instance.pk:
                solapadas = solapadas.exclude(pk=instance.pk)
            
            # Buscar franjas que se solapen - Su hora_inicio está entre hora_inicio y hora_fin de la nueva
           
            solapadas = solapadas.filter(
                Q(hora_inicio__lt=hora_fin, hora_fin__gt=hora_inicio)
            )
            
            if solapadas.exists():
                franja_conflictiva = solapadas.first()
                raise forms.ValidationError(
                    f'Esta franja horaria se solapa con la existente: '
                    f'{franja_conflictiva} ({franja_conflictiva.hora_inicio:%H:%M}-{franja_conflictiva.hora_fin:%H:%M}). '
                    f'No pueden existir franjas superpuestas en el mismo turno.'
                )

        return cleaned_data


class AsignaturaForm(BaseModelForm):
    """Formulario para crear/editar asignaturas con validaciones."""
    
    class Meta:
        model = Asignatura
        fields = ['nombre', 'abreviatura', 'anio']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo de la asignatura'
            }),
            'abreviatura': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: MAT, FIS, etc. (máx 10 chars)'
            }),
            'anio': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].required = True
        self.fields['abreviatura'].required = True
        self.fields['anio'].required = True
        
        self.fields['nombre'].error_messages = {
            'required': 'El nombre de la asignatura es obligatorio.',
        }
        self.fields['abreviatura'].error_messages = {
            'required': 'La abreviatura es obligatoria.',
        }

    def clean_nombre(self):
        """Validar nombre de asignatura."""
        nombre = self.cleaned_data.get('nombre', '').strip()
        
        if not nombre:
            raise ValidationError('El nombre de la asignatura es obligatorio.')
        
        if len(nombre) > 100:
            raise ValidationError('El nombre no puede tener más de 100 caracteres.')
        
        if len(nombre) < 3:
            raise ValidationError('El nombre debe tener al menos 3 caracteres.')
        
        return nombre

    def clean_abreviatura(self):
        """Validar abreviatura (solo letras mayúsculas, máx 10 chars)."""
        abrev = self.cleaned_data.get('abreviatura', '').strip().upper()
        
        if not abrev:
            raise ValidationError('La abreviatura es obligatoria.')
        
        if len(abrev) > 10:
            raise ValidationError('La abreviatura no puede tener más de 10 caracteres.')
        
        if len(abrev) < 2:
            raise ValidationError('La abreviatura debe tener al menos 2 caracteres.')
        
        # Solo letras mayúsculas y números
        if not re.match(r'^[A-Z0-9]+$', abrev):
            raise ValidationError('La abreviatura solo puede contener letras mayúsculas y números.')
        
        return abrev


class AsignacionProfesorForm(BaseModelForm):
    """Formulario para asignar profesores a asignaturas/grupos con validación de tipo."""
    
    class Meta:
        model = AsignacionProfesor
        fields = ['profesor', 'asignatura', 'grupo', 'tipo_actividad']
        widgets = {
            'profesor': forms.Select(attrs={'class': 'form-select'}),
            'asignatura': forms.Select(attrs={'class': 'form-select'}),
            'grupo': forms.Select(attrs={'class': 'form-select'}),
            'tipo_actividad': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profesor'].required = True
        self.fields['asignatura'].required = True
        self.fields['tipo_actividad'].required = True
        
        self.fields['tipo_actividad'].error_messages = {
            'required': 'El tipo de actividad es obligatorio.',
            'invalid_choice': 'Seleccione un tipo de actividad válido.',
        }

    def clean_tipo_actividad(self):
        """Validar que el tipo de actividad esté en las opciones permitidas."""
        from .models import TipoActividad
        
        tipo = self.cleaned_data.get('tipo_actividad')
        
        if not tipo:
            raise ValidationError('El tipo de actividad es obligatorio.')
        
        # Verificar que esté en los valores válidos
        valores_validos = [choice[0] for choice in TipoActividad.choices]
        
        if tipo not in valores_validos:
            raise ValidationError(
                f'Tipo de actividad no válido. Opciones: {", ".join(valores_validos)}'
            )
        
        return tipo


class AsignacionAulaGrupoForm(BaseModelForm):
    """Formulario para asignar aulas a grupos con validaciones."""
    
    class Meta:
        model = AsignacionAulaGrupo
        fields = ['grupo', 'local']
        widgets = {
            'grupo': forms.Select(attrs={'class': 'form-select'}),
            'local': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer campos requeridos
        self.fields['grupo'].required = True
        self.fields['local'].required = True
        
        self.fields['grupo'].error_messages = {
            'required': 'Debe seleccionar un grupo.',
            'invalid_choice': 'Seleccione un grupo válido.',
        }
        self.fields['local'].error_messages = {
            'required': 'Debe seleccionar un aula.',
            'invalid_choice': 'Seleccione un aula válida.',
        }
        
        # Filtrar solo locales de tipo AULA
        from .models import TipoLocal
        self.fields['local'].queryset = Local.objects.filter(tipo=TipoLocal.AULA)
        
        # Filtrar grupos que aún no tienen aula asignada (para creación)
        if not self.instance.pk:
            grupos_con_aula = AsignacionAulaGrupo.objects.values_list('grupo_id', flat=True)
            self.fields['grupo'].queryset = Grupo.objects.exclude(id__in=grupos_con_aula)
