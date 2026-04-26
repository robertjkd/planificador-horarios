"""
Modelos de datos para el sistema de planificación académica.

Reglas de negocio principales:
- Año académico 1 y 3 → turno Mañana (M); 2 y 4 → turno Tarde (T).
- Actividades tipo C/CE (Conferencia/Conferencia Especial) no tienen grupo (grupo=None).
- Actividades por grupo (CP, L, S, T, TE, E, PP) se replican por cada grupo del año.
- Actividades NP (No Presencial) no requieren local (requiere_local=False).
- Educación Física (E) usa local tipo POLI pero en la celda del horario NO se muestra el local.
- Capacidad del local debe ser >= alumnos del grupo (o suma de todos para conferencias).
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


# ─────────────────────────────────────────────────────────────
# CHOICES GLOBALES (reutilizados en múltiples modelos)
# ─────────────────────────────────────────────────────────────

class Turno(models.TextChoices):
    """Turno de clases. 1° y 3° año van en la mañana; 2° y 4° en la tarde."""
    MANANA = 'M', 'Mañana'
    TARDE = 'T', 'Tarde'


class TipoLocal(models.TextChoices):
    """Tipos de locales disponibles en la facultad."""
    AULA = 'AULA', 'Aula'
    SALON = 'SALON', 'Salón de Conferencia'
    LABORATORIO = 'LAB', 'Laboratorio'
    POLIDEPORTIVO = 'POLI', 'Polideportivo'
    OTRO = 'OTRO', 'Otro'


class TipoActividad(models.TextChoices):
    """
    Modalidades de actividad docente.

    Reglas de réplica por grupo al importar el balance de carga:
    - UNA_SOLA_VEZ: C, CE, NP (solo un registro por asignatura/semana/día).
    - POR_GRUPO:    CP, L, S, T, TE, E, PP (un registro por cada grupo del año).
    """
    CONFERENCIA = 'C', 'Conferencia'
    CONFERENCIA_ESPECIAL = 'CE', 'Conferencia Especial'
    CLASE_PRACTICA = 'CP', 'Clase Práctica'
    LABORATORIO = 'L', 'Laboratorio'
    SEMINARIO = 'S', 'Seminario'
    TALLER = 'T', 'Taller'
    TALLER_EJERCICIOS = 'TE', 'Taller de Ejercicios'
    EDUCACION_FISICA = 'E', 'Educación Física'
    PRACTICA_PROFESIONAL = 'PP', 'Práctica Profesional'
    NO_PRESENCIAL = 'NP', 'No Presencial'

    @classmethod
    def es_conferencia(cls, valor: str) -> bool:
        """Devuelve True si el tipo es conferencia para todo el año."""
        return valor in (cls.CONFERENCIA, cls.CONFERENCIA_ESPECIAL)

    @classmethod
    def es_por_grupo(cls, valor: str) -> bool:
        """Devuelve True si el tipo se replica por cada grupo del año."""
        return valor in (
            cls.CLASE_PRACTICA, cls.LABORATORIO, cls.SEMINARIO,
            cls.TALLER, cls.TALLER_EJERCICIOS, cls.EDUCACION_FISICA,
            cls.PRACTICA_PROFESIONAL,
        )

    @classmethod
    def no_requiere_local(cls, valor: str) -> bool:
        """Devuelve True si la actividad no necesita asignación de local."""
        return valor == cls.NO_PRESENCIAL

    @classmethod
    def tipo_local_requerido(cls, valor: str) -> str | None:
        """Mapea el tipo de actividad al tipo de local necesario."""
        mapping = {
            cls.CONFERENCIA: TipoLocal.SALON,
            cls.CONFERENCIA_ESPECIAL: TipoLocal.SALON,
            cls.CLASE_PRACTICA: TipoLocal.AULA,
            cls.LABORATORIO: TipoLocal.LABORATORIO,
            cls.SEMINARIO: TipoLocal.AULA,
            cls.TALLER: TipoLocal.AULA,
            cls.TALLER_EJERCICIOS: TipoLocal.AULA,
            cls.EDUCACION_FISICA: TipoLocal.POLIDEPORTIVO,
            cls.PRACTICA_PROFESIONAL: TipoLocal.AULA,
        }
        return mapping.get(valor)


class DiaSemana(models.IntegerChoices):
    """Días de la semana. 0=Lunes … 4=Viernes (formato del balance)."""
    LUNES = 0, 'Lunes'
    MARTES = 1, 'Martes'
    MIERCOLES = 2, 'Miércoles'
    JUEVES = 3, 'Jueves'
    VIERNES = 4, 'Viernes'


# ─────────────────────────────────────────────────────────────
# ANIO ACADEMICO
# ─────────────────────────────────────────────────────────────

class AnioAcademico(models.Model):
    """
    Representa un año de la carrera (1° a 4°).

    Regla de negocio: los años 1 y 3 se imparten en el turno de mañana;
    los años 2 y 4 en el turno de tarde.
    """
    numero = models.PositiveSmallIntegerField(
        unique=True,
        verbose_name='Número de año',
        help_text='Valores permitidos: 1, 2, 3, 4',
    )
    turno = models.CharField(
        max_length=1,
        choices=Turno.choices,
        verbose_name='Turno',
    )

    class Meta:
        verbose_name = 'Año Académico'
        verbose_name_plural = 'Años Académicos'
        ordering = ['numero']
        constraints = [
            models.CheckConstraint(
                check=models.Q(numero__gte=1, numero__lte=4),
                name='anio_numero_1_a_4',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.numero}° año ({self.get_turno_display()})'

    def clean(self):
        """Validación de integridad: turno coherente con el número de año."""
        turno_esperado = Turno.MANANA if self.numero in (1, 3) else Turno.TARDE
        if self.turno != turno_esperado:
            raise ValidationError(
                {'turno': f'El año {self.numero}° debe tener turno '
                         f'"{Turno.MANANA.label}" (1° y 3°) o '
                         f'"{Turno.TARDE.label}" (2° y 4°).'}
            )

    def total_alumnos(self) -> int:
        """Suma de alumnos de todos los grupos del año (útil para capacidad de salones)."""
        return sum(g.cantidad_alumnos for g in self.grupos.all())


# ─────────────────────────────────────────────────────────────
# GRUPO
# ─────────────────────────────────────────────────────────────

class Grupo(models.Model):
    """
    Grupo de estudiantes dentro de un año académico.

    Ejemplo: 1° año tiene 5 grupos (G1 … G5), 2° año 5 grupos,
    3° año 4 grupos, 4° año 4 grupos.
    """
    anio = models.ForeignKey(
        AnioAcademico,
        on_delete=models.CASCADE,
        related_name='grupos',
        verbose_name='Año académico',
    )
    nombre = models.CharField(
        max_length=50,
        verbose_name='Nombre del grupo',
        help_text='Ej. G1, G2, Grupo A…',
    )
    cantidad_alumnos = models.PositiveIntegerField(
        verbose_name='Cantidad de alumnos',
        help_text='Se usa para validar la capacidad del local asignado',
    )

    class Meta:
        verbose_name = 'Grupo'
        verbose_name_plural = 'Grupos'
        # Un mismo año no puede tener dos grupos con el mismo nombre.
        unique_together = [('anio', 'nombre')]
        ordering = ['anio__numero', 'nombre']
        indexes = [
            models.Index(fields=['anio', 'nombre'], name='idx_grupo_anio_nombre'),
        ]

    def __str__(self) -> str:
        return f'{self.nombre} — {self.anio}'


# ─────────────────────────────────────────────────────────────
# PROFESOR
# ─────────────────────────────────────────────────────────────

class Profesor(models.Model):
    """
    Docente que imparte una o varias asignaturas.

    Se modela como entidad propia (no usa auth.User directamente) para
    desacoplar la identidad de login de la identidad académica.
    Si se requiere vincular con un usuario del sistema, se puede
    extender con un OneToOne hacia settings.AUTH_USER_MODEL.
    """
    nombre = models.CharField(
        max_length=150,
        verbose_name='Nombre completo',
    )
    # Vinculación opcional con el sistema de usuarios (para login/rol CONSULTA)
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profesor',
        verbose_name='Usuario del sistema',
        help_text='Si el profesor también es usuario del sistema (rol CONSULTA)',
    )

    class Meta:
        verbose_name = 'Profesor'
        verbose_name_plural = 'Profesores'
        ordering = ['nombre']

    def __str__(self) -> str:
        return self.nombre


# ─────────────────────────────────────────────────────────────
# LOCAL
# ─────────────────────────────────────────────────────────────

class Local(models.Model):
    """
    Espacio físico donde se imparten las actividades docentes.

    Tres categorías principales:
    - AULA: clases prácticas, seminarios, talleres (por grupo).
    - SALON: conferencias que requieren capacidad >= total de alumnos del año.
    - LABORATORIO: sesiones de laboratorio (por grupo).
    - POLIDEPORTIVO: Educación Física (por grupo; en la celda del horario NO se muestra).
    """
    codigo = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Código único',
        help_text='Ej. S401, A201, LAB1, POLI',
    )
    nombre = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Nombre descriptivo',
        help_text='Ej. Salón 401, Aula 201',
    )
    tipo = models.CharField(
        max_length=5,
        choices=TipoLocal.choices,
        verbose_name='Tipo de local',
    )
    capacidad = models.PositiveIntegerField(
        verbose_name='Capacidad (número de alumnos)',
    )

    class Meta:
        verbose_name = 'Local'
        verbose_name_plural = 'Locales'
        ordering = ['tipo', 'codigo']
        indexes = [
            models.Index(fields=['tipo', 'capacidad'], name='idx_local_tipo_cap'),
        ]

    def __str__(self) -> str:
        return f'{self.codigo} ({self.get_tipo_display()}) — cap. {self.capacidad}'


# ─────────────────────────────────────────────────────────────
# FRANJA HORARIA
# ─────────────────────────────────────────────────────────────

class FranjaHoraria(models.Model):
    """
    Segmento de tiempo dentro de un turno.

    Ejemplo turno mañana: 8:00-9:20, 9:30-10:50, 11:00-12:20, 12:30-13:50.
    Ejemplo turno tarde: (análogo).

    El atributo `orden` permite controlar la secuencia de presentación
    independientemente de la hora de inicio (por ejemplo, si se inserta
    una franja intermedia después).
    """
    turno = models.CharField(
        max_length=1,
        choices=Turno.choices,
        verbose_name='Turno',
    )
    orden = models.PositiveSmallIntegerField(
        verbose_name='Orden de presentación',
        help_text='Número secuencial dentro del turno: 1, 2, 3, 4…',
    )
    hora_inicio = models.TimeField(verbose_name='Hora de inicio')
    hora_fin = models.TimeField(verbose_name='Hora de fin')

    class Meta:
        verbose_name = 'Franja Horaria'
        verbose_name_plural = 'Franjas Horarias'
        # No puede haber dos franjas con el mismo orden dentro de un turno.
        unique_together = [('turno', 'orden')]
        ordering = ['turno', 'orden']
        indexes = [
            models.Index(fields=['turno', 'orden'], name='idx_franja_turno_ord'),
        ]

    def __str__(self) -> str:
        return (
            f'{self.get_turno_display()} — '
            f'Franja {self.orden} ({self.hora_inicio:%H:%M}-{self.hora_fin:%H:%M})'
        )

    def clean(self):
        """La hora de fin debe ser posterior a la de inicio."""
        if self.hora_fin <= self.hora_inicio:
            raise ValidationError(
                {'hora_fin': 'La hora de fin debe ser posterior a la de inicio.'}
            )


# ─────────────────────────────────────────────────────────────
# ASIGNATURA
# ─────────────────────────────────────────────────────────────

class Asignatura(models.Model):
    """
    Materia que se imparte en un año académico específico.

    La abreviatura (máx. 10 caracteres) se usa para compactar la celda
    del horario impreso/pantalla:  PROG-C-S401, BD-L-LAB.
    """
    nombre = models.CharField(
        max_length=150,
        verbose_name='Nombre completo',
    )
    abreviatura = models.CharField(
        max_length=10,
        verbose_name='Abreviatura',
        help_text='Máximo 10 caracteres. Se muestra en la tabla horaria.',
    )
    anio = models.ForeignKey(
        AnioAcademico,
        on_delete=models.CASCADE,
        related_name='asignaturas',
        verbose_name='Año académico',
    )

    class Meta:
        verbose_name = 'Asignatura'
        verbose_name_plural = 'Asignaturas'
        # La abreviatura debe ser única dentro del año (permite repetir
        # abreviaturas en distintos años si la facultad lo hace).
        unique_together = [('anio', 'abreviatura')]
        ordering = ['anio__numero', 'nombre']
        indexes = [
            models.Index(fields=['anio', 'abreviatura'], name='idx_asig_anio_abrev'),
        ]

    def __str__(self) -> str:
        return f'{self.abreviatura} — {self.nombre} ({self.anio})'


# ─────────────────────────────────────────────────────────────
# ASIGNACION DE PROFESOR A ASIGNATURA
# ─────────────────────────────────────────────────────────────

class AsignacionProfesor(models.Model):
    """
    Relación que indica qué profesor imparte qué asignatura y a qué grupo.

    Reglas de negocio:
    - Si `grupo` es NULL → el profesor da la asignatura como conferencia
      (C o CE) a TODO el año.
    - Si `grupo` tiene valor → el profesor da la asignatura solo a ese grupo
      (CP, L, S, T, TE, E, PP).
    - Una misma asignatura puede tener múltiples profesores (uno por grupo
      o uno para la conferencia).
    """
    profesor = models.ForeignKey(
        Profesor,
        on_delete=models.CASCADE,
        related_name='asignaciones',
        verbose_name='Profesor',
    )
    asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.CASCADE,
        related_name='asignaciones_profesor',
        verbose_name='Asignatura',
    )
    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='asignaciones_profesor',
        verbose_name='Grupo',
        help_text='Dejar en blanco para conferencia (todo el año)',
    )
    tipo_actividad = models.CharField(
        max_length=3,
        choices=TipoActividad.choices,
        verbose_name='Tipo de actividad',
        help_text='Indica la modalidad que imparte este profesor',
    )

    class Meta:
        verbose_name = 'Asignación Profesor'
        verbose_name_plural = 'Asignaciones de Profesores'
        # Un mismo profesor no puede estar asignado dos veces a la misma
        # combinación (asignatura, grupo, tipo). Evita duplicados accidentales.
        unique_together = [('profesor', 'asignatura', 'grupo', 'tipo_actividad')]
        ordering = ['profesor__nombre', 'asignatura__nombre']
        indexes = [
            models.Index(
                fields=['asignatura', 'tipo_actividad', 'grupo'],
                name='idx_asignprof_asig_tipo_grp',
            ),
        ]

    def __str__(self) -> str:
        grupo_str = self.grupo.nombre if self.grupo else 'Conferencia'
        return (
            f'{self.profesor.nombre} → '
            f'{self.asignatura.abreviatura} '
            f'{self.get_tipo_actividad_display()} ({grupo_str})'
        )

    def clean(self):
        """
        Validación cruzada: coherencia entre tipo de actividad y grupo.
        """
        if TipoActividad.es_conferencia(self.tipo_actividad) and self.grupo is not None:
            raise ValidationError(
                {'grupo': 'Las actividades de conferencia (C/CE) no deben '
                         'tener grupo asignado (imparten a todo el año).'}
            )
        if (
            TipoActividad.es_por_grupo(self.tipo_actividad)
            and self.grupo is None
        ):
            raise ValidationError(
                {'grupo': f'El tipo de actividad "{self.tipo_actividad}" '
                         f'requiere un grupo específico.'}
            )


# ─────────────────────────────────────────────────────────────
# ASIGNACION DE AULA FIJA A GRUPO
# ─────────────────────────────────────────────────────────────

class AsignacionAulaGrupo(models.Model):
    """
    Representa el aula base donde un grupo recibe sus clases regulares.
    
    Reglas de negocio:
    - Un grupo solo puede tener un aula asignada.
    - El local debe ser de tipo AULA (no Salón, Laboratorio ni Polideportivo).
    - Esta asignación es usada por el motor de planificación como preferencia.
    """
    grupo = models.OneToOneField(
        Grupo,
        on_delete=models.CASCADE,
        related_name='aula_fija',
        verbose_name='Grupo',
        help_text='Grupo al que se le asigna el aula base.',
    )
    local = models.ForeignKey(
        Local,
        on_delete=models.CASCADE,
        related_name='asignaciones_grupo',
        verbose_name='Aula',
        help_text='Aula base donde el grupo recibe sus clases regulares.',
    )

    class Meta:
        verbose_name = 'Asignación de Aula a Grupo'
        verbose_name_plural = 'Asignaciones de Aulas a Grupos'
        ordering = ['grupo__anio__numero', 'grupo__nombre']

    def __str__(self) -> str:
        return f'{self.grupo} → {self.local}'

    def clean(self):
        """Validar que el local sea de tipo AULA."""
        if self.local.tipo != TipoLocal.AULA:
            raise ValidationError(
                {'local': f'El local debe ser de tipo "Aula". '
                         f'Se seleccionó "{self.local.get_tipo_display()}".'}
            )


# ─────────────────────────────────────────────────────────────
# ACTIVIDAD PLAN (celdas del balance de carga importado)
# ─────────────────────────────────────────────────────────────

class ActividadPlan(models.Model):
    """
    Representa una actividad proveniente del balance de carga semanal.

    Procedimiento de importación (no forma parte del modelo, pero se documenta
    la regla de negocio aquí para referencia):
    - Tipos C y CE       → se crea UN solo registro con grupo=NULL.
    - Tipos CP, L, S, T, TE, E, PP
                         → se crea UN registro POR CADA grupo del año.
    - Tipo NP            → se crea un registro con requiere_local=False.

    La semana proviene del balance (normalmente 1..13 o 1..16).
    El día proviene del balance: 0=Lunes, 1=Martes, 2=Miércoles, 3=Jueves.
    El viernes (4) NO aparece en el balance pero SÍ puede usarse al planificar.
    """
    asignatura = models.ForeignKey(
        Asignatura,
        on_delete=models.CASCADE,
        related_name='actividades_plan',
        verbose_name='Asignatura',
    )
    tipo_actividad = models.CharField(
        max_length=3,
        choices=TipoActividad.choices,
        verbose_name='Tipo de actividad',
    )
    grupo = models.ForeignKey(
        Grupo,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='actividades_plan',
        verbose_name='Grupo',
        help_text='NULL para conferencias (afecta a todos los grupos del año)',
    )
    anio = models.ForeignKey(
        AnioAcademico,
        on_delete=models.CASCADE,
        related_name='actividades_plan',
        verbose_name='Año académico',
        help_text='Denormalizado para agilizar filtros (ya se infiere por asignatura)',
    )
    semana = models.PositiveSmallIntegerField(
        verbose_name='Semana del balance',
        help_text='Número de semana según el archivo importado',
    )
    dia_semana = models.PositiveSmallIntegerField(
        choices=DiaSemana.choices,
        verbose_name='Día de la semana (balance)',
        help_text='0=Lunes, 1=Martes, 2=Miércoles, 3=Jueves',
    )
    requiere_local = models.BooleanField(
        default=True,
        verbose_name='Requiere local',
        help_text='False para actividades NP (no presenciales)',
    )

    class Meta:
        verbose_name = 'Actividad Planificada'
        verbose_name_plural = 'Actividades Planificadas'
        ordering = ['anio__numero', 'semana', 'dia_semana', 'tipo_actividad']
        indexes = [
            models.Index(
                fields=['anio', 'semana'],
                name='idx_actplan_anio_sem',
            ),
            models.Index(
                fields=['asignatura', 'tipo_actividad', 'grupo'],
                name='idx_actplan_asig_tipo_grp',
            ),
        ]

    def __str__(self) -> str:
        grupo_str = self.grupo.nombre if self.grupo else 'Conferencia'
        return (
            f'{self.asignatura.abreviatura}-{self.tipo_actividad} '
            f'Sem{self.semana} D{self.dia_semana} ({grupo_str})'
        )

    def clean(self):
        """
        Validaciones de integridad de negocio.
        """
        # 1. Coherencia conferencia ↔ grupo=None
        if TipoActividad.es_conferencia(self.tipo_actividad) and self.grupo is not None:
            raise ValidationError(
                {'grupo': 'Conferencias (C/CE) deben tener grupo=NULL.'}
            )

        # 2. Actividades por grupo DEBEN tener grupo
        if TipoActividad.es_por_grupo(self.tipo_actividad) and self.grupo is None:
            raise ValidationError(
                {'grupo': f'Actividades tipo "{self.tipo_actividad}" requieren un grupo.'}
            )

        # 3. NP no requiere local (y viceversa: solo NP puede omitir local)
        if TipoActividad.no_requiere_local(self.tipo_actividad) and self.requiere_local:
            raise ValidationError(
                {'requiere_local': 'Las actividades No Presenciales (NP) '
                                   'no deben requerir local.'}
            )

        # 4. Coherencia grupo ↔ anio (el grupo debe pertenecer al mismo año)
        if self.grupo and self.grupo.anio_id != self.anio_id:
            raise ValidationError(
                {'grupo': 'El grupo seleccionado no pertenece al año académico '
                          'indicado en esta actividad.'}
            )

        # 5. Coherencia asignatura ↔ anio
        if self.asignatura.anio_id != self.anio_id:
            raise ValidationError(
                {'asignatura': 'La asignatura no pertenece al año académico '
                               'indicado en esta actividad.'}
            )

    @property
    def es_conferencia(self) -> bool:
        return TipoActividad.es_conferencia(self.tipo_actividad)

    @property
    def es_educacion_fisica(self) -> bool:
        return self.tipo_actividad == TipoActividad.EDUCACION_FISICA

    @property
    def alumnos_requeridos(self) -> int:
        """
        Cantidad de alumnos que deben caber en el local asignado.

        - Conferencia: suma de todos los grupos del año.
        - Grupo específico: alumnos de ese grupo.
        - Sin grupo (no conferencia): 0 (el solver validará que exista un grupo).
        """
        if self.es_conferencia:
            return self.anio.total_alumnos()
        if self.grupo:
            return self.grupo.cantidad_alumnos
        return 0


# ─────────────────────────────────────────────────────────────
# ASIGNACION (resultado de la planificación)
# ─────────────────────────────────────────────────────────────

class Asignacion(models.Model):
    """
    Resultado del motor de planificación: una ActividadPlan concreta ubicada
    en un día, franja horaria y local específicos.

    Reglas de integridad (el motor CP-SAT las impone; en BD usamos constraints
    para evitar duplicados accidentales post-solución o edición manual):
    - Un ActividadPlan solo puede aparecer UNA vez (OneToOne implícito).
    - Un local no puede tener dos actividades en la misma franja+día.
    - Un profesor no puede estar en dos actividades en la misma franja+día
      (se valida en la vista de edición manual, no como constraint de BD
      para no bloquear reasignaciones transitorias).

    La marca `manual` permite auditar qué asignaciones fueron retocadas
    manualmente por el planificador tras la generación automática.
    """
    actividad_plan = models.OneToOneField(
        ActividadPlan,
        on_delete=models.CASCADE,
        related_name='asignacion',
        verbose_name='Actividad planificada',
    )
    franja = models.ForeignKey(
        FranjaHoraria,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='asignaciones',
        verbose_name='Franja horaria',
        help_text='NULL si la asignación es virtual o está pendiente de franja real',
    )
    local = models.ForeignKey(
        Local,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='asignaciones',
        verbose_name='Local asignado',
        help_text='NULL si la asignación es virtual o está pendiente de local real',
    )
    profesor = models.ForeignKey(
        Profesor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asignaciones_horario',
        verbose_name='Profesor asignado',
        help_text='Se deriva de AsignacionProfesor; puede quedar NULL si '
                  'no se definió previamente la asignación profesor-materia.',
    )
    dia_semana = models.PositiveSmallIntegerField(
        choices=DiaSemana.choices,
        verbose_name='Día de la semana final',
        help_text='0=Lunes … 4=Viernes. Puede diferir del día del balance '
                  'porque el solver puede reubicar la actividad.',
    )
    manual = models.BooleanField(
        default=False,
        verbose_name='Editada manualmente',
        help_text='True si el planificador modificó esta asignación tras '
                  'la generación automática',
    )
    fecha_generacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de generación',
    )

    class Meta:
        verbose_name = 'Asignación'
        verbose_name_plural = 'Asignaciones'
        ordering = ['dia_semana', 'franja__orden']
        # Un local no puede tener dos actividades en la misma franja+día.
        # Nota: las conferencias (que bloquean todo el año) se representan
        # como una única Asignacion vinculada a ActividadPlan(grupo=None),
        # por lo que esta constraint no duplica filas por grupo.
        unique_together = [('franja', 'local', 'dia_semana')]
        indexes = [
            models.Index(
                fields=['dia_semana', 'franja', 'local'],
                name='idx_asig_dia_franja_local',
            ),
            models.Index(
                fields=['dia_semana', 'franja'],
                name='idx_asig_dia_franja',
            ),
            models.Index(
                fields=['actividad_plan'],
                name='idx_asig_actplan',
            ),
        ]

    def __str__(self) -> str:
        return (
            f'{self.actividad_plan} → '
            f'{self.local.codigo} '
            f'({self.get_dia_semana_display()} F{self.franja.orden})'
        )

    def clean(self):
        """
        Validaciones ejecutadas tanto en generación automática como en
        edición manual desde la interfaz administrativa.
        """
        # 1. Capacidad del local >= alumnos requeridos
        if self.local.capacidad < self.actividad_plan.alumnos_requeridos:
            raise ValidationError(
                {'local': f'Capacidad insuficiente: local {self.local.codigo} '
                         f'({self.local.capacidad}) < '
                         f'{self.actividad_plan.alumnos_requeridos} alumnos.'}
            )

        # 2. Tipo de local compatible con el tipo de actividad
        tipo_local_esperado = TipoActividad.tipo_local_requerido(
            self.actividad_plan.tipo_actividad
        )
        if tipo_local_esperado and self.local.tipo != tipo_local_esperado:
            raise ValidationError(
                {'local': f'El tipo de local esperado para '
                         f'{self.actividad_plan.get_tipo_actividad_display()} '
                         f'es "{tipo_local_esperado}", pero se asignó '
                         f'"{self.local.tipo}".'}
            )

        # 3. Coherencia de turno: la franja debe pertenecer al mismo turno
        #    que el año académico de la actividad.
        turno_anio = self.actividad_plan.anio.turno
        if self.franja.turno != turno_anio:
            raise ValidationError(
                {'franja': f'La franja pertenece al turno '
                           f'"{self.franja.get_turno_display()}", pero el '
                           f'año académico usa el turno '
                           f'"{self.actividad_plan.anio.get_turno_display()}".'}
            )

    @property
    def texto_celda(self) -> str:
        """
        Texto que se muestra en la celda de la tabla horaria.

        Formato normal:   {abreviatura_asignatura}-{tipo_actividad}-{codigo_local}
        Ejemplo:          PROG-C-S401, BD-L-LAB

        Excepción (Educación Física): solo la abreviatura de la asignatura.
        """
        ap = self.actividad_plan
        if ap.es_educacion_fisica:
            return ap.asignatura.abreviatura
        return f'{ap.asignatura.abreviatura}-{ap.tipo_actividad}-{self.local.codigo}'


# ─────────────────────────────────────────────────────────────
# AUDITORIA
# ─────────────────────────────────────────────────────────────

class TipoAccionAuditoria(models.TextChoices):
    """Tipos de acciones auditables en el sistema."""
    IMPORTAR_BALANCE = 'IMPORTAR_BALANCE', 'Importar Balance de Carga'
    GENERAR_HORARIO = 'GENERAR_HORARIO', 'Generar Horario Automático'
    MODIFICAR_ASIGNACION = 'MODIFICAR_ASIGNACION', 'Modificar Asignación Manual'
    CREAR_USUARIO = 'CREAR_USUARIO', 'Crear Usuario'
    EDITAR_USUARIO = 'EDITAR_USUARIO', 'Editar Usuario'
    ELIMINAR_USUARIO = 'ELIMINAR_USUARIO', 'Eliminar Usuario'
    INICIO_SESION = 'INICIO_SESION', 'Inicio de Sesión'
    CIERRE_SESION = 'CIERRE_SESION', 'Cierre de Sesión'
    ERROR_SOLVER = 'ERROR_SOLVER', 'Error del Motor de Optimización'


class Auditoria(models.Model):
    """
    Registro de auditoría para acciones críticas del sistema.
    
    Permite rastrear quién hizo qué, cuándo y desde dónde.
    Se utiliza tanto para seguridad como para diagnóstico de problemas.
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='auditorias',
        verbose_name='Usuario',
        help_text='NULL si la acción es automática (ej. error del solver)',
    )
    accion = models.CharField(
        max_length=50,
        choices=TipoAccionAuditoria.choices,
        verbose_name='Acción',
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha y hora',
    )
    detalles = models.TextField(
        blank=True,
        verbose_name='Detalles',
        help_text='Información adicional en formato JSON o texto descriptivo',
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dirección IP',
    )
    navegador = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Navegador/Agente de Usuario',
    )

    class Meta:
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['-fecha'], name='idx_aud_fecha'),
            models.Index(fields=['usuario', '-fecha'], name='idx_aud_usuario_fecha'),
            models.Index(fields=['accion', '-fecha'], name='idx_aud_accion_fecha'),
        ]

    def __str__(self) -> str:
        usuario_str = self.usuario.username if self.usuario else 'Sistema'
        return f'{self.fecha:%Y-%m-%d %H:%M} - {usuario_str} - {self.get_accion_display()}'

    @classmethod
    def registrar(cls, usuario, accion, detalles='', request=None):
        """
        Método de clase para crear un registro de auditoría.
        
        Args:
            usuario: Instancia de Usuario o None
            accion: TipoAccionAuditoria o string del choice
            detalles: String con detalles adicionales
            request: Objeto HttpRequest para extraer IP y navegador
        """
        ip_address = None
        navegador = None
        
        if request:
            # Obtener IP (considerando proxies)
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            # Obtener navegador
            navegador = request.META.get('HTTP_USER_AGENT', '')[:255]
        
        return cls.objects.create(
            usuario=usuario,
            accion=accion,
            detalles=detalles,
            ip_address=ip_address,
            navegador=navegador,
        )
