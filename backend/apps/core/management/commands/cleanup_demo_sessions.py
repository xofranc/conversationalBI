# apps/core/management/commands/cleanup_demo_sessions.py
from django.core.management.base import BaseCommand
from apps.core.services.demo_service import DemoService


class Command(BaseCommand):
    help = 'Limpia sesiones de demo expiradas y sus datasets'
    
    def handle(self, *args, **options):
        self.stdout.write('Limpiando sesiones de demo expiradas...')
        
        try:
            total_cleaned = DemoService.cleanup_all_expired()
            self.stdout.write(
                self.style.SUCCESS(f'Se limpiaron {total_cleaned} datasets de sesiones expiradas')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al limpiar: {e}')
            )
