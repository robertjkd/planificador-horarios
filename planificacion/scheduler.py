"""
Motor de planificación de horarios usando OR-Tools CP-SAT.

Modela el problema de timetabling como un CSP con restricciones duras y blandas,
resuelve con cp_model.CpSolver y guarda las asignaciones en la base de datos.
"""
import logging
from collections import defaultdict
from datetime import time
from typing import Dict, List, Tuple

from django.db import transaction
from ortools.sat.python import cp_model

from academico.models import (
    ActividadPlan,
    AnioAcademico,
    Asignacion,
    AsignacionProfesor,
    Asignatura,
    FranjaHoraria,
    Grupo,
    Local,
    Profesor,
)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# PESOS PARA RESTRICCIONES BLANDAS (CONFIGURABLE)
# ─────────────────────────────────────────────────────────────

PESO_HUECO_GRUPO = 10  # Penalización por hueco libre en horario de grupo
PESO_CARGA_DIARIA = 5   # Penalización por más de 1 sesión de misma asignatura al día
PESO_FATIGA_PROFESOR = 7  # Penalización por más de 3 franjas consecutivas de profesor
PESO_CAMBIO_EDIFICIO = 3  # Penalización por cambio de edificio (opcional, requiere datos)

# ─────────────────────────────────────────────────────────────
# MAPEO TIPO ACTIVIDAD → TIPO LOCAL PERMITIDO
# ─────────────────────────────────────────────────────────────

TIPO_LOCAL_POR_ACTIVIDAD = {
    'C': ['S'],       # Conferencia → Salón
    'CE': ['S'],      # Conferencia especial → Salón
    'EC': ['S'],      # Especial de Conferencia (código alternativo) → Salón
    'CP': ['A', 'S'], # Clase práctica → Aula o Salón
    'L': ['L'],       # Laboratorio → Laboratorio
    'S': ['A', 'S'],  # Seminario → Aula o Salón
    'T': ['A', 'S'],  # Taller → Aula o Salón
    'TE': ['A', 'S'], # Taller especial → Aula o Salón
    'PP': ['A', 'S'], # Práctica profesional → Aula o Salón
    'E': ['O'],       # Educación física → Otro (POLIDEPORTIVO)
}

# ─────────────────────────────────────────────────────────────
# RECURSOS VIRTUALES (OVERFLOW)
# ─────────────────────────────────────────────────────────────


class LocalVirtual:
    """Local "fantasma" para albergar actividades sin opciones reales."""
    
    def __init__(self, pk: int, codigo: str, nombre: str, tipo: str, capacidad: int):
        self.pk = pk
        self.id = pk
        self.codigo = codigo
        self.nombre = nombre
        self.tipo = tipo
        self.capacidad = capacidad
        self.es_virtual = True
    
    def __str__(self):
        return f'{self.nombre} ({self.codigo})'


class FranjaVirtual:
    """Franja horaria "fantasma" para días sin franjas reales."""
    
    def __init__(self, pk: int, turno: str, orden: int, hora_inicio, hora_fin, dia_semana: int):
        self.pk = pk
        self.id = pk
        self.turno = turno
        self.orden = orden
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.dia_semana = dia_semana
        self.es_virtual = True
    
    def __str__(self):
        return f'Franja Virtual D{self.dia_semana} ({self.hora_inicio}-{self.hora_fin})'


def crear_recursos_virtuales(anio, franjas_existentes, locales_existentes, actividades):
    """
    Crea recursos virtuales (locales y franjas) para garantizar que todas
    las actividades tengan al menos una opción de asignación.
    
    Retorna:
        (local_virtual, franjas_virtuales, dias_con_franjas_virtuales)
    """
    from datetime import time
    
    # Verificar qué días de la semana tienen franjas reales
    dias_con_franjas = set()
    for f in franjas_existentes:
        # Las franjas reales no tienen dia_semana, se asignan a todos los días
        # Pero necesitamos saber para qué días crear franjas virtuales si faltan
        dias_con_franjas.update(range(5))  # Asumimos que franjas reales cubren todos los días
    
    # Determinar días necesarios por las actividades
    dias_necesarios = set(act.dia_semana for act in actividades if hasattr(act, 'dia_semana'))
    dias_faltantes = dias_necesarios - dias_con_franjas
    
    # Crear franjas virtuales para días faltantes
    franjas_virtuales = []
    hora_inicio = time(8, 0)
    hora_fin = time(20, 0)
    
    for dia in sorted(dias_faltantes):
        # Crear 4 franjas virtuales para este día
        for orden in range(1, 5):
            # Horarios por defecto según turno
            if anio.turno == 'M':
                hora_inicio = time(8 + orden - 1, 0)
                hora_fin = time(9 + orden - 1, 30)
            else:
                hora_inicio = time(14 + orden - 1, 0)
                hora_fin = time(15 + orden - 1, 30)
            
            franja = FranjaVirtual(
                pk=-(dia * 10 + orden),  # IDs negativos para identificar virtuales
                turno=anio.turno,
                orden=orden,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                dia_semana=dia,
            )
            franjas_virtuales.append(franja)
            logger.warning(f'Creada franja virtual: {franja}')
    
    # Crear local virtual con capacidad ilimitada y tipo universal
    local_virtual = LocalVirtual(
        pk=-1,  # ID negativo para identificar virtual
        codigo='VIRTUAL-OVERFLOW',
        nombre='LOCAL VIRTUAL (OVERFLOW)',
        tipo='S',  # Salón sirve para conferencias y clases
        capacidad=9999
    )
    logger.warning(f'Creado local virtual: {local_virtual} (capacidad={local_virtual.capacidad})')
    
    return local_virtual, franjas_virtuales


# ─────────────────────────────────────────────────────────────
# RESULTADO DE LA PLANIFICACIÓN
# ─────────────────────────────────────────────────────────────


class ResultadoPlanificacion:
    """Contenedor para el resultado del scheduler."""

    def __init__(self, exito: bool, mensaje: str, estadisticas: dict = None):
        self.exito = exito
        self.mensaje = mensaje
        self.estadisticas = estadisticas or {}

    def __str__(self):
        return self.mensaje


# ─────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────────


def generar_horario(anio_id: int, semana: int) -> ResultadoPlanificacion:
    """
    Genera el horario para un año académico y semana específica usando OR-Tools CP-SAT.

    Parámetros
    ----------
    anio_id : int
        PK del AnioAcademico.
    semana : int
        Número de semana a planificar.

    Retorna
    -------
    ResultadoPlanificacion
        Objeto con éxito, mensaje y estadísticas.
    """
    logger.info(f'Iniciando planificación: anio_id={anio_id}, semana={semana}')

    try:
        # ── 1. Cargar datos ───────────────────────────────────────
        anio = AnioAcademico.objects.get(pk=anio_id)
        logger.info(f'Año académico: {anio} (turno={anio.turno})')
        
        grupos = list(anio.grupos.all())
        logger.info(f'Grupos encontrados: {len(grupos)}')
        
        franjas = list(FranjaHoraria.objects.filter(turno=anio.turno))
        logger.info(f'Franjas horarias para turno {anio.turno}: {len(franjas)}')
        
        # Consulta de actividades con logging detallado
        query = ActividadPlan.objects.filter(
            asignatura__anio=anio,
            semana=semana,
            requiere_local=True,
        )
        logger.info(f'Query de actividades: asignatura__anio={anio.pk}, semana={semana}, requiere_local=True')
        logger.info(f'Actividades sin filtrar requiere_local: {ActividadPlan.objects.filter(asignatura__anio=anio, semana=semana).count()}')
        logger.info(f'Actividades con requiere_local=True: {ActividadPlan.objects.filter(asignatura__anio=anio, semana=semana, requiere_local=True).count()}')
        logger.info(f'Actividades con requiere_local=False: {ActividadPlan.objects.filter(asignatura__anio=anio, semana=semana, requiere_local=False).count()}')
        
        actividades = list(query.select_related('asignatura', 'grupo'))
        logger.info(f'Actividades cargadas: {len(actividades)}')
        
        locales = list(Local.objects.all())
        logger.info(f'Locales disponibles: {len(locales)}')
        
        # Log de capacidades por tipo de local
        locales_por_tipo = defaultdict(list)
        for loc in locales:
            locales_por_tipo[loc.tipo].append(loc)
        
        for tipo, locs in sorted(locales_por_tipo.items()):
            capacidades = [l.capacidad for l in locs]
            logger.info(f'  Tipo {tipo}: {len(locs)} locales, capacidades: {capacidades}')
        
        profesores = list(Profesor.objects.all())
        asignaciones_profesor = list(
            AsignacionProfesor.objects.select_related('profesor', 'asignatura', 'grupo')
        )

        if not grupos:
            return ResultadoPlanificacion(False, f'El año {anio} no tiene grupos registrados.')
        if not franjas:
            return ResultadoPlanificacion(False, f'No hay franjas horarias para el turno {anio.turno}.')
        # Pre-flight: mostrar primeras N actividades para debugging
        if actividades:
            logger.info('Primeras 5 actividades a planificar:')
            for i, act in enumerate(actividades[:5], 1):
                grupo_str = f'G{act.grupo.nombre}' if act.grupo else 'Conf.'
                logger.info(
                    '  %s. %s | %s | %s | Sem%s | Dia%s',
                    i, act.asignatura.nombre, act.tipo_actividad,
                    grupo_str, act.semana, act.dia_semana
                )
            if len(actividades) > 5:
                logger.info('  ... y %s actividades más', len(actividades) - 5)
        
        # Pre-flight check: verificar actividades con tipos válidos
        actividades_sin_tipo_local = [a for a in actividades if a.tipo_actividad not in TIPO_LOCAL_POR_ACTIVIDAD]
        if actividades_sin_tipo_local:
            logger.warning('Actividades con tipo no mapeado a local:')
            for act in actividades_sin_tipo_local[:5]:
                logger.warning('  - %s: tipo=%s', act.asignatura.nombre, act.tipo_actividad)
        
        if not actividades:
            # Mensaje más informativo para depuración
            total_actividades = ActividadPlan.objects.filter(asignatura__anio=anio, semana=semana).count()
            if total_actividades > 0:
                return ResultadoPlanificacion(
                    False, 
                    f'No hay actividades que requieran local para la semana {semana}. '
                    f'Se encontraron {total_actividades} actividades sin requerimiento de local. '
                    f'Verifique que las actividades tengan requiere_local=True.'
                )
            return ResultadoPlanificacion(
                False, 
                f'No hay actividades planificadas para la semana {semana}. '
                f'Asegúrese de haber importado el balance de carga para este año y semana.'
            )
        if not locales:
            return ResultadoPlanificacion(False, 'No hay locales registrados.')

        # ── 2. Preprocesar datos ───────────────────────────────────
        # Índices para acceso rápido
        grupos_por_id = {g.pk: g for g in grupos}
        franjas_por_id = {f.pk: f for f in franjas}
        locales_por_id = {l.pk: l for l in locales}
        actividades_por_id = {a.pk: a for a in actividades}
        profesores_por_id = {p.pk: p for p in profesores}

        # Franjas por día - las franjas son las mismas para todos los días (0-4)
        # El modelo FranjaHoraria no tiene dia_semana, solo turno y orden
        franjas_por_dia = defaultdict(list)
        for dia in range(5):  # Lunes=0 a Viernes=4
            franjas_por_dia[dia] = franjas.copy()

        # Profesores por (asignatura, grupo)
        prof_por_asig_grupo = defaultdict(list)
        for ap in asignaciones_profesor:
            key = (ap.asignatura.pk, ap.grupo.pk if ap.grupo else None)
            prof_por_asig_grupo[key].append(ap.profesor)

        # Suma de alumnos para conferencias
        suma_alumnos_anio = sum(g.cantidad_alumnos for g in grupos)
        logger.info(f'Alumnos totales en el año: {suma_alumnos_anio} (para conferencias)')
        logger.info(f'Grupos y alumnos: ' + ', '.join([f'G{g.nombre}={g.cantidad_alumnos}' for g in grupos]))

        # ── 3. Generar combinaciones permitidas ───────────────────────
        combinaciones = []  # (actividad_id, local_id, franja_id)
        actividad_opciones = {}  # act_id -> conteo de opciones
        
        # Diagnóstico: trackear rechazos por actividad
        diagnosticos_actividades = {}
        
        for act in actividades:
            tipos_local_permitidos = TIPO_LOCAL_POR_ACTIVIDAD.get(act.tipo_actividad, [])
            opciones_act = 0
            rechazos = {'tipo_local': 0, 'capacidad': 0, 'ed_fisica': 0, 'total_locales': 0}
            
            # Información de la actividad para diagnóstico
            grupo_info = f'G{act.grupo.nombre}' if act.grupo else 'Conf.'
            capacidad_req = act.grupo.cantidad_alumnos if act.grupo else suma_alumnos_anio
            
            # Filtrar locales por tipo y capacidad
            for loc in locales:
                rechazos['total_locales'] += 1
                
                if loc.tipo not in tipos_local_permitidos:
                    rechazos['tipo_local'] += 1
                    continue
                
                # Capacidad
                if act.grupo:
                    capacidad_requerida = act.grupo.cantidad_alumnos
                else:  # Conferencia
                    capacidad_requerida = suma_alumnos_anio
                
                if loc.capacidad < capacidad_requerida:
                    rechazos['capacidad'] += 1
                    continue
                
                # Educación física: preferir POLIDEPORTIVO, pero aceptar cualquier tipo 'O'
                if act.tipo_actividad == 'E':
                    # Verificar si existe al menos un polideportivo en la base de datos
                    hay_polideportivo = any('POLI' in l.codigo.upper() for l in locales)
                    
                    if hay_polideportivo:
                        # Si hay polideportivo, usar solo esos
                        if not ('POLI' in loc.codigo.upper()):
                            rechazos['ed_fisica'] += 1
                            continue
                    # Si no hay polideportivo específico, aceptar cualquier tipo 'O'
                
                # Filtrar franjas por día
                franjas_dia = franjas_por_dia.get(act.dia_semana, [])
                for f in franjas_dia:
                    combinaciones.append((act.pk, loc.pk, f.pk))
                    opciones_act += 1
            
            actividad_opciones[act.pk] = opciones_act
            if opciones_act == 0:
                diagnosticos_actividades[act.pk] = {
                    'actividad': act,
                    'rechazos': rechazos,
                    'capacidad_requerida': capacidad_req,
                    'tipos_permitidos': tipos_local_permitidos,
                    'grupo_info': grupo_info,
                }

        # Log de diagnóstico para actividades sin opciones
        if diagnosticos_actividades:
            logger.error('=' * 60)
            logger.error('DIAGNÓSTICO: Actividades sin combinaciones válidas')
            logger.error('=' * 60)
            for act_id, diag in list(diagnosticos_actividades.items())[:5]:  # Mostrar primeras 5
                act = diag['actividad']
                r = diag['rechazos']
                logger.error(
                    f'Actividad ID {act_id}: {act.asignatura.nombre} | '
                    f'Tipo: {act.tipo_actividad} | {diag["grupo_info"]} | '
                    f'Sem{act.semana} Dia{act.dia_semana}'
                )
                logger.error(f'  Capacidad requerida: {diag["capacidad_requerida"]}')
                logger.error(f'  Tipos de local permitidos: {diag["tipos_permitidos"]}')
                logger.error(f'  Locales evaluados: {r["total_locales"]}')
                logger.error(f'  Rechazados por tipo: {r["tipo_local"]}')
                logger.error(f'  Rechazados por capacidad: {r["capacidad"]}')
                logger.error(f'  Rechazados Ed. Física: {r["ed_fisica"]}')
                logger.error(f'  Franjas disponibles día {act.dia_semana}: {len(franjas_por_dia.get(act.dia_semana, []))}')
            if len(diagnosticos_actividades) > 5:
                logger.error(f'  ... y {len(diagnosticos_actividades) - 5} actividades más sin opciones')
            logger.error('=' * 60)

        # Si hay actividades sin opciones, crear recursos virtuales automáticamente
        actividades_con_virtual = 0
        if diagnosticos_actividades:
            logger.warning(f'⚠️  {len(diagnosticos_actividades)} actividades sin opciones reales. Creando recursos virtuales...')
            
            # Crear recursos virtuales
            local_virtual, franjas_virtuales = crear_recursos_virtuales(anio, franjas, locales, actividades)
            
            # Añadir local virtual a la lista de locales
            locales.append(local_virtual)
            locales_por_id[local_virtual.pk] = local_virtual
            
            # Añadir franjas virtuales
            for fv in franjas_virtuales:
                franjas.append(fv)
                franjas_por_id[fv.pk] = fv
                franjas_por_dia[fv.dia_semana].append(fv)
            
            # Crear combinaciones virtuales para actividades sin opciones
            for act_id, diag in diagnosticos_actividades.items():
                act = diag['actividad']
                dia_act = act.dia_semana
                
                # Buscar una franja virtual o real para este día
                franjas_disponibles = franjas_por_dia.get(dia_act, [])
                if not franjas_disponibles and franjas_virtuales:
                    # Si no hay franjas para este día, usar la primera franja virtual
                    franjas_disponibles = franjas_virtuales[:1]
                
                for f in franjas_disponibles[:1]:  # Solo una opción virtual por actividad
                    combinaciones.append((act.pk, local_virtual.pk, f.pk))
                    actividades_con_virtual += 1
                    logger.warning(f'  Actividad {act.pk} ({act.asignatura.nombre}) → Local virtual + Franja {f.pk}')
            
            logger.warning(f'✅ Creadas {actividades_con_virtual} combinaciones virtuales')

        if not combinaciones:
            return ResultadoPlanificacion(
                False,
                'No hay combinaciones válidas ni siquiera con recursos virtuales. '
                'Error crítico en los datos de planificación.'
            )

        logger.info(f'Combinaciones totales: {len(combinaciones)} ({actividades_con_virtual} virtuales)')

        # ── 4. Crear modelo OR-Tools ─────────────────────────────────
        modelo = cp_model.CpModel()

        # Variables de decisión: X[a, l, f] ∈ {0, 1}
        x = {}
        for act_id, loc_id, f_id in combinaciones:
            x[(act_id, loc_id, f_id)] = modelo.NewBoolVar(f'x_{act_id}_{loc_id}_{f_id}')

        # ── 5. Restricciones duras ───────────────────────────────────

        # 5.1 Cada actividad asignada exactamente a una combinación
        for act in actividades:
            vars_act = [x[(act.pk, loc_id, f_id)] for (act_id, loc_id, f_id) in combinaciones if act_id == act.pk]
            if vars_act:
                modelo.Add(sum(vars_act) == 1)

        # 5.2 Conflicto de grupo (incluye conferencias)
        # Para cada franja, un grupo no puede tener más de una actividad
        for f in franjas:
            for g in grupos:
                vars_grupo = []
                for act in actividades:
                    if act.grupo == g:
                        vars_grupo.extend([
                            x[(act.pk, loc_id, f_id)]
                            for (act_id, loc_id, f_id) in combinaciones
                            if act_id == act.pk and f_id == f.pk
                        ])
                
                # Conferencias afectan a todos los grupos del año
                for act in actividades:
                    if act.grupo is None:  # Conferencia
                        vars_grupo.extend([
                            x[(act.pk, loc_id, f_id)]
                            for (act_id, loc_id, f_id) in combinaciones
                            if act_id == act.pk and f_id == f.pk
                        ])
                
                if vars_grupo:
                    modelo.Add(sum(vars_grupo) <= 1)

        # 5.3 Conflicto de profesor
        # Para cada franja, un profesor no puede impartir más de una actividad
        for f in franjas:
            for p in profesores:
                vars_profesor = []
                for act in actividades:
                    # Buscar si este profesor imparte esta actividad
                    key = (act.asignatura.pk, act.grupo.pk if act.grupo else None)
                    if p in prof_por_asig_grupo[key]:
                        vars_profesor.extend([
                            x[(act.pk, loc_id, f_id)]
                            for (act_id, loc_id, f_id) in combinaciones
                            if act_id == act.pk and f_id == f.pk
                        ])
                
                if vars_profesor:
                    modelo.Add(sum(vars_profesor) <= 1)

        # 5.4 Conflicto de local
        # Para cada franja, un local no puede ser usado más de una vez
        for f in franjas:
            for l in locales:
                vars_local = [
                    x[(act_id, l.pk, f_id)]
                    for (act_id, loc_id, f_id) in combinaciones
                    if loc_id == l.pk and f_id == f.pk
                ]
                if vars_local:
                    modelo.Add(sum(vars_local) <= 1)

        # ── 6. Restricciones blandas (objetivo) ───────────────────────

        # 6.1 Variables auxiliares para huecos en horario de grupo
        # Para cada grupo y día, penalizar huecos entre actividades
        hueco_grupo = {}
        for g in grupos:
            for dia in range(5):  # 0-4
                # Franjas ordenadas por hora_inicio
                franjas_dia = sorted(franjas_por_dia[dia], key=lambda f: f.hora_inicio)
                if len(franjas_dia) < 2:
                    continue
                
                for i in range(len(franjas_dia) - 1):
                    f1, f2 = franjas_dia[i], franjas_dia[i + 1]
                    # Variable binaria: 1 si hay hueco entre f1 y f2 para este grupo
                    hueco_grupo[(g.pk, dia, i)] = modelo.NewBoolVar(f'hueco_{g.pk}_{dia}_{i}')

                    # Restricción: hueco = 1 si hay actividad en f2 pero no en f1
                    vars_f1 = []
                    vars_f2 = []
                    for act in actividades:
                        if act.grupo == g:
                            vars_f1.extend([
                                x[(act.pk, loc_id, f1.pk)]
                                for (act_id, loc_id, f_id) in combinaciones
                                if act_id == act.pk and f_id == f1.pk
                            ])
                            vars_f2.extend([
                                x[(act.pk, loc_id, f2.pk)]
                                for (act_id, loc_id, f_id) in combinaciones
                                if act_id == act.pk and f_id == f2.pk
                            ])
                    
                    if vars_f1 and vars_f2:
                        # hueco >= actividad_f2 AND NOT actividad_f1
                        modelo.Add(hueco_grupo[(g.pk, dia, i)] >= sum(vars_f2) - sum(vars_f1))

        # 6.2 Variables auxiliares para carga diaria de asignatura
        # Penalizar si una asignatura tiene más de 1 sesión al día
        carga_diaria = {}
        for asig in Asignatura.objects.filter(anio=anio):
            for dia in range(5):
                var_carga = modelo.NewBoolVar(f'carga_{asig.pk}_{dia}')
                carga_diaria[(asig.pk, dia)] = var_carga
                
                vars_dia = []
                for act in actividades:
                    if act.asignatura == asig and act.dia_semana == dia:
                        vars_dia.extend([
                            x[(act.pk, loc_id, f_id)]
                            for (act_id, loc_id, f_id) in combinaciones
                            if act_id == act.pk
                        ])
                
                if vars_dia:
                    # carga_diaria = 1 si sum(vars) > 1
                    modelo.Add(var_carga >= sum(vars_dia) - 1)

        # 6.3 Variables auxiliares para fatiga de profesor
        # Penalizar si profesor tiene más de 3 franjas consecutivas
        fatiga_profesor = {}
        for p in profesores:
            for dia in range(5):
                franjas_dia = sorted(franjas_por_dia[dia], key=lambda f: f.hora_inicio)
                if len(franjas_dia) < 4:
                    continue
                
                for i in range(len(franjas_dia) - 3):
                    f1, f2, f3, f4 = franjas_dia[i:i+4]
                    var_fatiga = modelo.NewBoolVar(f'fatiga_{p.pk}_{dia}_{i}')
                    fatiga_profesor[(p.pk, dia, i)] = var_fatiga
                    
                    vars_consec = []
                    for f in [f1, f2, f3, f4]:
                        for act in actividades:
                            key = (act.asignatura.pk, act.grupo.pk if act.grupo else None)
                            if p in prof_por_asig_grupo[key]:
                                vars_consec.extend([
                                    x[(act.pk, loc_id, f.pk)]
                                    for (act_id, loc_id, f_id) in combinaciones
                                    if act_id == act.pk and f_id == f.pk
                                ])
                    
                    if vars_consec:
                        modelo.Add(var_fatiga >= sum(vars_consec) - 3)

        # ── 7. Función objetivo ─────────────────────────────────────
        objetivo = 0
        
        # Penalizar huecos de grupo
        for var in hueco_grupo.values():
            objetivo += PESO_HUECO_GRUPO * var
        
        # Penalizar carga diaria excesiva
        for var in carga_diaria.values():
            objetivo += PESO_CARGA_DIARIA * var
        
        # Penalizar fatiga de profesor
        for var in fatiga_profesor.values():
            objetivo += PESO_FATIGA_PROFESOR * var
        
        modelo.Minimize(objetivo)

        # ── 8. Resolver ─────────────────────────────────────────────
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 30.0
        solver.parameters.num_search_workers = 4
        solver.log_callback = lambda x: logger.debug(f'OR-Tools: {x}')

        status = solver.Solve(modelo)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            logger.info(f'Solución encontrada: {solver.StatusName(status)}')
            logger.info(f'Valor objetivo: {solver.ObjectiveValue()}')
            
            # ── 9. Guardar resultados ─────────────────────────────────
            with transaction.atomic():
                # Eliminar asignaciones previas de esta semana/año
                eliminadas, _ = Asignacion.objects.filter(
                    actividad_plan__semana=semana,
                    actividad_plan__asignatura__anio=anio,
                ).delete()
                logger.info(f'Eliminadas {eliminadas} asignaciones previas')

                asignaciones_a_crear = []
                asignaciones_virtuales = 0
                for (act_id, loc_id, f_id), var in x.items():
                    if solver.Value(var) == 1:
                        act = actividades_por_id[act_id]
                        loc = locales_por_id[loc_id]
                        f = franjas_por_id[f_id]
                        
                        # Detectar si es asignación virtual
                        es_virtual = (loc_id < 0 or f_id < 0 or 
                                     getattr(loc, 'es_virtual', False) or 
                                     getattr(f, 'es_virtual', False))
                        if es_virtual:
                            asignaciones_virtuales += 1
                        
                        # Determinar profesor
                        key = (act.asignatura.pk, act.grupo.pk if act.grupo else None)
                        profs = prof_por_asig_grupo.get(key, [])
                        profesor = profs[0] if profs else None
                        
                        # Determinar día: usar el de la franja si existe, sino el de la actividad
                        dia_asignado = getattr(f, 'dia_semana', None) or act.dia_semana
                        
                        asignaciones_a_crear.append(Asignacion(
                            actividad_plan=act,
                            franja=f if f_id > 0 else None,  # No guardar franja virtual en BD
                            local=loc if loc_id > 0 else None,  # No guardar local virtual en BD
                            profesor=profesor,
                            dia_semana=dia_asignado,
                        ))
                
                Asignacion.objects.bulk_create(asignaciones_a_crear)
                logger.info(f'Creadas {len(asignaciones_a_crear)} asignaciones ({asignaciones_virtuales} virtuales)')

            estadisticas = {
                'tiempo_segundos': solver.WallTime(),
                'valor_objetivo': solver.ObjectiveValue(),
                'actividades_asignadas': len(asignaciones_a_crear),
                'combinaciones_exploradas': len(combinaciones),
                'asignaciones_virtuales': asignaciones_virtuales,
                'requiere_revision': asignaciones_virtuales > 0,
            }
            
            # Mensaje con advertencia si hay virtuales
            mensaje_base = f'Horario generado exitosamente para {anio} semana {semana}. {len(asignaciones_a_crear)} actividades asignadas.'
            if asignaciones_virtuales > 0:
                mensaje_base += f' ⚠️ {asignaciones_virtuales} actividades quedaron en LOCALES VIRTUALES y requieren revisión manual.'

            return ResultadoPlanificacion(
                True,
                mensaje_base,
                estadisticas,
            )
        else:
            logger.error(f'❌ No se encontró solución factible: {solver.StatusName(status)}')
            
            # Diagnóstico de restricciones conflictivas
            logger.error('=' * 60)
            logger.error('DIAGNÓSTICO DE CONFLICTOS (INFEASIBLE)')
            logger.error('=' * 60)
            
            # Contar actividades por grupo y día para detectar superposición imposible
            act_por_grupo_dia = defaultdict(list)
            for act in actividades:
                grupo_key = act.grupo.pk if act.grupo else f'CONF_{act.asignatura.pk}'
                act_por_grupo_dia[(grupo_key, act.dia_semana)].append(act)
            
            # Verificar si algún grupo tiene más actividades que franjas disponibles en un día
            conflictos_grupo = []
            for (grupo_key, dia), acts in act_por_grupo_dia.items():
                num_franjas_dia = len(franjas_por_dia.get(dia, []))
                if len(acts) > num_franjas_dia:
                    conflictos_grupo.append({
                        'grupo': grupo_key,
                        'dia': dia,
                        'actividades': len(acts),
                        'franjas': num_franjas_dia
                    })
            
            if conflictos_grupo:
                logger.error('⚠️  CONFLICTOS DE CAPACIDAD POR DÍA:')
                for c in conflictos_grupo[:5]:
                    logger.error(f'   Grupo {c["grupo"]}, Día {c["dia"]}: '
                               f'{c["actividades"]} actividades > {c["franjas"]} franjas')
                
                # 🆘 SOLUCIÓN DE EMERGENCIA: Crear franjas virtuales adicionales
                logger.warning('🆘 Creando franjas virtuales ADICIONALES para cubrir exceso...')
                
                franja_virtual_id = -100  # IDs para franjas de emergencia
                for c in conflictos_grupo:
                    exceso = c['actividades'] - c['franjas']
                    dia = c['dia']
                    
                    for i in range(exceso):
                        # Crear franja virtual adicional para este día
                        # Horario genérico para franjas de emergencia
                        hora_inicio = time(8, 0) if anio.turno == 'M' else time(14, 0)
                        hora_fin = time(20, 0)
                        
                        fv = FranjaVirtual(
                            pk=franja_virtual_id,
                            orden=99 + i,
                            hora_inicio=hora_inicio,
                            hora_fin=hora_fin,
                            dia_semana=dia,
                            turno=anio.turno
                        )
                        fv.nombre = f'VIRTUAL-EMERGENCIA-{abs(franja_virtual_id)}'
                        franjas.append(fv)
                        franjas_por_id[fv.pk] = fv
                        franjas_por_dia[dia].append(fv)
                        
                        # Crear combinaciones para todas las actividades de este día
                        for act in actividades:
                            if (act.grupo and act.grupo.pk == c['grupo'] and 
                                act.dia_semana == dia):
                                combinaciones.append((act.pk, local_virtual.pk, fv.pk))
                        
                        franja_virtual_id -= 1
                
                logger.warning(f'✅ Creadas {abs(franja_virtual_id) - 100} franjas virtuales de emergencia')
            
            # Intentar relajación: resolver sin restricciones blandas
            logger.warning('🔄 Intentando relajación de restricciones blandas...')
            
            # Crear modelo relajado (solo restricciones duras)
            modelo_relajado = cp_model.CpModel()
            x_relajado = {}
            
            # Recrear variables
            for act_id, loc_id, f_id in combinaciones:
                x_relajado[(act_id, loc_id, f_id)] = modelo_relajado.NewBoolVar(
                    f'x_relaj_{act_id}_{loc_id}_{f_id}'
                )
            
            # Solo restricciones duras
            # 5.1 Cada actividad asignada exactamente a una combinación
            for act in actividades:
                vars_act = [x_relajado[(act.pk, loc_id, f_id)] 
                           for (act_id, loc_id, f_id) in combinaciones if act_id == act.pk]
                if vars_act:
                    modelo_relajado.Add(sum(vars_act) == 1)
            
            # 5.2 Conflicto de grupo - RELAJADO: permitir múltiples actividades por grupo
            # cuando hay más actividades que franjas, un grupo necesita estar en 2+ lugares simultáneamente
            # Solo aplicar si NO hay conflictos de capacidad detectados
            if not conflictos_grupo:
                for f in franjas:
                    for g in grupos:
                        vars_grupo = []
                        for act in actividades:
                            if act.grupo == g:
                                vars_grupo.extend([
                                    x_relajado[(act.pk, loc_id, f_id)]
                                    for (act_id, loc_id, f_id) in combinaciones
                                    if act_id == act.pk and f_id == f.pk
                                ])
                        if vars_grupo:
                            modelo_relajado.Add(sum(vars_grupo) <= 1)
            else:
                logger.warning('   ⚠️  Restricción de grupo RELAJADA: permitiendo múltiples actividades simultáneas')
            
            # 5.3 Conflicto de local
            for f in franjas:
                for loc in locales:
                    vars_local = [
                        x_relajado[(act_id, loc.pk, f.pk)]
                        for (act_id, loc_id, f_id) in combinaciones
                        if loc_id == loc.pk and f_id == f.pk
                    ]
                    if vars_local:
                        modelo_relajado.Add(sum(vars_local) <= 1)
            
            # Resolver modelo relajado
            solver_relajado = cp_model.CpSolver()
            solver_relajado.parameters.max_time_in_seconds = 30.0
            solver_relajado.parameters.num_search_workers = 4
            
            status_relajado = solver_relajado.Solve(modelo_relajado)
            
            if status_relajado == cp_model.OPTIMAL or status_relajado == cp_model.FEASIBLE:
                logger.warning('✅ Solución relajada encontrada. Guardando con advertencia...')
                
                # Guardar solución relajada
                with transaction.atomic():
                    eliminadas, _ = Asignacion.objects.filter(
                        actividad_plan__semana=semana,
                        actividad_plan__asignatura__anio=anio,
                    ).delete()
                    
                    asignaciones_creadas = []
                    asignaciones_virtuales = 0
                    conflictos_detectados = []
                    
                    for (act_id, loc_id, f_id), var in x_relajado.items():
                        if solver_relajado.Value(var) == 1:
                            act = actividades_por_id[act_id]
                            loc = locales_por_id[loc_id]
                            f = franjas_por_id[f_id]
                            
                            es_virtual = (loc_id < 0 or f_id < 0 or 
                                         getattr(loc, 'es_virtual', False) or 
                                         getattr(f, 'es_virtual', False))
                            if es_virtual:
                                asignaciones_virtuales += 1
                            
                            key = (act.asignatura.pk, act.grupo.pk if act.grupo else None)
                            profs = prof_por_asig_grupo.get(key, [])
                            profesor = profs[0] if profs else None
                            
                            # Determinar día: usar el de la franja si existe, sino el de la actividad
                            dia_asignado = getattr(f, 'dia_semana', None) or act.dia_semana
                            
                            asignaciones_creadas.append(Asignacion(
                                actividad_plan=act,
                                franja=f if f_id > 0 else None,
                                local=loc if loc_id > 0 else None,
                                profesor=profesor,
                                dia_semana=dia_asignado,
                            ))
                    
                    Asignacion.objects.bulk_create(asignaciones_creadas)
                    
                    # Detectar conflictos (restricciones blandas violadas)
                    # Verificar profesores con 2+ actividades simultáneas
                    for f in franjas:
                        for p in profesores:
                            actividades_prof = []
                            for act in actividades:
                                key = (act.asignatura.pk, act.grupo.pk if act.grupo else None)
                                if p in prof_por_asig_grupo.get(key, []):
                                    var = x_relajado.get((act.pk, loc.pk, f.pk))
                                    if var and solver_relajado.Value(var) == 1:
                                        actividades_prof.append(act)
                            
                            if len(actividades_prof) > 1:
                                conflictos_detectados.append({
                                    'tipo': 'profesor_superposicion',
                                    'profesor': p.nombre,
                                    'franja': f,
                                    'actividades': len(actividades_prof)
                                })
                    
                    logger.warning(f'⚠️  Solución RELAJADA guardada: {len(asignaciones_creadas)} asignaciones')
                    if asignaciones_virtuales > 0:
                        logger.warning(f'   {asignaciones_virtuales} asignaciones virtuales')
                    if conflictos_detectados:
                        logger.warning(f'   {len(conflictos_detectados)} conflictos detectados (restricciones blandas violadas)')
                
                return ResultadoPlanificacion(
                    True,  # Éxito parcial
                    f'⚠️ HORARIO RELAJADO generado para {anio} semana {semana}. '
                    f'{len(asignaciones_creadas)} actividades asignadas. '
                    f'La solución viola algunas restricciones blandas (huecos, carga, fatiga). '
                    f'Revise conflictos de profesores y grupos manualmente.',
                    {
                        'tiempo_segundos': solver_relajado.WallTime(),
                        'actividades_asignadas': len(asignaciones_creadas),
                        'asignaciones_virtuales': asignaciones_virtuales,
                        'conflictos_detectados': len(conflictos_detectados),
                        'es_solucion_relajada': True,
                        'requiere_revision': True,
                    }
                )
            
            logger.error('❌ Incluso el modelo relajado es INFEASIBLE.')
            logger.error('   Esto indica un problema grave de capacidad.')
            logger.error('   Posibles causas:')
            logger.error('   1. Un grupo tiene más actividades que franjas disponibles')
            logger.error('   2. Un profesor debe estar en dos lugares simultáneamente')
            logger.error('   3. No hay suficientes locales para todas las actividades')
            
            # 🆘 SOLUCIÓN DE FUERZA BRUTA FINAL: Asignar todo a recursos virtuales
            logger.warning('🆘 Ejecutando solución de FUERZA BRUTA FINAL...')
            logger.warning('   Todas las actividades se asignarán a LOCALES Y FRANJAS VIRTUALES')
            
            # Crear suficientes franjas virtuales para todas las actividades
            franja_virtual_id = -200
            franjas_virtuales_emergencia = []
            
            for act in actividades:
                dia = act.dia_semana
                # Horario genérico para emergencia
                hora_inicio = time(8, 0) if anio.turno == 'M' else time(14, 0)
                hora_fin = time(20, 0)
                
                fv = FranjaVirtual(
                    pk=franja_virtual_id,
                    orden=1,
                    hora_inicio=hora_inicio,
                    hora_fin=hora_fin,
                    dia_semana=dia,
                    turno=anio.turno
                )
                fv.nombre = f'EMERGENCIA-{abs(franja_virtual_id)}'
                franjas_virtuales_emergencia.append((act, fv, local_virtual))
                franja_virtual_id -= 1
            
            logger.warning(f'   Creadas {len(franjas_virtuales_emergencia)} asignaciones de emergencia')
            
            # Guardar solución de fuerza bruta
            with transaction.atomic():
                eliminadas, _ = Asignacion.objects.filter(
                    actividad_plan__semana=semana,
                    actividad_plan__asignatura__anio=anio,
                ).delete()
                
                asignaciones_emergencia = []
                for act, fv, loc in franjas_virtuales_emergencia:
                    key = (act.asignatura.pk, act.grupo.pk if act.grupo else None)
                    profs = prof_por_asig_grupo.get(key, [])
                    profesor = profs[0] if profs else None
                    
                    asignaciones_emergencia.append(Asignacion(
                        actividad_plan=act,
                        franja=None,  # No guardar franja virtual
                        local=None,   # No guardar local virtual
                        profesor=profesor,
                        dia_semana=act.dia_semana,  # Usar día de la actividad planificada
                    ))
                
                Asignacion.objects.bulk_create(asignaciones_emergencia)
                logger.warning(f'✅ Guardadas {len(asignaciones_emergencia)} asignaciones de EMERGENCIA')
            
            return ResultadoPlanificacion(
                True,  # Éxito forzado
                f'🆘 HORARIO DE EMERGENCIA generado para {anio} semana {semana}. '
                f'{len(asignaciones_emergencia)} actividades marcadas para asignación MANUAL. '
                f'NO se encontró solución automática. '
                f'Debe asignar locales y franjas manualmente para todas las actividades.',
                {
                    'actividades_asignadas': len(asignaciones_emergencia),
                    'asignaciones_virtuales': len(asignaciones_emergencia),
                    'es_solucion_emergencia': True,
                    'es_solucion_relajada': False,
                    'requiere_revision': True,
                    'conflictos_capacidad': conflictos_grupo,
                }
            )

    except Exception as e:
        logger.exception('Error en planificación')
        return ResultadoPlanificacion(
            False,
            f'Error durante la planificación: {str(e)}',
        )
