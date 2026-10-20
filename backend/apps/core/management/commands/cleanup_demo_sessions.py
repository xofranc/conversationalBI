# apps/core/management/commands/cleanup_demo_sessions.py
from django.core.management.base import BaseCommand, CommandError

from config.composition import build_cleanup_expired_sessions_use_case


class Command(BaseCommand):
    help = 'Limpia sesiones de demo expiradas y sus datasets'
    
    def handle(self, *args, **options):
        self.stdout.write('Limpiando sesiones de demo expiradas...')

        try:
            result = build_cleanup_expired_sessions_use_case().execute()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Se limpiaron {result.deleted_dataset_count} datasets '
                    f'de {result.deleted_session_count} sesiones expiradas'
                )
            )
        except Exception as error:
            raise CommandError(f'Error al limpiar: {error}') from error
