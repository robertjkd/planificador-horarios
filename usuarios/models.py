from django.db import models
from django.contrib.auth.models import AbstractUser


class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado con control de acceso basado en roles (RBAC).
    
    Roles:
    - VICEDECANO: Administrador con permisos completos
    - PLANIFICADOR: Gestión académica y generación de horarios
    - CONSULTA: Solo visualización (estudiantes/profesores)
    """
    class Rol(models.TextChoices):
        VICEDECANO = 'VICEDECANO', 'Vicedecano'
        PLANIFICADOR = 'PLANIFICADOR', 'Planificador'
        CONSULTA = 'CONSULTA', 'Consulta'
    
    rol = models.CharField(
        max_length=12,
        choices=Rol.choices,
        default=Rol.CONSULTA,
        verbose_name='Rol',
    )
    grupo = models.ForeignKey(
        'academico.Grupo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Grupo (estudiante)',
        related_name='usuarios',
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['username']

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_rol_display()})'

    @property
    def es_vicedecano(self):
        """Verifica si el usuario es Vicedecano."""
        return self.rol == self.Rol.VICEDECANO

    @property
    def es_planificador(self):
        """Verifica si el usuario es Planificador."""
        return self.rol == self.Rol.PLANIFICADOR

    @property
    def es_consulta(self):
        """Verifica si el usuario es de Consulta."""
        return self.rol == self.Rol.CONSULTA
    
    def puede_asignar_rol(self, rol_a_asignar):
        """
        Verifica si el usuario actual puede asignar el rol especificado.
        Solo VICEDECANO puede asignar roles, y no puede crear otro VICEDECANO.
        """
        if not self.es_vicedecano:
            return False
        # Un Vicedecano no puede crear otro Vicedecano (protección contra escalada de privilegios)
        if rol_a_asignar == self.Rol.VICEDECANO:
            return False
        return True
