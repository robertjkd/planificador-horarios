"""
Management command para verificar la configuración de base de datos.

Emite advertencias si se está usando SQLite en producción.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Verifica la configuración de base de datos y emite advertencias'

    def handle(self, *args, **options):
        db_engine = settings.DATABASES['default']['ENGINE']
        debug = settings.DEBUG
        
        self.stdout.write(self.style.SUCCESS('Verificando configuración de base de datos...'))
        self.stdout.write(f'Motor de base de datos: {db_engine}')
        self.stdout.write(f'DEBUG mode: {debug}')
        
        # Verificar si se usa SQLite en producción
        if db_engine == 'django.db.backends.sqlite3' and not debug:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  ADVERTENCIA: Se está usando SQLite en producción (DEBUG=False). '
                    'SQLite no es recomendado para entornos con múltiples usuarios concurrentes. '
                    'Considere usar PostgreSQL para producción.'
                )
            )
            logger.warning(
                'SQLite en producción detectado. '
                'Se recomienda usar PostgreSQL para entornos de producción.'
            )
        elif db_engine == 'django.db.backends.sqlite3' and debug:
            self.stdout.write(
                self.style.SUCCESS(
                    '✓ SQLite en modo desarrollo (DEBUG=True). '
                    'Adecuado para desarrollo rápido.'
                )
            )
        elif db_engine == 'django.db.backends.postgresql':
            self.stdout.write(
                self.style.SUCCESS(
                    '✓ PostgreSQL configurado. '
                    'Recomendado para producción.'
                )
            )
        
        self.stdout.write(self.style.SUCCESS('Verificación completada.'))
