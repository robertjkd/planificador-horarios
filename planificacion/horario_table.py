"""
Estructura de tabla de horario para visualización.

Define clases para representar el horario generado en formato de tabla
(filas=franjas, columnas=días) para fácil visualización en templates.
"""
from collections import defaultdict
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class CeldaHorario:
    """Representa una celda en la tabla de horario."""
    asignatura: str
    tipo_actividad: str
    grupo: Optional[str]  # None para conferencias
    local: Optional[str]  # None si es virtual
    profesor: Optional[str]
    es_virtual: bool  # True si usa local/franja virtual
    es_conflicto: bool  # True si hay superposición de profesor
    actividad_id: int
    asignacion_id: Optional[int]
    
    def __str__(self):
        if self.es_virtual:
            return f"⚠️ {self.asignatura[:15]}... (PENDIENTE)"
        return f"{self.asignatura[:20]} ({self.tipo_actividad})"


@dataclass
class FilaHorario:
    """Representa una fila (franja horaria) en la tabla."""
    franja_id: int
    franja_nombre: str
    hora_inicio: str
    hora_fin: str
    celdas: Dict[int, List[CeldaHorario]]  # día -> lista de celdas
    
    def __init__(self, franja_id: int, franja_nombre: str, hora_inicio, hora_fin):
        self.franja_id = franja_id
        self.franja_nombre = franja_nombre
        self.hora_inicio = str(hora_inicio)[:5] if hora_inicio else "--:--"
        self.hora_fin = str(hora_fin)[:5] if hora_fin else "--:--"
        self.celdas = defaultdict(list)


@dataclass
class TablaHorario:
    """Tabla completa del horario para un año y semana."""
    anio_nombre: str
    semana: int
    dias: List[str]  # ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    filas: List[FilaHorario]
    pendientes: List[CeldaHorario]  # Actividades sin franja asignada
    estadisticas: Dict
    
    def __init__(self, anio_nombre: str, semana: int, estadisticas: Dict = None):
        self.anio_nombre = anio_nombre
        self.semana = semana
        self.dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
        self.filas = []
        self.pendientes = []
        self.estadisticas = estadisticas or {}
    
    def tiene_conflictos(self) -> bool:
        """Retorna True si hay celdas virtuales o conflictos."""
        for fila in self.filas:
            for dia, celdas in fila.celdas.items():
                for celda in celdas:
                    if celda.es_virtual or celda.es_conflicto:
                        return True
        return False
    
    def contar_virtuales(self) -> int:
        """Cuenta asignaciones virtuales."""
        count = 0
        for fila in self.filas:
            for dia, celdas in fila.celdas.items():
                count += sum(1 for c in celdas if c.es_virtual)
        return count


def construir_tabla_horario(asignaciones_queryset, franjas_queryset) -> TablaHorario:
    """
    Construye una TablaHorario a partir de asignaciones de la BD.
    
    Args:
        asignaciones_queryset: QuerySet de Asignacion con select_related
        franjas_queryset: QuerySet de FranjaHoraria para el turno
    
    Returns:
        TablaHorario lista para renderizar en template
    """
    from academico.models import Asignacion
    
    # Agrupar asignaciones por franja y día
    asignaciones_por_franja_dia = defaultdict(lambda: defaultdict(list))
    
    for asig in asignaciones_queryset:
        if asig.franja and hasattr(asig.actividad_plan, 'dia_semana'):
            dia = asig.actividad_plan.dia_semana
            franja_id = asig.franja.pk
            asignaciones_por_franja_dia[franja_id][dia].append(asig)
    
    # Recopilar actividades pendientes (sin franja asignada)
    actividades_pendientes = [
        asig for asig in asignaciones_queryset
        if not asig.franja and hasattr(asig.actividad_plan, 'dia_semana')
    ]
    
    # Crear tabla
    primera_asig = asignaciones_queryset.first()
    if primera_asig:
        anio_nombre = str(primera_asig.actividad_plan.asignatura.anio)
        semana = primera_asig.actividad_plan.semana
    else:
        anio_nombre = "Sin datos"
        semana = 0
    
    tabla = TablaHorario(anio_nombre=anio_nombre, semana=semana)
    
    # Crear filas para cada franja
    for franja in franjas_queryset.order_by('orden'):
        fila = FilaHorario(
            franja_id=franja.pk,
            franja_nombre=f"Franja {franja.orden}",
            hora_inicio=franja.hora_inicio,
            hora_fin=franja.hora_fin
        )
        
        # Llenar celdas con asignaciones
        for dia in range(5):
            asigs_dia = asignaciones_por_franja_dia.get(franja.pk, {}).get(dia, [])
            
            for asig in asigs_dia:
                act = asig.actividad_plan
                es_virtual = (asig.local is None or asig.franja is None)
                
                celda = CeldaHorario(
                    asignatura=act.asignatura.nombre,
                    tipo_actividad=act.tipo_actividad,
                    grupo=act.grupo.nombre if act.grupo else None,
                    local=asig.local.codigo if asig.local else "VIRTUAL",
                    profesor=asig.profesor.nombre if asig.profesor else "Sin profesor",
                    es_virtual=es_virtual,
                    es_conflicto=False,  # Se detecta en paso posterior
                    actividad_id=act.pk,
                    asignacion_id=asig.pk
                )
                fila.celdas[dia].append(celda)
        
        tabla.filas.append(fila)
    
    # Agregar actividades pendientes (sin franja) a la tabla
    for asig in actividades_pendientes:
        act = asig.actividad_plan
        celda = CeldaHorario(
            asignatura=act.asignatura.nombre,
            tipo_actividad=act.tipo_actividad,
            grupo=act.grupo.nombre if act.grupo else None,
            local="PENDIENTE",
            profesor=asig.profesor.nombre if asig.profesor else "Sin profesor",
            es_virtual=True,
            es_conflicto=False,
            actividad_id=act.pk,
            asignacion_id=asig.pk
        )
        tabla.pendientes.append(celda)
    
    return tabla


def detectar_conflictos_profesor(tabla: TablaHorario) -> TablaHorario:
    """
    Marca celdas con conflictos de profesor (mismo profe, misma franja, diferente día).
    
    Nota: Esta es una verificación simple. Los conflictos reales de superposición
    temporal requieren análisis más complejo considerando días específicos.
    """
    # Para cada franja, verificar si un profesor está en múltiples días simultáneamente
    # Esto es una simplificación - el verdadero conflicto es mismo día + misma franja
    
    for fila in tabla.filas:
        profesores_en_dia = defaultdict(list)  # día -> lista de profesores
        
        for dia, celdas in fila.celdas.items():
            for celda in celdas:
                if celda.profesor:
                    profesores_en_dia[dia].append(celda.profesor)
        
        # Verificar superposiciones (mismo profesor, mismo día, misma franja)
        for dia, profesores in profesores_en_dia.items():
            vistos = set()
            for profe in profesores:
                if profe in vistos:
                    # Marcar conflicto
                    for celda in fila.celdas[dia]:
                        if celda.profesor == profe:
                            celda.es_conflicto = True
                vistos.add(profe)
    
    return tabla


# Constantes para templates
DIAS_SEMANA = [
    (0, 'Lunes'),
    (1, 'Martes'),
    (2, 'Miércoles'),
    (3, 'Jueves'),
    (4, 'Viernes'),
]

ESTILOS_CELDA = {
    'normal': 'bg-white',
    'virtual': 'bg-warning bg-opacity-25 border-warning',
    'conflicto': 'bg-danger bg-opacity-25 border-danger',
    'conferencia': 'bg-info bg-opacity-10',
}


def get_estilo_celda(celda: CeldaHorario) -> str:
    """Retorna la clase CSS para una celda según su estado."""
    if celda.es_conflicto:
        return ESTILOS_CELDA['conflicto']
    if celda.es_virtual:
        return ESTILOS_CELDA['virtual']
    if celda.grupo is None:  # Conferencia
        return ESTILOS_CELDA['conferencia']
    return ESTILOS_CELDA['normal']
