from django import forms
from django.core.exceptions import ValidationError
from academico.models import (
    Asignacion,
    AsignacionProfesor,
    FranjaHoraria,
    Local,
    Profesor,
    Grupo,
)


def locales_compatibles(asignacion):
    """
    Retorna los locales compatibles con la asignación según:
    - Tipo de local compatible con tipo de actividad
    - Capacidad suficiente (considerando conferencias vs grupos específicos)
    """
    actividad = asignacion.actividad_plan
    tipo_actividad = actividad.tipo_actividad
    grupo = actividad.grupo
    anio = actividad.asignatura.anio
    
    # Mapeo de tipo de actividad a tipo de local requerido
    tipo_local_requerido = None
    if tipo_actividad in ['C', 'CE']:
        tipo_local_requerido = 'S'  # Salón
    elif tipo_actividad == 'L':
        tipo_local_requerido = 'L'  # Laboratorio
    elif tipo_actividad in ['CP', 'S', 'T', 'TE', 'PP']:
        tipo_local_requerido = 'A'  # Aula
    elif tipo_actividad == 'E':
        tipo_local_requerido = 'O'  # Otro (Polideportivo)
    elif tipo_actividad == 'NP':
        # No presencial no requiere local
        return Local.objects.none()
    
    # Calcular capacidad requerida
    if grupo is None:
        # Conferencia: suma de alumnos de todos los grupos del año
        capacidad_requerida = sum(
            g.cantidad_alumnos for g in Grupo.objects.filter(anio=anio)
        )
    else:
        # Grupo específico
        capacidad_requerida = grupo.cantidad_alumnos
    
    # Filtrar locales
    queryset = Local.objects.filter(tipo=tipo_local_requerido)
    
    # Filtrar por capacidad
    queryset = queryset.filter(capacidad__gte=capacidad_requerida)
    
    # Para Educación Física, filtrar por código que contenga "POLI"
    if tipo_actividad == 'E':
        queryset = queryset.filter(codigo__icontains='POLI')
    
    return queryset


def profesores_compatibles(asignacion):
    """
    Retorna los profesores que pueden impartir la asignación.
    Considera AsignacionProfesor para el grupo específico o conferencia.
    """
    actividad = asignacion.actividad_plan
    asignatura = actividad.asignatura
    grupo = actividad.grupo
    
    if grupo is None:
        # Conferencia: profesores asignados a la asignatura sin grupo específico
        asignaciones_profesor = AsignacionProfesor.objects.filter(
            asignatura=asignatura,
            grupo__isnull=True
        )
    else:
        # Grupo específico: profesores asignados a ese grupo
        asignaciones_profesor = AsignacionProfesor.objects.filter(
            asignatura=asignatura,
            grupo=grupo
        )
    
    profesor_ids = asignaciones_profesor.values_list('profesor_id', flat=True)
    return Profesor.objects.filter(id__in=profesor_ids)


class EditarAsignacionForm(forms.ModelForm):
    """
    Formulario para editar manualmente una asignación de horario.
    Permite modificar franja, local y profesor con validaciones cruzadas.
    """
    class Meta:
        model = Asignacion
        fields = ['franja', 'local', 'profesor']
        widgets = {
            'franja': forms.Select(attrs={'class': 'form-select'}),
            'local': forms.Select(attrs={'class': 'form-select'}),
            'profesor': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.asignacion = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)
        
        if self.asignacion:
            actividad = self.asignacion.actividad_plan
            anio = actividad.asignatura.anio
            dia_semana = actividad.dia_semana
            turno = anio.turno
            
            # Filtrar franjas: mismo día y turno
            self.fields['franja'].queryset = FranjaHoraria.objects.filter(
                dia_semana=dia_semana,
                turno=turno
            ).order_by('hora_inicio')
            
            # Filtrar locales compatibles
            self.fields['local'].queryset = locales_compatibles(self.asignacion)
            
            # Filtrar profesores compatibles
            self.fields['profesor'].queryset = profesores_compatibles(self.asignacion)
            self.fields['profesor'].required = False
            self.fields['profesor'].empty_label = "Sin asignar"
    
    def clean(self):
        cleaned_data = super().clean()
        franja = cleaned_data.get('franja')
        local = cleaned_data.get('local')
        profesor = cleaned_data.get('profesor')
        
        if not self.asignacion:
            return cleaned_data
        
        actividad = self.asignacion.actividad_plan
        grupo = actividad.grupo
        anio = actividad.asignatura.anio
        
        # Validación 1: conflicto de profesor
        if profesor and franja:
            otras = Asignacion.objects.filter(
                franja=franja,
                profesor=profesor
            ).exclude(pk=self.instance.pk)
            if otras.exists():
                raise ValidationError(
                    f"El profesor {profesor.nombre} ya está ocupado en esta franja."
                )
        
        # Validación 2: conflicto de local
        if local and franja:
            if Asignacion.objects.filter(
                franja=franja,
                local=local
            ).exclude(pk=self.instance.pk).exists():
                raise ValidationError(
                    f"El local {local.codigo} ya está ocupado en esta franja."
                )
        
        # Validación 3: conflicto de grupo
        if grupo and franja:
            # Busca otras asignaciones del mismo grupo en la misma franja
            conflicto = Asignacion.objects.filter(
                franja=franja,
                actividad_plan__grupo=grupo
            ).exclude(pk=self.instance.pk).exists()
            
            if not conflicto:
                # Verifica si hay una conferencia del mismo año en esa franja
                conflicto = Asignacion.objects.filter(
                    franja=franja,
                    actividad_plan__grupo__isnull=True,
                    actividad_plan__asignatura__anio=anio
                ).exists()
            
            if conflicto:
                raise ValidationError(
                    f"El grupo {grupo.nombre} ya tiene clase en esta franja."
                )
        
        elif grupo is None and franja:
            # Conferencia: ningún grupo del año puede tener actividad
            grupos_anio = Grupo.objects.filter(anio=anio)
            if Asignacion.objects.filter(
                franja=franja,
                actividad_plan__grupo__in=grupos_anio
            ).exclude(pk=self.instance.pk).exists():
                raise ValidationError(
                    "Hay grupos con clase en esta franja; la conferencia no puede solaparse."
                )
        
        # Validación 4: compatibilidad local-tipo y capacidad
        if local:
            tipo_actividad = actividad.tipo_actividad
            tipo_local = local.tipo
            
            # Mapeo de compatibilidad
            compatibilidad = {
                'C': ['S'],
                'CE': ['S'],
                'L': ['L'],
                'CP': ['A', 'S'],
                'S': ['A', 'S'],
                'T': ['A', 'S'],
                'TE': ['A', 'S'],
                'PP': ['A', 'S'],
                'E': ['O'],
                'NP': [],
            }
            
            if tipo_actividad not in compatibilidad:
                raise ValidationError(f"Tipo de actividad desconocido: {tipo_actividad}")
            
            if tipo_local not in compatibilidad[tipo_actividad]:
                raise ValidationError(
                    f"El local de tipo {tipo_local} no es compatible con la actividad {tipo_actividad}."
                )
            
            # Validar capacidad
            if grupo is None:
                capacidad_requerida = sum(
                    g.cantidad_alumnos for g in Grupo.objects.filter(anio=anio)
                )
            else:
                capacidad_requerida = grupo.cantidad_alumnos
            
            if local.capacidad < capacidad_requerida:
                raise ValidationError(
                    f"El local {local.codigo} no tiene capacidad suficiente "
                    f"(requiere {capacidad_requerida}, tiene {local.capacidad})."
                )
            
            # Para Educación Física, verificar que sea polideportivo
            if tipo_actividad == 'E' and 'POLI' not in local.codigo.upper():
                raise ValidationError(
                    "La Educación Física debe asignarse a un local tipo Otro (Polideportivo)."
                )
        
        return cleaned_data
