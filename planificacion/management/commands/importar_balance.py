"""
Management command para importar el balance de carga desde un archivo Excel/CSV.

Reutiliza la función ``importar_balance()`` del módulo de vistas para
mantener coherencia entre la interfaz web y la línea de comandos.

Uso:
    python manage.py importar_balance archivo.csv --anio 1
    python manage.py importar_balance archivo.xlsx --anio 1 --limpiar --crear-asignaturas
"""
import logging

from django.core.management.base import BaseCommand, CommandError

from planificacion.views import importar_balance

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Importa el balance de carga desde un archivo Excel o CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            'archivo',
            type=str,
            help='Ruta al archivo Excel (.xlsx) o CSV (.csv)',
        )
        parser.add_argument(
            '--anio',
            type=int,
            required=True,
            help='ID (PK) del año académico al que corresponde el balance',
        )
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Elimina actividades planificadas previas del año antes de importar',
        )
        parser.add_argument(
            '--crear-asignaturas',
            action='store_true',
            help='Crea asignaturas automáticamente si no existen',
        )
        parser.add_argument(
            '--formato',
            choices=['csv', 'xlsx', 'auto'],
            default='auto',
            help='Formato del archivo (por defecto: auto-detectar)',
        )

    def handle(self, *args, **options):
        archivo_path = options['archivo']
        anio_id = options['anio']
        limpiar = options['limpiar']
        crear_asignaturas = options['crear_asignaturas']
        formato = options['formato']

        try:
            with open(archivo_path, 'rb') as f:
                resumen = importar_balance(
                    archivo=f,
                    anio_id=anio_id,
                    user=None,
                    formato=formato,
                    limpiar_previos=limpiar,
                    crear_asignaturas=crear_asignaturas,
                )
        except FileNotFoundError:
            raise CommandError(f'Archivo no encontrado: {archivo_path}')
        except Exception as e:
            raise CommandError(f'Error durante la importación: {e}')

        # ── Salida ──────────────────────────────────────────────
        self.stdout.write(self.style.SUCCESS(
            f'Importación completada para {resumen["anio"]}'
        ))
        self.stdout.write(f'  Asignaturas procesadas : {resumen["asignaturas_procesadas"]}')
        self.stdout.write(f'  Actividades creadas    : {resumen["actividades_creadas"]}')
        self.stdout.write(f'  Actividades omitidas   : {resumen["actividades_omitidas"]}')
        self.stdout.write(f'  Filas vacías           : {resumen["filas_vacias"]}')

        if resumen['detalle_por_tipo']:
            self.stdout.write('  Desglose por tipo:')
            for tipo, cantidad in sorted(resumen['detalle_por_tipo'].items()):
                self.stdout.write(f'    {tipo:4s}: {cantidad}')

        if resumen['errores']:
            self.stdout.write(self.style.WARNING(
                f'  Errores encontrados ({len(resumen["errores"])}):'
            ))
            for err in resumen['errores'][:20]:
                self.stdout.write(self.style.WARNING(f'    - {err}'))
            if len(resumen['errores']) > 20:
                self.stdout.write(self.style.WARNING(
                    f'    … y {len(resumen["errores"]) - 20} errores más.'
                ))
        else:
            self.stdout.write(self.style.SUCCESS('  Sin errores.'))
