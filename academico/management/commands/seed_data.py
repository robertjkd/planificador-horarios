"""
Comando de Django para poblar la base de datos con datos iniciales.

Uso:
    python manage.py seed_data              # Crear datos iniciales
    python manage.py seed_data --clear     # Limpiar y recrear todo
"""
import random
from datetime import time

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from academico.models import (
    AnioAcademico, Grupo, Asignatura, Local, FranjaHoraria,
    Profesor, AsignacionProfesor, Turno, TipoLocal
)

Usuario = get_user_model()


class Command(BaseCommand):
    help = 'Puebla la base de datos con datos iniciales para pruebas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Elimina todos los datos existentes antes de crear nuevos',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('=== SEED DATA ==='))
        
        if options['clear']:
            self.clear_data()
        
        with transaction.atomic():
            # Crear datos en orden de dependencias
            self.crear_usuarios()
            self.crear_anios_academicos()
            self.crear_grupos()
            self.crear_locales()
            self.crear_franjas_horarias()
            self.crear_profesores()
            self.crear_asignaturas()
            self.crear_asignaciones_profesor()
        
        self.mostrar_resumen()
        self.stdout.write(self.style.SUCCESS('\n✅ Datos iniciales creados exitosamente!'))

    def clear_data(self):
        """Elimina datos existentes preservando usuarios admin."""
        self.stdout.write(self.style.WARNING('⚠️  Eliminando datos existentes...'))
        
        # Eliminar en orden inverso de dependencias
        AsignacionProfesor.objects.all().delete()
        Profesor.objects.all().delete()
        Asignatura.objects.all().delete()
        FranjaHoraria.objects.all().delete()
        Local.objects.all().delete()
        Grupo.objects.all().delete()
        AnioAcademico.objects.all().delete()
        
        # Eliminar usuarios no admin (preservar vicedecano y planificador si existen)
        Usuario.objects.filter(rol=Usuario.Rol.CONSULTA).delete()
        
        self.stdout.write(self.style.SUCCESS('   ✓ Datos eliminados'))

    def crear_usuarios(self):
        """Crea usuarios iniciales: Vicedecano, Planificador y Estudiante."""
        self.stdout.write('\n👤 Creando usuarios...')
        
        usuarios_data = [
            {
                'username': 'vicedecano',
                'email': 'vicedecano@uci.cu',
                'password': 'Admin1234',
                'first_name': 'Vice',
                'last_name': 'Decano',
                'rol': Usuario.Rol.VICEDECANO,
            },
            {
                'username': 'planificador',
                'email': 'planificador@uci.cu',
                'password': 'Plan1234',
                'first_name': 'Plan',
                'last_name': 'Ficador',
                'rol': Usuario.Rol.PLANIFICADOR,
            },
            {
                'username': 'estudiante',
                'email': 'estudiante@uci.cu',
                'password': 'Estud1234',
                'first_name': 'Estu',
                'last_name': 'Diante',
                'rol': Usuario.Rol.CONSULTA,
            },
        ]
        
        creados = 0
        for data in usuarios_data:
            username = data.pop('username')
            password = data.pop('password')
            
            user, created = Usuario.objects.get_or_create(
                username=username,
                defaults=data
            )
            
            if created:
                user.set_password(password)
                user.save()
                creados += 1
                self.stdout.write(f"   ✓ Creado: {username}")
            else:
                self.stdout.write(f"   ⏭  Ya existe: {username}")
        
        self.stdout.write(f"   Total: {creados} usuarios nuevos")
        self.usuario_estudiante = Usuario.objects.get(username='estudiante')

    def crear_anios_academicos(self):
        """Crea los años académicos."""
        self.stdout.write('\n📚 Creando años académicos...')
        
        anios_data = [
            {'numero': 1, 'turno': Turno.MANANA, 'nombre': '1er año'},
            {'numero': 2, 'turno': Turno.TARDE, 'nombre': '2do año'},
            {'numero': 3, 'turno': Turno.MANANA, 'nombre': '3er año'},
            {'numero': 4, 'turno': Turno.TARDE, 'nombre': '4to año'},
        ]
        
        creados = 0
        self.anios = {}
        for data in anios_data:
            anio, created = AnioAcademico.objects.get_or_create(
                numero=data['numero'],
                defaults={'turno': data['turno']}
            )
            self.anios[data['numero']] = anio
            if created:
                creados += 1
                self.stdout.write(f"   ✓ {data['nombre']} ({data['turno'].label})")
        
        self.stdout.write(f"   Total: {creados} años nuevos")

    def crear_grupos(self):
        """Crea grupos para cada año académico."""
        self.stdout.write('\n👥 Creando grupos...')
        
        grupos_config = [
            {'anio': 1, 'cantidad': 5, 'alumnos': 30},
            {'anio': 2, 'cantidad': 5, 'alumnos': 30},
            {'anio': 3, 'cantidad': 4, 'alumnos': 25},
            {'anio': 4, 'cantidad': 4, 'alumnos': 25},
        ]
        
        creados = 0
        self.grupos = []
        self.primer_grupo = None
        
        for config in grupos_config:
            anio = self.anios[config['anio']]
            for i in range(1, config['cantidad'] + 1):
                nombre = f"G{i}"
                grupo, created = Grupo.objects.get_or_create(
                    nombre=nombre,
                    anio=anio,
                    defaults={'cantidad_alumnos': config['alumnos']}
                )
                
                # Guardar referencia al primer grupo de 1er año para el usuario estudiante
                if config['anio'] == 1 and i == 1 and self.primer_grupo is None:
                    self.primer_grupo = grupo
                
                self.grupos.append(grupo)
                if created:
                    creados += 1
        
        # Asignar el primer grupo al usuario estudiante
        if self.primer_grupo and self.usuario_estudiante:
            self.usuario_estudiante.grupo = self.primer_grupo
            self.usuario_estudiante.save()
            self.stdout.write(f"   ✓ Asignado grupo {self.primer_grupo} a usuario 'estudiante'")
        
        self.stdout.write(f"   Total: {creados} grupos nuevos")

    def crear_locales(self):
        """Crea aulas, salones, laboratorios y polideportivo."""
        self.stdout.write('\n🏢 Creando locales...')
        
        locales_data = [
            # Aulas (8) - capacidad para grupos de 30
            * [{'codigo': f'A{200+i}', 'nombre': f'Aula {200+i}', 'tipo': TipoLocal.AULA, 'capacidad': 40} for i in range(1, 9)],
            # Salones (3) - capacidad aumentada para conferencias (150 alumnos + margen)
            * [{'codigo': f'S{400+i}', 'nombre': f'Salón {400+i}', 'tipo': TipoLocal.SALON, 'capacidad': 200} for i in range(1, 4)],
            # Laboratorios (3) - capacidad para grupos pequeños
            * [{'codigo': f'LAB{i}', 'nombre': f'Laboratorio {i}', 'tipo': TipoLocal.LABORATORIO, 'capacidad': 40} for i in range(1, 4)],
            # Polideportivos (2) - capacidad aumentada para Ed. Física de años grandes
            {'codigo': 'POLI1', 'nombre': 'Polideportivo 1', 'tipo': TipoLocal.OTRO, 'capacidad': 200},
            {'codigo': 'POLI2', 'nombre': 'Polideportivo 2', 'tipo': TipoLocal.OTRO, 'capacidad': 200},
        ]
        
        creados = 0
        self.locales = []
        for data in locales_data:
            local, created = Local.objects.get_or_create(
                codigo=data['codigo'],
                defaults={
                    'nombre': data['nombre'],
                    'tipo': data['tipo'],
                    'capacidad': data['capacidad']
                }
            )
            self.locales.append(local)
            if created:
                creados += 1
                self.stdout.write(f"   ✓ {data['codigo']} ({data['nombre']})")
        
        self.stdout.write(f"   Total: {creados} locales nuevos")

    def crear_franjas_horarias(self):
        """Crea franjas horarias para turno mañana y tarde."""
        self.stdout.write('\n⏰ Creando franjas horarias...')
        
        # Franjas para turno Mañana
        franjas_manana = [
            {'orden': 1, 'hora_inicio': time(8, 0), 'hora_fin': time(9, 20)},
            {'orden': 2, 'hora_inicio': time(9, 30), 'hora_fin': time(10, 50)},
            {'orden': 3, 'hora_inicio': time(11, 0), 'hora_fin': time(12, 20)},
            {'orden': 4, 'hora_inicio': time(12, 30), 'hora_fin': time(13, 50)},
        ]
        
        # Franjas para turno Tarde
        franjas_tarde = [
            {'orden': 1, 'hora_inicio': time(12, 0), 'hora_fin': time(13, 20)},
            {'orden': 2, 'hora_inicio': time(13, 30), 'hora_fin': time(14, 50)},
            {'orden': 3, 'hora_inicio': time(15, 0), 'hora_fin': time(16, 20)},
            {'orden': 4, 'hora_inicio': time(16, 30), 'hora_fin': time(17, 50)},
        ]
        
        creados = 0
        
        # Crear franjas para turno Mañana
        for franja in franjas_manana:
            fh, created = FranjaHoraria.objects.get_or_create(
                turno=Turno.MANANA,
                orden=franja['orden'],
                defaults={
                    'hora_inicio': franja['hora_inicio'],
                    'hora_fin': franja['hora_fin'],
                }
            )
            if created:
                creados += 1
        
        # Crear franjas para turno Tarde
        for franja in franjas_tarde:
            fh, created = FranjaHoraria.objects.get_or_create(
                turno=Turno.TARDE,
                orden=franja['orden'],
                defaults={
                    'hora_inicio': franja['hora_inicio'],
                    'hora_fin': franja['hora_fin'],
                }
            )
            if created:
                creados += 1
        
        self.stdout.write(f"   Total: {creados} franjas horarias nuevas")

    def crear_profesores(self):
        """Crea profesores ficticios."""
        self.stdout.write('\n👨‍🏫 Creando profesores...')
        
        nombres = [
            'Juan Pérez', 'María García', 'Carlos López', 'Ana Martínez',
            'Luis Rodríguez', 'Carmen Sánchez', 'Pedro Ramírez', 'Laura Torres',
            'Miguel Castro', 'Sofía Flores', 'José Ortiz', 'Isabel Ruiz',
            'Francisco Morales', 'Patricia Vega', 'Antonio Herrera',
            'Elena Domínguez', 'Ricardo Cruz', 'Marta Reyes', 'Fernando Aguilar',
        ]
        
        creados = 0
        self.profesores = []
        for nombre in nombres:
            profesor, created = Profesor.objects.get_or_create(nombre=nombre)
            self.profesores.append(profesor)
            if created:
                creados += 1
        
        self.stdout.write(f"   Total: {creados} profesores nuevos")

    def crear_asignaturas(self):
        """Crea asignaturas por año con abreviaturas."""
        self.stdout.write('\n📖 Creando asignaturas...')
        
        asignaturas_data = {
            1: [  # 1er año
                ('Filosofía', 'FILO'),
                ('Álgebra', 'ALG'),
                ('Matemática Discreta I', 'MD1'),
                ('Introducción a la Programación I', 'IP1'),
                ('Educación Física I', 'EF1'),
                ('Seguridad Nacional', 'SN'),
                ('Introducción a las Ciencias Informáticas I', 'ICI1'),
            ],
            2: [  # 2do año
                ('Economía Política', 'EP'),
                ('Matemática II', 'MAT2'),
                ('Estructura de Datos I', 'ED1'),
                ('Física', 'FIS'),
                ('Educación Física III', 'EF3'),
                ('Fundamentos de Gestión de Organizaciones', 'FGO'),
                ('Proyecto de Investigación y Desarrollo I', 'PID1'),
            ],
            3: [  # 3er año
                ('Teoría Política', 'TP'),
                ('Probabilidades y Estadística', 'PE'),
                ('Sistema de Base de Datos II', 'SBD2'),
                ('Ingeniería de Software I', 'IS1'),
                ('Metodología de la Investigación Científica', 'MIC'),
                ('Sistema Operativo', 'SO'),
                ('Proyecto de Investigación y Desarrollo II', 'PID2'),
                ('Proyecto de Investigación y Desarrollo III', 'PID3'),
            ],
            4: [  # 4to año
                ('Investigación de Operaciones', 'IO'),
                ('Inteligencia Artificial', 'IA'),
                ('Ingeniería de Software II', 'IS2'),
                ('Redes y Seguridad Informática I', 'RSI1'),
                ('Proyecto de Investigación y Desarrollo IV', 'PID4'),
                ('Programación Web', 'PW'),
                ('Optativa I', 'OPT1'),
                ('Optativa II', 'OPT2'),
            ],
        }
        
        creados = 0
        self.asignaturas = []
        for num_anio, asignaturas in asignaturas_data.items():
            anio = self.anios[num_anio]
            for nombre, abrev in asignaturas:
                asig, created = Asignatura.objects.get_or_create(
                    nombre=nombre,
                    anio=anio,
                    defaults={'abreviatura': abrev}
                )
                self.asignaturas.append(asig)
                if created:
                    creados += 1
        
        self.stdout.write(f"   Total: {creados} asignaturas nuevas")

    def crear_asignaciones_profesor(self):
        """Crea asignaciones de profesores a asignaturas."""
        self.stdout.write('\n🔗 Creando asignaciones profesor-asignatura...')
        
        creados = 0
        random.seed(42)  # Reproducible
        
        for asignatura in self.asignaturas:
            # Asignar 1-2 profesores aleatorios por asignatura
            num_profesores = random.choice([1, 2])
            profesores_asignados = random.sample(self.profesores, num_profesores)
            
            for profesor in profesores_asignados:
                # Para asignaturas que típicamente son conferencias (asignar a todo el año)
                es_conferencia = any(
                    palabra in asignatura.nombre.lower() 
                    for palabra in ['álgebra', 'filosofía', 'economía', 'teoría política', 'física']
                )
                
                # Crear asignación sin grupo específico (conferencia) o con grupo
                asig, created = AsignacionProfesor.objects.get_or_create(
                    profesor=profesor,
                    asignatura=asignatura,
                    defaults={'grupo': None if es_conferencia else random.choice(self.grupos)}
                )
                
                if created:
                    creados += 1
        
        self.stdout.write(f"   Total: {creados} asignaciones nuevas")

    def mostrar_resumen(self):
        """Muestra resumen de datos creados."""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.MIGRATE_HEADING('RESUMEN'))
        self.stdout.write('='*50)
        
        modelos = [
            ('Usuarios', Usuario.objects.count()),
            ('Años Académicos', AnioAcademico.objects.count()),
            ('Grupos', Grupo.objects.count()),
            ('Locales', Local.objects.count()),
            ('Franjas Horarias', FranjaHoraria.objects.count()),
            ('Profesores', Profesor.objects.count()),
            ('Asignaturas', Asignatura.objects.count()),
            ('Asignaciones Profesor', AsignacionProfesor.objects.count()),
        ]
        
        for nombre, cantidad in modelos:
            self.stdout.write(f"  {nombre:25} {cantidad:>4}")
        
        self.stdout.write('='*50)
        
        # Mostrar credenciales
        self.stdout.write('\n' + self.style.MIGRATE_HEADING('CREDENCIALES DE PRUEBA'))
        self.stdout.write('  Usuario: vicedecano    Contraseña: Admin1234')
        self.stdout.write('  Usuario: planificador  Contraseña: Plan1234')
        self.stdout.write('  Usuario: estudiante    Contraseña: Estud1234')
